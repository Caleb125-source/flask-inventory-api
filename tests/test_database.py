"""
tests/test_database.py
----------------------
Unit tests for the in-memory database helper functions in app/database.py.

Run with:
    pytest tests/test_database.py -v
"""

import pytest
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app.database as db


# ── Fixture: reset inventory before each test ─────────────────────────────────

@pytest.fixture(autouse=True)
def reset_inventory():
    """Restore inventory to a clean two-item state before every test."""
    db.inventory.clear()
    db.inventory.extend([
        {
            "id": "db-1",
            "barcode": "111",
            "product_name": "Alpha Bar",
            "brands": "AlphaCo",
            "category": "Snacks",
            "ingredients_text": "Oats, honey",
            "nutriments": {},
            "quantity": "50g",
            "image_url": "",
            "price": 1.50,
            "stock": 20,
        },
        {
            "id": "db-2",
            "barcode": "222",
            "product_name": "Beta Juice",
            "brands": "BetaCo",
            "category": "Beverages",
            "ingredients_text": "Apple juice",
            "nutriments": {},
            "quantity": "330ml",
            "image_url": "",
            "price": 2.00,
            "stock": 35,
        },
    ])
    yield


# ── get_all_items ──────────────────────────────────────────────────────────────

class TestGetAllItems:
    def test_returns_list(self):
        assert isinstance(db.get_all_items(), list)

    def test_returns_all_items(self):
        assert len(db.get_all_items()) == 2

    def test_returns_copy_not_reference(self):
        result = db.get_all_items()
        result.clear()
        # Original inventory must be untouched
        assert len(db.inventory) == 2


# ── get_item_by_id ─────────────────────────────────────────────────────────────

class TestGetItemById:
    def test_finds_existing_item(self):
        item = db.get_item_by_id("db-1")
        assert item is not None
        assert item["product_name"] == "Alpha Bar"

    def test_returns_none_for_unknown_id(self):
        assert db.get_item_by_id("no-such-id") is None

    def test_coerces_int_id_to_string(self):
        item = db.get_item_by_id("db-2")
        assert item is not None
        assert item["product_name"] == "Beta Juice"


# ── add_item ───────────────────────────────────────────────────────────────────

class TestAddItem:
    def test_item_count_increases(self):
        db.add_item({"product_name": "Gamma Chips"})
        assert len(db.inventory) == 3

    def test_returns_new_item(self):
        item = db.add_item({"product_name": "Gamma Chips", "price": 3.00, "stock": 10})
        assert item["product_name"] == "Gamma Chips"

    def test_price_is_cast_to_float(self):
        item = db.add_item({"product_name": "X", "price": "4"})
        assert isinstance(item["price"], float)

    def test_stock_is_cast_to_int(self):
        item = db.add_item({"product_name": "X", "stock": "15"})
        assert isinstance(item["stock"], int)

    def test_auto_generates_id_when_not_supplied(self):
        item = db.add_item({"product_name": "AutoId Product"})
        assert item["id"] != "" and item["id"] is not None

    def test_uses_supplied_id(self):
        item = db.add_item({"id": "custom-99", "product_name": "Custom ID"})
        assert item["id"] == "custom-99"

    def test_defaults_stock_to_zero(self):
        item = db.add_item({"product_name": "No Stock"})
        assert item["stock"] == 0

    def test_defaults_price_to_zero(self):
        item = db.add_item({"product_name": "Free Stuff"})
        assert item["price"] == 0.0


# ── update_item ────────────────────────────────────────────────────────────────

class TestUpdateItem:
    def test_updates_price(self):
        db.update_item("db-1", {"price": 9.99})
        item = db.get_item_by_id("db-1")
        assert item is not None
        assert item["price"] == 9.99

    def test_updates_stock(self):
        db.update_item("db-2", {"stock": 200})
        item = db.get_item_by_id("db-2")
        assert item is not None
        assert item["stock"] == 200

    def test_returns_updated_item(self):
        result = db.update_item("db-1", {"price": 5.00})
        assert result is not None
        assert result["price"] == 5.00

    def test_returns_none_for_unknown_id(self):
        assert db.update_item("ghost", {"price": 1.00}) is None

    def test_partial_update_preserves_other_fields(self):
        db.update_item("db-1", {"price": 7.77})
        item = db.get_item_by_id("db-1")
        assert item is not None
        assert item["brands"] == "AlphaCo"   # unchanged
        assert item["stock"] == 20            # unchanged

    def test_price_coerced_to_float(self):
        db.update_item("db-1", {"price": "3"})
        item = db.get_item_by_id("db-1")
        assert item is not None
        assert isinstance(item["price"], float)

    def test_stock_coerced_to_int(self):
        db.update_item("db-2", {"stock": "77"})
        item = db.get_item_by_id("db-2")
        assert item is not None
        assert isinstance(item["stock"], int)


# ── delete_item ────────────────────────────────────────────────────────────────

class TestDeleteItem:
    def test_removes_item_from_inventory(self):
        db.delete_item("db-1")
        assert db.get_item_by_id("db-1") is None

    def test_returns_deleted_item(self):
        removed = db.delete_item("db-2")
        assert removed is not None
        assert removed["product_name"] == "Beta Juice"

    def test_returns_none_for_unknown_id(self):
        assert db.delete_item("no-such") is None

    def test_inventory_shrinks_by_one(self):
        db.delete_item("db-1")
        assert len(db.inventory) == 1