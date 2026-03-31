"""
external_api.py
---------------
Integration with the OpenFoodFacts public API.
Provides helpers to search by barcode or product name.
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 8  # seconds


def _extract_product_fields(raw_product: dict) -> dict:
    """
    Pluck only the fields relevant to our inventory schema
    from a raw OpenFoodFacts product dict.
    """
    nutriments = raw_product.get("nutriments", {})
    return {
        "product_name": raw_product.get("product_name", ""),
        "brands": raw_product.get("brands", ""),
        "category": raw_product.get("categories", "").split(",")[0].strip(),
        "ingredients_text": raw_product.get("ingredients_text", ""),
        "quantity": raw_product.get("quantity", ""),
        "image_url": raw_product.get("image_front_url", ""),
        "nutriments": {
            "energy_kcal": nutriments.get("energy-kcal_100g", 0),
            "fat": nutriments.get("fat_100g", 0),
            "carbohydrates": nutriments.get("carbohydrates_100g", 0),
            "proteins": nutriments.get("proteins_100g", 0),
        },
    }


def fetch_by_barcode(barcode: str) -> dict | None:
    """
    Query the OpenFoodFacts API for a product by barcode.

    Returns a dict of product fields on success, or None on failure.
    """
    url = f"{BASE_URL}/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 1 and "product" in data:
            product = _extract_product_fields(data["product"])
            product["barcode"] = barcode
            return product
        return None
    except requests.RequestException as exc:
        print(f"[external_api] Request failed: {exc}")
        return None


def fetch_by_name(name: str) -> list[dict]:
    """
    Search OpenFoodFacts by product name.

    Returns a list of up to 5 matching product dicts.
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        products = data.get("products", [])
        return [_extract_product_fields(p) for p in products if p.get("product_name")]
    except requests.RequestException as exc:
        print(f"[external_api] Request failed: {exc}")
        return []