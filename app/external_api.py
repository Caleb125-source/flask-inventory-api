"""
external_api.py
---------------
Integration with the OpenFoodFacts public API.
Provides helpers to search by barcode or product name.

Common reasons a barcode returns nothing:
1. No User-Agent header  → OpenFoodFacts blocks the request silently
2. Timeout too short     → their servers are slow, 8s often isn't enough
3. Product not in their database (try scanning on https://world.openfoodfacts.org first)
4. Barcode has leading zeros that got stripped (always pass as a string)
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 20  # increased from 8 — OFF servers can be slow

# ⚠️  OpenFoodFacts REQUIRES a User-Agent header that identifies your app.
# Without it, many requests return empty or are silently blocked.
HEADERS = {
    "User-Agent": "FlaskInventoryApp/1.0 (contact@youremail.com)"
}


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

    Tips:
    - Always pass barcode as a string e.g. fetch_by_barcode("0012345678905")
    - Leading zeros matter — "012345" != "12345"
    - Verify the barcode exists first at https://world.openfoodfacts.org
    """
    url = f"{BASE_URL}/api/v0/product/{barcode}.json"

    print(f"[external_api] Fetching barcode: {barcode}")
    print(f"[external_api] URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        print(f"[external_api] Response status field: {data.get('status')}")

        if data.get("status") == 1 and "product" in data:
            product = _extract_product_fields(data["product"])
            product["barcode"] = barcode
            print(f"[external_api] Found: {product['product_name']}")
            return product

        # status=0 means barcode exists in OFF but product has no data,
        # or the barcode simply isn't in their database
        print(f"[external_api] Product not found in OpenFoodFacts database.")
        return None

    except requests.Timeout:
        print(f"[external_api] Request timed out after {TIMEOUT}s — try again.")
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

    print(f"[external_api] Searching by name: '{name}'")

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        products = data.get("products", [])
        results = [_extract_product_fields(p) for p in products if p.get("product_name")]
        print(f"[external_api] Found {len(results)} result(s) for '{name}'")
        return results

    except requests.Timeout:
        print(f"[external_api] Request timed out after {TIMEOUT}s — try again.")
        return []
    except requests.RequestException as exc:
        print(f"[external_api] Request failed: {exc}")
        return []