import logging
import re
from typing import Any, Optional
import aiohttp
from openai import AsyncAzureOpenAI
from azure.identity import get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

logger = logging.getLogger("voicerag")

REALTORDR_API_BASE = "https://realtordr.com/wp-json/wp/v2"
API_TIMEOUT = 10
API_HEADERS = {"User-Agent": "MacHenryRealtorApp/1.0 (property-search)"}

# Taxonomy caches — populated at startup via refresh_taxonomy_cache()
_property_type_map: dict[str, int] = {}
_city_map: dict[str, int] = {}
_status_map: dict[str, int] = {}

# Hardcoded fallbacks (scraped from realtordr.com taxonomy endpoints)
_FALLBACK_PROPERTY_TYPES = {
    "villa": 37,
    "condo": 38,
    "apartment": 39,
    "land": 40,
    "commercial": 41,
    "house": 42,
    "penthouse": 43,
    "townhouse": 44,
}

_FALLBACK_CITIES = {
    "cabarete": 48,
    "sosua": 49,
    "puerto plata": 50,
    "punta cana": 51,
    "santo domingo": 52,
    "las terrenas": 53,
    "samana": 54,
    "santiago": 55,
    "bavaro": 56,
    "cabrera": 57,
    "rio san juan": 58,
    "luperon": 59,
    "nagua": 60,
    "constanza": 61,
    "jarabacoa": 62,
}

_FALLBACK_STATUSES = {
    "for sale": 30,
    "for rent": 31,
    "sold": 32,
}

