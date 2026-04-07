"""
routes.py
---------
Flask Blueprint that exposes all inventory REST endpoints.

Routes
------
GET    /inventory            – list all items
GET    /inventory/<id>       – get one item
POST   /inventory            – create a new item
PATCH  /inventory/<id>       – partially update an item
DELETE /inventory/<id>       – delete an item
GET    /inventory/search/barcode/<barcode>  – look up on OpenFoodFacts by barcode
GET    /inventory/search/name/<name>        – search OpenFoodFacts by name
POST   /inventory/import/<barcode>          – fetch from OFF and add to inventory
"""

from flask import Blueprint, jsonify, request

from app.database import (
    add_item,
    delete_item,
    get_all_items,
    get_item_by_id,
    update_item,
)
from app.external_api import fetch_by_barcode, fetch_by_name

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


# ── Helper ────────────────────────────────────────────────────────────────────

def _ok(data, status=200):
    return jsonify({"status": "success", "data": data}), status


def _err(message, status=400):
    return jsonify({"status": "error", "message": message}), status


# ── External-API endpoints ────────────────────────────────────────────────────
# IMPORTANT: These must be registered BEFORE the /<string:item_id> routes,
# otherwise Flask will match "search" as an item_id and never reach these.

@inventory_bp.route("/search/barcode/<string:barcode>", methods=["GET"])
def search_barcode(barcode):
    """Fetch product details from OpenFoodFacts by barcode (does NOT modify inventory)."""
    product = fetch_by_barcode(barcode)
    if product is None:
        return _err(f"No product found for barcode '{barcode}'.", 404)
    return _ok(product)


@inventory_bp.route("/search/name/<string:name>", methods=["GET"])
def search_name(name):
    """Search OpenFoodFacts by product name (does NOT modify inventory)."""
    results = fetch_by_name(name)
    if not results:
        return _err(f"No products found matching '{name}'.", 404)
    return _ok(results)


@inventory_bp.route("/import/<string:barcode>", methods=["POST"])
def import_from_api(barcode):
    """
    Fetch a product from OpenFoodFacts by barcode and add it to the inventory.
    Optional JSON body fields: price, stock, category (to override/supplement API data).
    """
    product = fetch_by_barcode(barcode)
    if product is None:
        return _err(f"Could not fetch product for barcode '{barcode}' from OpenFoodFacts.", 404)

    # Allow caller to supply store-specific fields
    body = request.get_json(silent=True) or {}
    product["price"] = float(body.get("price", 0.0))
    product["stock"] = int(body.get("stock", 0))
    if "category" in body:
        product["category"] = body["category"]

    new_item = add_item(product)
    return _ok(new_item, 201)


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@inventory_bp.route("", methods=["GET"])
def list_inventory():
    """Return every item currently in the inventory."""
    items = get_all_items()
    return _ok(items)


@inventory_bp.route("/<string:item_id>", methods=["GET"])
def get_item(item_id):
    """Return a single inventory item by id."""
    item = get_item_by_id(item_id)
    if item is None:
        return _err(f"Item with id '{item_id}' not found.", 404)
    return _ok(item)


@inventory_bp.route("", methods=["POST"])
def create_item():
    """
    Create a new inventory item.
    Expects JSON body with at minimum: product_name, price, stock.
    """
    body = request.get_json(silent=True)
    if not body:
        return _err("Request body must be valid JSON.", 400)
    if not body.get("product_name"):
        return _err("'product_name' is required.", 400)
    new_item = add_item(body)
    return _ok(new_item, 201)


@inventory_bp.route("/<string:item_id>", methods=["PATCH"])
def update_item_route(item_id):
    """
    Partially update an inventory item.
    Only fields present in the request body are changed.
    """
    body = request.get_json(silent=True)
    if not body:
        return _err("Request body must be valid JSON.", 400)
    updated = update_item(item_id, body)
    if updated is None:
        return _err(f"Item with id '{item_id}' not found.", 404)
    return _ok(updated)


@inventory_bp.route("/<string:item_id>", methods=["DELETE"])
def delete_item_route(item_id):
    """Remove an inventory item permanently."""
    removed = delete_item(item_id)
    if removed is None:
        return _err(f"Item with id '{item_id}' not found.", 404)
    return _ok({"deleted": removed})