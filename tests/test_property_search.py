"""Tests for backend.tools.realtordr.property_search — pure helper functions."""

import pytest

from backend.tools.realtordr import property_search as ps


# ── _extract_property_id ─────────────────────────────────────────────────────

class TestExtractPropertyId:
    def test_direct_number(self):
        assert ps._extract_property_id("55069") == 55069

    def test_with_rdr_prefix(self):
        assert ps._extract_property_id("rdr-55069") == 55069

    def test_with_rdr_space(self):
        assert ps._extract_property_id("rdr 55069") == 55069

    def test_look_up_prefix(self):
        assert ps._extract_property_id("look up property 55069") == 55069

    def test_listing_prefix(self):
        assert ps._extract_property_id("listing 55069") == 55069

    def test_id_prefix(self):
        assert ps._extract_property_id("id 55069") == 55069

    def test_tell_me_about(self):
        assert ps._extract_property_id("tell me about rdr-55069") == 55069

    def test_details_on(self):
        assert ps._extract_property_id("details on property 55069") == 55069

    def test_too_short_returns_none(self):
        assert ps._extract_property_id("123") is None

    def test_too_long_returns_none(self):
        assert ps._extract_property_id("1234567") is None

    def test_no_id_natural_language(self):
        assert ps._extract_property_id("villa in Cabarete") is None

    def test_four_digits(self):
        assert ps._extract_property_id("5506") == 5506

    def test_six_digits(self):
        assert ps._extract_property_id("550691") == 550691

    def test_show_me(self):
        assert ps._extract_property_id("show me property 55069") == 55069

    def test_property_suffix(self):
        assert ps._extract_property_id("55069-property") == 55069


# ── _build_search_keywords ───────────────────────────────────────────────────

class TestBuildSearchKeywords:
    def test_all_stop_words_returns_none(self):
        assert ps._build_search_keywords("find me some available listings", []) is None

    def test_meaningful_keywords_remain(self):
        result = ps._build_search_keywords(
            "beachfront villa in Cabarete", ["villa", "cabarete"]
        )
        assert result == "beachfront"

    def test_single_keyword_with_matched(self):
        result = ps._build_search_keywords("beachfront", ["villa", "cabarete"])
        assert result == "beachfront"

    def test_numbers_removed(self):
        # numbers are stripped by the regex [a-z]+
        result = ps._build_search_keywords("oceanview 300000", [])
        assert result == "oceanview"

    def test_empty_string(self):
        assert ps._build_search_keywords("", []) is None


# ── _parse_query_filters ─────────────────────────────────────────────────────

class TestParseQueryFilters:
    @pytest.fixture(autouse=True)
    def _set_fallback_maps(self):
        """Ensure module-level maps are set to the fallback values."""
        ps._property_type_map = ps._FALLBACK_PROPERTY_TYPES
        ps._city_map = ps._FALLBACK_CITIES
        ps._status_map = ps._FALLBACK_STATUSES

    def test_type_and_city_match(self):
        params = ps._parse_query_filters("villa in Cabarete")
        assert params["property-type"] == 37  # villa
        assert params["property-city"] == 48  # cabarete

    def test_status_for_rent(self):
        params = ps._parse_query_filters("condo for rent in Sosua")
        assert params["property-status"] == 31  # for rent

    def test_default_status_for_sale(self):
        params = ps._parse_query_filters("villa in Cabarete")
        assert params["property-status"] == 30  # for sale (default)

    def test_keyword_only_no_taxonomy(self):
        params = ps._parse_query_filters("beachfront oceanview")
        assert "search" in params
        assert "beachfront" in params["search"]

    def test_always_has_per_page_and_status(self):
        params = ps._parse_query_filters("something random")
        assert params["per_page"] == 20
        assert params["status"] == "publish"

    def test_sold_status(self):
        params = ps._parse_query_filters("sold properties in Punta Cana")
        assert params["property-status"] == 32  # sold
        assert params["property-city"] == 51  # punta cana


# ── _extract_property_fields ─────────────────────────────────────────────────

class TestExtractPropertyFields:
    def test_full_property(self):
        prop = {
            "id": 55069,
            "title": {"rendered": "Luxury Beachfront Villa"},
            "link": "https://realtordr.com/property/55069",
            "property_meta": {
                "REAL_HOMES_property_price": ["450000"],
                "REAL_HOMES_property_bedrooms": ["4"],
                "REAL_HOMES_property_bathrooms": ["3"],
                "REAL_HOMES_property_size": ["3500"],
                "REAL_HOMES_property_address": ["Cabarete, DR"],
            },
        }
        fields = ps._extract_property_fields(prop)
        assert fields["id"] == 55069
        assert fields["title"] == "Luxury Beachfront Villa"
        assert fields["price"] == "450000"
        assert fields["bedrooms"] == "4"
        assert fields["bathrooms"] == "3"
        assert fields["size"] == "3500"
        assert fields["address"] == "Cabarete, DR"
        assert fields["link"] == "https://realtordr.com/property/55069"

    def test_missing_meta_fields(self):
        prop = {
            "id": 100,
            "title": {"rendered": "Empty Lot"},
            "link": None,
            "property_meta": {},
        }
        fields = ps._extract_property_fields(prop)
        assert fields["id"] == 100
        assert fields["price"] is None
        assert fields["bedrooms"] is None
        assert fields["bathrooms"] is None
        assert fields["size"] is None
        assert fields["address"] is None

    def test_meta_as_scalar(self):
        prop = {
            "id": 200,
            "title": {"rendered": "Test"},
            "property_meta": {
                "REAL_HOMES_property_price": 250000,
            },
        }
        fields = ps._extract_property_fields(prop)
        assert fields["price"] == 250000

    def test_meta_as_empty_list(self):
        prop = {
            "id": 300,
            "title": {"rendered": "Test"},
            "property_meta": {
                "REAL_HOMES_property_price": [],
            },
        }
        fields = ps._extract_property_fields(prop)
        assert fields["price"] is None

    def test_missing_title(self):
        prop = {"id": 400, "property_meta": {}}
        fields = ps._extract_property_fields(prop)
        assert fields["title"] == "Untitled"


# ── _summarize_for_voice ─────────────────────────────────────────────────────

class TestSummarizeForVoice:
    @pytest.mark.asyncio
    async def test_empty_list_returns_no_listings(self):
        result = await ps._summarize_for_voice(client=None, query="villas", properties=[])
        assert "wasn't able to find" in result.lower() or "no listings" in result.lower()
