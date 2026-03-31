"""
database.py
-----------
Simulated in-memory database for the inventory management system.
Modelled after the OpenFoodFacts API response structure.
"""

import uuid

# ---------------------------------------------------------------------------
# Mock inventory – each entry mirrors OpenFoodFacts product fields plus
# store-specific fields (id, price, stock, category, barcode).
# ---------------------------------------------------------------------------

inventory = [
    {
        "id": "1",
        "barcode": "0041570050057",
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "category": "Beverages",
        "ingredients_text": "Filtered water, almonds, cane sugar, calcium carbonate, sea salt, carrageenan, vitamin E acetate",
        "nutriments": {
            "energy_kcal": 30,
            "fat": 2.5,
            "carbohydrates": 1,
            "proteins": 1
        },
        "quantity": "64 fl oz",
        "image_url": "https://images.openfoodfacts.org/images/products/004/157/005/0057/front_en.jpg",
        "price": 4.99,
        "stock": 120,
    },
    {
        "id": "2",
        "barcode": "016000275720",
        "product_name": "Cheerios",
        "brands": "General Mills",
        "category": "Breakfast Cereals",
        "ingredients_text": "Whole grain oats, modified corn starch, sugar, salt, calcium carbonate, oat bran",
        "nutriments": {
            "energy_kcal": 100,
            "fat": 2,
            "carbohydrates": 20,
            "proteins": 3
        },
        "quantity": "8.9 oz",
        "image_url": "https://images.openfoodfacts.org/images/products/016/000/275/720/front_en.jpg",
        "price": 3.79,
        "stock": 85,
    },
    {
        "id": "3",
        "barcode": "021000658459",
        "product_name": "Kraft Mac & Cheese",
        "brands": "Kraft",
        "category": "Pasta & Grains",
        "ingredients_text": "Enriched macaroni product, cheese sauce mix, whey, milkfat, milk protein concentrate",
        "nutriments": {
            "energy_kcal": 250,
            "fat": 3,
            "carbohydrates": 47,
            "proteins": 9
        },
        "quantity": "7.25 oz",
        "image_url": "https://images.openfoodfacts.org/images/products/021/000/658/459/front_en.jpg",
        "price": 1.49,
        "stock": 200,
    },
    {
        "id": "4",
        "barcode": "028400597951",
        "product_name": "Lay's Classic Potato Chips",
        "brands": "Lay's",
        "category": "Snacks",
        "ingredients_text": "Potatoes, vegetable oil (sunflower, corn, and/or canola oil), salt",
        "nutriments": {
            "energy_kcal": 160,
            "fat": 10,
            "carbohydrates": 15,
            "proteins": 2
        },
        "quantity": "8 oz",
        "image_url": "https://images.openfoodfacts.org/images/products/028/400/597/951/front_en.jpg",
        "price": 4.29,
        "stock": 60,
    },
    {
        "id": "5",
        "barcode": "044000030032",
        "product_name": "Oreo Cookies",
        "brands": "Nabisco",
        "category": "Cookies & Biscuits",
        "ingredients_text": "Unbleached enriched flour, sugar, palm and/or canola oil, cocoa, high fructose corn syrup, leavening",
        "nutriments": {
            "energy_kcal": 140,
            "fat": 6,
            "carbohydrates": 21,
            "proteins": 1
        },
        "quantity": "14.3 oz",
        "image_url": "https://images.openfoodfacts.org/images/products/044/000/003/0032/front_en.jpg",
        "price": 4.49,
        "stock": 150,
    },
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def get_all_items():
    """Return a copy of the full inventory list."""
    return list(inventory)


def get_item_by_id(item_id: str):
    """Return a single item by its string id, or None if not found."""
    return next((item for item in inventory if item["id"] == str(item_id)), None)


def add_item(data: dict):
    """
    Append a new item to the inventory.
    Generates a unique id if one is not supplied.
    Returns the newly created item.
    """
    new_item = {
        "id": data.get("id", str(uuid.uuid4())[:8]),
        "barcode": data.get("barcode", ""),
        "product_name": data.get("product_name", "Unknown Product"),
        "brands": data.get("brands", ""),
        "category": data.get("category", "Uncategorized"),
        "ingredients_text": data.get("ingredients_text", ""),
        "nutriments": data.get("nutriments", {}),
        "quantity": data.get("quantity", ""),
        "image_url": data.get("image_url", ""),
        "price": float(data.get("price", 0.0)),
        "stock": int(data.get("stock", 0)),
    }
    inventory.append(new_item)
    return new_item


def update_item(item_id: str, updates: dict):
    """
    Apply partial updates (PATCH semantics) to an existing item.
    Returns the updated item, or None if not found.
    """
    item = get_item_by_id(item_id)
    if item is None:
        return None
    # Coerce numeric fields if supplied
    if "price" in updates:
        updates["price"] = float(updates["price"])
    if "stock" in updates:
        updates["stock"] = int(updates["stock"])
    item.update(updates)
    return item


def delete_item(item_id: str):
    """
    Remove an item by id.
    Returns the removed item, or None if not found.
    """
    item = get_item_by_id(item_id)
    if item is None:
        return None
    inventory.remove(item)
    return item