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
API_TIMEOUT = 15
API_HEADERS = {"User-Agent": "MacHenryRealtorApp/1.0 (property-search)"}

# Taxonomy caches — populated at startup via refresh_taxonomy_cache()
_property_type_map: dict[str, int] = {}
_city_map: dict[str, int] = {}
_status_map: dict[str, int] = {}

# Hardcoded fallbacks (verified against live API filter params)
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
        url = f"{REALTORDR_API_BASE}/{endpoint}"
        try:
            async with aiohttp.ClientSession(headers=API_HEADERS) as session:
                async with session.get(
                    url,
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
                        logger.info(f"  ✅ {endpoint}: {len(result)} terms fetched")
                    else:
                        logger.warning(f"  ⚠️ {endpoint}: HTTP {resp.status} (endpoint may not be exposed via REST)")
        except Exception as e:
            logger.warning(f"  ❌ {endpoint}: {e}")
        return result

    logger.info("🏠 Refreshing taxonomy cache from realtordr.com...")
    types = await _fetch_terms("property-type")
    cities = await _fetch_terms("property-city")
    statuses = await _fetch_terms("property-status")

    _property_type_map = types if types else _FALLBACK_PROPERTY_TYPES
    _city_map = cities if cities else _FALLBACK_CITIES
    _status_map = statuses if statuses else _FALLBACK_STATUSES

    using_fallback = []
    if not types:
        using_fallback.append("types")
    if not cities:
        using_fallback.append("cities")
    if not statuses:
        using_fallback.append("statuses")

    logger.info(
        f"🏠 Taxonomy cache ready: {len(_property_type_map)} types, "
        f"{len(_city_map)} cities, {len(_status_map)} statuses"
        + (f" (using hardcoded fallback for: {', '.join(using_fallback)})" if using_fallback else "")
    )


def _extract_property_id(query: str) -> Optional[int]:
    """Try to extract a numeric property ID from the query string.
    Handles many formats: '55069', 'rdr-55069', 'property 55069',
    'look up 55069', 'tell me about listing 55069', etc."""
    q = query.strip()

    # Strip common conversational prefixes
    q = re.sub(
        r"^(look\s*up|tell\s+me\s+about|details?\s+(on|for|about)|"
        r"info\s+(on|about|for)|what\s+about|show\s+me|find|search\s+for|get)\s+",
        "", q, flags=re.IGNORECASE
    ).strip()

    # Strip "property", "listing", "id", "number", "rdr" prefixes
    q = re.sub(
        r"^(property|listing|id|number|rdr)[- :]*",
        "", q, flags=re.IGNORECASE
    ).strip()

    # Strip trailing "property"
    q = re.sub(r"[- ]?property$", "", q, flags=re.IGNORECASE).strip()

    # Strip "rdr-" or "rdr " prefix if still present
    q = re.sub(r"^rdr[- ]?", "", q, flags=re.IGNORECASE).strip()

    # Now check if what remains is a 4-6 digit number
    if re.fullmatch(r"\d{4,6}", q):
        property_id = int(q)
        logger.info(f"🔍 Extracted property ID {property_id} from query: '{query}'")
        return property_id

    # Fallback: search for a 4-6 digit number anywhere in the original query
    # Only match if it looks like an ID reference (near words like property, listing, id, rdr)
    id_context = re.search(
        r"(?:property|listing|id|rdr|number|#)[- :]*(\d{4,6})\b",
        query, flags=re.IGNORECASE
    )
    if id_context:
        property_id = int(id_context.group(1))
        logger.info(f"🔍 Extracted property ID {property_id} from context match in: '{query}'")
        return property_id

    return None


# Words to remove from the search query before sending to WordPress
_STOP_WORDS = {
    "i", "me", "my", "want", "looking", "for", "a", "an", "the", "in", "on",
    "at", "to", "of", "with", "and", "or", "under", "over", "below", "above",
    "around", "about", "near", "less", "than", "more", "between", "from",
    "any", "some", "please", "find", "show", "search", "get", "list",
    "available", "properties", "listings", "real", "estate", "budget",
    "price", "priced", "range", "up", "down", "max", "maximum", "minimum",
    "min", "dollar", "dollars", "usd", "k", "bedroom", "bedrooms", "bed",
    "beds", "bath", "baths", "bathroom", "bathrooms", "sqft", "sq", "ft",
    "square", "feet", "that", "are", "is", "be", "have", "has", "can",
    "do", "does", "what", "which", "where", "how", "much", "many",
}


def _build_search_keywords(query: str, matched_terms: list[str]) -> Optional[str]:
    """Extract meaningful search keywords from the NL query.
    Removes matched taxonomy terms, stop words, and numbers.
    Returns None if no useful keywords remain (taxonomy filters are enough)."""
    q = query.lower()

    # Remove matched taxonomy terms (already used as filters)
    for term in matched_terms:
        q = q.replace(term.lower(), " ")

    # Tokenize and filter
    words = re.findall(r"[a-z]+", q)
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 1]

    if not keywords:
        return None

    result = " ".join(keywords)
    logger.info(f"🔍 Extracted search keywords: '{result}' (from: '{query}')")
    return result


