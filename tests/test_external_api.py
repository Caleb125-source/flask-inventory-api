"""
tests/test_external_api.py
--------------------------
Unit tests for app/external_api.py using unittest.mock so no real
HTTP requests are made during the test suite.

Run with:
    pytest tests/test_external_api.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.external_api import fetch_by_barcode, fetch_by_name


# ── Shared mock helpers ────────────────────────────────────────────────────────

def _mock_response(json_data: dict, status_code: int = 200, raise_for=None):
    """Build a MagicMock that behaves like a requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    if raise_for:
        mock.raise_for_status.side_effect = raise_for
    else:
        mock.raise_for_status.return_value = None
    return mock


SAMPLE_OFF_PRODUCT = {
    "product_name": "Organic Almond Milk",
    "brands": "Silk",
    "categories": "Beverages, Plant-based drinks",
    "ingredients_text": "Water, almonds, sugar",
    "quantity": "64 fl oz",
    "image_front_url": "https://example.com/milk.jpg",
    "nutriments": {
        "energy-kcal_100g": 30,
        "fat_100g": 2.5,
        "carbohydrates_100g": 1.0,
        "proteins_100g": 1.0,
    },
}


# ── fetch_by_barcode ───────────────────────────────────────────────────────────

class TestFetchByBarcode:
    def test_returns_product_dict_on_success(self):
        mock_resp = _mock_response({"status": 1, "product": SAMPLE_OFF_PRODUCT})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0041570050057")
        assert result is not None
        assert result["product_name"] == "Organic Almond Milk"

    def test_barcode_is_included_in_result(self):
        mock_resp = _mock_response({"status": 1, "product": SAMPLE_OFF_PRODUCT})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0041570050057")
        assert result is not None
        assert result["barcode"] == "0041570050057"

    def test_returns_none_when_status_is_zero(self):
        mock_resp = _mock_response({"status": 0})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0000000000000")
        assert result is None

    def test_returns_none_on_network_error(self):
        import requests as req_lib
        with patch("app.external_api.requests.get", side_effect=req_lib.ConnectionError):
            result = fetch_by_barcode("0041570050057")
        assert result is None

    def test_nutriments_are_mapped_correctly(self):
        mock_resp = _mock_response({"status": 1, "product": SAMPLE_OFF_PRODUCT})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0041570050057")
        assert result is not None
        assert result["nutriments"]["energy_kcal"] == 30
        assert result["nutriments"]["fat"] == 2.5

    def test_first_category_is_selected(self):
        mock_resp = _mock_response({"status": 1, "product": SAMPLE_OFF_PRODUCT})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0041570050057")
        assert result is not None
        # "Beverages, Plant-based drinks" → first token is "Beverages"
        assert result["category"] == "Beverages"

    def test_missing_product_key_returns_none(self):
        mock_resp = _mock_response({"status": 1})   # no "product" key
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_barcode("0041570050057")
        assert result is None

    def test_calls_correct_url(self):
        mock_resp = _mock_response({"status": 0})
        with patch("app.external_api.requests.get", return_value=mock_resp) as mock_get:
            fetch_by_barcode("1234567890")
        url_called = mock_get.call_args[0][0]
        assert "1234567890" in url_called
        assert "openfoodfacts" in url_called


# ── fetch_by_name ──────────────────────────────────────────────────────────────

class TestFetchByName:
    def test_returns_list_of_products(self):
        mock_resp = _mock_response({
            "products": [SAMPLE_OFF_PRODUCT, SAMPLE_OFF_PRODUCT]
        })
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_name("almond milk")
        assert isinstance(result, list)
        assert len(result) == 2

    def test_each_result_has_product_name(self):
        mock_resp = _mock_response({"products": [SAMPLE_OFF_PRODUCT]})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_name("almond milk")
        assert result is not None
        assert result[0]["product_name"] == "Organic Almond Milk"

    def test_returns_empty_list_on_network_error(self):
        import requests as req_lib
        with patch("app.external_api.requests.get", side_effect=req_lib.Timeout):
            result = fetch_by_name("milk")
        assert result == []

    def test_returns_empty_list_when_no_products_key(self):
        mock_resp = _mock_response({})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_name("nothing")
        assert result == []

    def test_filters_out_products_with_no_name(self):
        no_name_product = {**SAMPLE_OFF_PRODUCT, "product_name": ""}
        mock_resp = _mock_response({"products": [no_name_product, SAMPLE_OFF_PRODUCT]})
        with patch("app.external_api.requests.get", return_value=mock_resp):
            result = fetch_by_name("milk")
        assert result is not None
        # Only the named product should survive
        assert len(result) == 1
        assert result[0]["product_name"] == "Organic Almond Milk"

    def test_search_query_is_passed_as_param(self):
        mock_resp = _mock_response({"products": []})
        with patch("app.external_api.requests.get", return_value=mock_resp) as mock_get:
            fetch_by_name("cheerios")
        params = mock_get.call_args[1]["params"]
        assert params["search_terms"] == "cheerios"