_property_search_tool_schema = {
    "type": "function",
    "name": "property_search",
    "description": (
        "Search available real estate listings on the MacHenry Realtor website (realtordr.com). "
        "Use this tool when a caller asks about specific properties, pricing, what's available in a "
        "certain area, or any listing-related question. Pass a natural language description of what "
        "the caller is looking for. Also supports looking up a specific property by its ID number "
        "(e.g. '55069', 'rdr-55069', or '55069-property')."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Natural language description of what the caller wants, e.g. "
                    "'3 bedroom villa in Cabarete under 300k' or 'beachfront condos in Sosua'. "
                    "Can also be a property ID like '55069' or 'rdr-55069'."
                ),
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


async def refresh_taxonomy_cache():
    """Fetch WordPress taxonomy terms and populate the lookup maps.
    Falls back to hardcoded values on failure."""
    global _property_type_map, _city_map, _status_map

    async def _fetch_terms(endpoint: str) -> dict[str, int]:
        result = {}
        try:
            async with aiohttp.ClientSession(headers=API_HEADERS) as session:
                async with session.get(
                    f"{REALTORDR_API_BASE}/{endpoint}",
                    params={"per_page": 100},
                    timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
                ) as resp:
                    if resp.status == 200:
                        terms = await resp.json()
                        for term in terms:
                            name = term.get("name", "").lower().strip()
                            term_id = term.get("id")
                            if name and term_id:
                                result[name] = term_id
        except Exception as e:
            logger.warning(f"Failed to fetch taxonomy {endpoint}: {e}")
        return result

    types = await _fetch_terms("property-type")
    cities = await _fetch_terms("property-city")
    statuses = await _fetch_terms("property-status")

    _property_type_map = types if types else _FALLBACK_PROPERTY_TYPES
    _city_map = cities if cities else _FALLBACK_CITIES
    _status_map = statuses if statuses else _FALLBACK_STATUSES

    logger.info(
        f"🏠 Property taxonomy cache loaded: {len(_property_type_map)} types, "
        f"{len(_city_map)} cities, {len(_status_map)} statuses"
    )


# Matches: "55069", "rdr-55069", "55069-property", "rdr 55069", "property 55069"
_PROPERTY_ID_PATTERN = re.compile(
    r"(?:rdr[- ]?)?(\d{4,6})(?:[- ]?property)?$", re.IGNORECASE
)


def _extract_property_id(query: str) -> Optional[int]:
    """Try to extract a numeric property ID from the query string.
    Accepts: '55069', 'rdr-55069', 'rdr 55069', '55069-property', 'property 55069'."""
    q = query.strip()
    # Also handle "property 55069" prefix form
    q = re.sub(r"^property[- ]?", "", q, flags=re.IGNORECASE).strip()
    m = _PROPERTY_ID_PATTERN.match(q)
    if m:
        return int(m.group(1))
    return None


async def _fetch_property_by_id(property_id: int) -> Optional[dict]:
    """Fetch a single property by its WordPress post ID."""
    try:
        async with aiohttp.ClientSession(headers=API_HEADERS) as session:
            async with session.get(
                f"{REALTORDR_API_BASE}/properties/{property_id}",
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as resp:
                if resp.status == 200:
                    raw = await resp.json()
                    return _extract_property_fields(raw)
                logger.warning(f"Property ID {property_id} lookup returned status {resp.status}")
                return None
    except Exception as e:
        logger.error(f"Property ID {property_id} lookup failed: {e}")
        return None


def _parse_query_filters(query: str) -> dict[str, Any]:
    """Extract WordPress API filter params from a natural-language query."""
    q = query.lower()
    params: dict[str, Any] = {"search": query, "per_page": 20, "status": "publish"}

    # Match property type
    for name, tid in _property_type_map.items():
        if name in q:
            params["property-type"] = tid
            break

    # Match city
    for name, tid in _city_map.items():
        if name in q:
            params["property-city"] = tid
            break

    # Match status (default to for-sale)
    matched_status = False
    for name, tid in _status_map.items():
        if name in q:
            params["property-status"] = tid
            matched_status = True
            break
    if not matched_status:
        # Default to "for sale" if available
        if "for sale" in _status_map:
            params["property-status"] = _status_map["for sale"]

    return params


def _extract_property_fields(prop: dict) -> dict:
    """Pull the key fields out of a WordPress property response object."""
    meta = prop.get("property_meta", {})

    def _first(val):
        """WordPress meta fields are often arrays; grab the first element."""
        if isinstance(val, list):
            return val[0] if val else None
        return val

    return {
        "id": prop.get("id"),
        "title": (prop.get("title") or {}).get("rendered", "Untitled"),
        "price": _first(meta.get("REAL_HOMES_property_price")),
        "bedrooms": _first(meta.get("REAL_HOMES_property_bedrooms")),
        "bathrooms": _first(meta.get("REAL_HOMES_property_bathrooms")),
        "size": _first(meta.get("REAL_HOMES_property_size")),
        "address": _first(meta.get("REAL_HOMES_property_address")),
        "link": prop.get("link"),
    }


async def _fetch_properties(params: dict) -> list[dict]:
    """Query the WordPress REST API and return extracted property data."""
    try:
        async with aiohttp.ClientSession(headers=API_HEADERS) as session:
            async with session.get(
                f"{REALTORDR_API_BASE}/properties",
                params=params,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Property API returned status {resp.status}")
                    return []
                raw = await resp.json()
                return [_extract_property_fields(p) for p in raw]
    except Exception as e:
        logger.error(f"Property API request failed: {e}")
        return []


async def _summarize_for_voice(
    client: AsyncAzureOpenAI,
    query: str,
    properties: list[dict],
) -> str:
    """Use o4-mini to produce a brief, voice-friendly summary of search results."""
    if not properties:
        return (
            "I wasn't able to find any listings matching that criteria. "
            "You might want to try broadening your search, or I can connect you "
            "with our team for a more detailed look."
        )

    property_text = "\n".join(
        f"- ID {p['id']}: {p['title']} | Price: {p['price'] or 'Contact for price'} | "
        f"Beds: {p['bedrooms'] or 'N/A'} | Baths: {p['bathrooms'] or 'N/A'} | "
        f"Size: {p['size'] or 'N/A'} sqft | Address: {p['address'] or 'N/A'}"
        for p in properties
    )

    prompt = f"""You are summarizing real estate search results for a live phone call. The caller asked: "{query}"

Here are the listings found:
{property_text}

Produce a brief, natural, voice-friendly response:
- If there is only one result: mention the title, price, bedrooms, bathrooms, square footage, and property ID.
- If there are multiple results: start with a high-level summary (how many listings, price range), then highlight 2-3 standout properties with title, price, beds/baths, sqft, and property ID.
- Always mention the property ID number so the caller can reference it in follow-up questions.
- Keep it concise — this will be spoken aloud on a phone call.
- Use USD for prices. If a price looks like it has no currency, assume USD.
- Do NOT include URLs or links."""

    try:
        response = await client.chat.completions.create(
            model="o4-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful real estate assistant summarizing property "
                        "search results for a phone conversation. Be concise and natural."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"o4-mini summarization failed: {e}")
        # Fall back to a basic summary
        count = len(properties)
        prices = [p["price"] for p in properties if p["price"]]
        if prices:
            return (
                f"I found {count} listing{'s' if count != 1 else ''} matching your criteria. "
                f"Prices range from {min(prices)} to {max(prices)}. "
                "Would you like me to go through the details of any of these?"
            )
        return (
            f"I found {count} listing{'s' if count != 1 else ''} matching your criteria. "
            "Would you like me to go through the details?"
        )


async def _property_search(client: AsyncAzureOpenAI, args: Any) -> ToolResult:
    """Execute a property search and return a voice-friendly summary."""
    query = args.get("query", "")
    logger.info(f"🏠 Property search: '{query}'")

    # Check if the query is a property ID lookup
    property_id = _extract_property_id(query)
    if property_id:
        logger.info(f"🏠 Looking up property by ID: {property_id}")
        prop = await _fetch_property_by_id(property_id)
        properties = [prop] if prop else []
    else:
        params = _parse_query_filters(query)
        properties = await _fetch_properties(params)

    logger.info(f"🏠 Found {len(properties)} properties")

    summary = await _summarize_for_voice(client, query, properties)
    return ToolResult(summary, ToolResultDirection.TO_SERVER)


def property_search_tool(
    endpoint: str,
    api_key: str = None,
    credentials=None,
) -> Tool:
    """Factory: create the property_search Tool wired to o4-mini for summarization."""
    if api_key:
        client = AsyncAzureOpenAI(
            api_key=api_key,
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint,
        )
    elif credentials:
        token_provider = get_bearer_token_provider(
            credentials, "https://cognitiveservices.azure.com/.default"
        )
        client = AsyncAzureOpenAI(
            azure_ad_token_provider=token_provider,
            api_version="2024-12-01-preview",
            azure_endpoint=endpoint,
        )
    else:
        raise ValueError("Either api_key or credentials must be provided")

    return Tool(
        schema=_property_search_tool_schema,
        target=lambda args: _property_search(client, args),
    )