def _parse_query_filters(query: str) -> dict[str, Any]:
    """Extract WordPress API filter params from a natural-language query."""
    q = query.lower()
    params: dict[str, Any] = {"per_page": 20, "status": "publish"}
    matched_terms: list[str] = []

    # Match property type
    for name, tid in _property_type_map.items():
        if name in q:
            params["property-type"] = tid
            matched_terms.append(name)
            logger.info(f"🔍 Matched property type: '{name}' → ID {tid}")
            break

    # Match city
    for name, tid in _city_map.items():
        if name in q:
            params["property-city"] = tid
            matched_terms.append(name)
            logger.info(f"🔍 Matched city: '{name}' → ID {tid}")
            break

    # Match status (default to for-sale)
    matched_status = False
    for name, tid in _status_map.items():
        if name in q:
            params["property-status"] = tid
            matched_terms.append(name)
            matched_status = True
            logger.info(f"🔍 Matched status: '{name}' → ID {tid}")
            break
    if not matched_status:
        if "for sale" in _status_map:
            params["property-status"] = _status_map["for sale"]

    # Only add search= if we have useful keywords AND no taxonomy filters,
    # or if the keywords add meaningful specificity beyond the filters.
    has_taxonomy_filters = "property-type" in params or "property-city" in params
    keywords = _build_search_keywords(query, matched_terms)

    if keywords and not has_taxonomy_filters:
        # No taxonomy filters matched — rely on keyword search
        params["search"] = keywords
        logger.info(f"🔍 Using keyword search (no taxonomy filters): '{keywords}'")
    elif keywords and has_taxonomy_filters:
        # We have filters — only add keywords if they seem specific enough
        # (e.g., "beachfront", "oceanview" — not generic words)
        if len(keywords.split()) <= 2:
            params["search"] = keywords
            logger.info(f"🔍 Adding keyword search alongside filters: '{keywords}'")
        else:
            logger.info(f"🔍 Skipping keyword search (taxonomy filters sufficient, keywords too broad): '{keywords}'")
    else:
        logger.info("🔍 No keyword search needed — using taxonomy filters only")

    logger.info(f"🔍 Final API params: {params}")
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


async def _fetch_property_by_id(property_id: int) -> Optional[dict]:
    """Fetch a single property by its WordPress post ID."""
    url = f"{REALTORDR_API_BASE}/properties/{property_id}"
    logger.info(f"🌐 Fetching property by ID: GET {url}")
    try:
        async with aiohttp.ClientSession(headers=API_HEADERS) as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as resp:
                logger.info(f"🌐 Property ID {property_id}: HTTP {resp.status}")
                if resp.status == 200:
                    raw = await resp.json()
                    result = _extract_property_fields(raw)
                    logger.info(f"🌐 Property ID {property_id}: '{result.get('title')}' | ${result.get('price', 'N/A')}")
                    return result
                body = await resp.text()
                logger.warning(f"🌐 Property ID {property_id}: HTTP {resp.status} — {body[:200]}")
                return None
    except Exception as e:
        logger.error(f"🌐 Property ID {property_id} request failed: {e}")
        return None


async def _fetch_properties(params: dict) -> list[dict]:
    """Query the WordPress REST API and return extracted property data."""
    url = f"{REALTORDR_API_BASE}/properties"
    logger.info(f"🌐 Searching properties: GET {url} params={params}")
    try:
        async with aiohttp.ClientSession(headers=API_HEADERS) as session:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as resp:
                logger.info(f"🌐 Property search: HTTP {resp.status}")
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(f"🌐 Property search: HTTP {resp.status} — {body[:200]}")
                    return []
                raw = await resp.json()
                results = [_extract_property_fields(p) for p in raw]
                logger.info(f"🌐 Property search: {len(results)} results returned")
                for i, r in enumerate(results[:3]):
                    logger.info(f"   #{i+1}: ID {r['id']} — {r['title']} | ${r.get('price', 'N/A')}")
                return results
    except Exception as e:
        logger.error(f"🌐 Property search request failed: {e}")
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

    logger.info(f"🤖 Sending {len(properties)} properties to o4-mini for voice summary...")
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
        summary = response.choices[0].message.content
        logger.info(f"🤖 o4-mini summary generated ({len(summary)} chars)")
        return summary
    except Exception as e:
        logger.error(f"🤖 o4-mini summarization failed: {e}")
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
    logger.info(f"🏠 Property search called with query: '{query}'")

    # Check if the query is a property ID lookup
    property_id = _extract_property_id(query)
    if property_id:
        logger.info(f"🏠 → ID lookup path: property {property_id}")
        prop = await _fetch_property_by_id(property_id)
        properties = [prop] if prop else []
    else:
        logger.info(f"🏠 → Search path: parsing filters from query")
        params = _parse_query_filters(query)
        properties = await _fetch_properties(params)

    logger.info(f"🏠 Found {len(properties)} properties — generating voice summary")

    summary = await _summarize_for_voice(client, query, properties)
    logger.info(f"🏠 Property search complete. Summary: {summary[:100]}...")
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
