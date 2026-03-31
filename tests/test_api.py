"""
tests/test_api.py
-----------------
Unit tests for every Flask REST endpoint.

Run with:
    pytest tests/test_api.py -v
"""

import pytest
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
import app.database as db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Yield a Flask test client and reset the database to a clean known
    state before every test so tests are fully independent.
    """
    flask_app = create_app(testing=True)

    # Reset inventory to a predictable seed for each test
    db.inventory.clear()
    db.inventory.extend([
        {
            "id": "test-1",
            "barcode": "111111111111",
            "product_name": "Test Almond Milk",
            "brands": "TestBrand",
            "category": "Beverages",
            "ingredients_text": "Water, almonds",
            "nutriments": {"energy_kcal": 30, "fat": 2, "carbohydrates": 1, "proteins": 1},
            "quantity": "32 fl oz",
            "image_url": "",
            "price": 3.99,
            "stock": 50,
        },
        {
            "id": "test-2",
            "barcode": "222222222222",
            "product_name": "Test Granola Bar",
            "brands": "TestBrand",
            "category": "Snacks",
            "ingredients_text": "Oats, honey",
            "nutriments": {"energy_kcal": 200, "fat": 5, "carbohydrates": 30, "proteins": 4},
            "quantity": "1.4 oz",
            "image_url": "",
            "price": 1.29,
            "stock": 100,
        },
    ])

    with flask_app.test_client() as test_client:
        yield test_client


# ── GET /inventory ─────────────────────────────────────────────────────────────

class TestGetAllInventory:
    def test_returns_200(self, client):
        resp = client.get("/inventory")
        assert resp.status_code == 200

    def test_returns_success_status(self, client):
        data = client.get("/inventory").get_json()
        assert data["status"] == "success"

    def test_returns_all_items(self, client):
        data = client.get("/inventory").get_json()
        assert len(data["data"]) == 2

    def test_items_have_required_fields(self, client):
        items = client.get("/inventory").get_json()["data"]
        for item in items:
            for field in ("id", "product_name", "price", "stock"):
                assert field in item, f"Missing field '{field}' in item"


# ── GET /inventory/<id> ────────────────────────────────────────────────────────

class TestGetSingleItem:
    def test_returns_200_for_existing_item(self, client):
        resp = client.get("/inventory/test-1")
        assert resp.status_code == 200

    def test_returns_correct_item(self, client):
        item = client.get("/inventory/test-1").get_json()["data"]
        assert item["product_name"] == "Test Almond Milk"
        assert item["price"] == 3.99

    def test_returns_404_for_unknown_id(self, client):
        resp = client.get("/inventory/does-not-exist")
        assert resp.status_code == 404

    def test_404_has_error_status(self, client):
        body = client.get("/inventory/does-not-exist").get_json()
        assert body["status"] == "error"


# ── POST /inventory ────────────────────────────────────────────────────────────

class TestCreateItem:
    def test_returns_201_on_success(self, client):
        resp = client.post("/inventory", json={
            "product_name": "New Product",
            "price": 2.50,
            "stock": 10,
        })
        assert resp.status_code == 201

    def test_item_appears_in_inventory_after_create(self, client):
        client.post("/inventory", json={"product_name": "Fresh Juice", "price": 1.99, "stock": 30})
        items = client.get("/inventory").get_json()["data"]
        names = [i["product_name"] for i in items]
        assert "Fresh Juice" in names

    def test_returns_created_item_in_response(self, client):
        resp = client.post("/inventory", json={"product_name": "Sparkling Water", "price": 0.99, "stock": 5})
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["data"]["product_name"] == "Sparkling Water"

    def test_400_when_product_name_missing(self, client):
        resp = client.post("/inventory", json={"price": 1.00, "stock": 5})
        assert resp.status_code == 400

    def test_400_when_body_is_not_json(self, client):
        resp = client.post("/inventory", data="not json", content_type="text/plain")
        assert resp.status_code == 400

    def test_inventory_count_increases_by_one(self, client):
        before = len(client.get("/inventory").get_json()["data"])
        client.post("/inventory", json={"product_name": "Widget", "price": 0.50, "stock": 1})
        after = len(client.get("/inventory").get_json()["data"])
        assert after == before + 1


# ── PATCH /inventory/<id> ──────────────────────────────────────────────────────

class TestUpdateItem:
    def test_returns_200_on_success(self, client):
        resp = client.patch("/inventory/test-1", json={"price": 5.99})
        assert resp.status_code == 200

    def test_price_is_updated(self, client):
        client.patch("/inventory/test-1", json={"price": 9.99})
        item = client.get("/inventory/test-1").get_json()["data"]
        assert item["price"] == 9.99

    def test_stock_is_updated(self, client):
        client.patch("/inventory/test-2", json={"stock": 250})
        item = client.get("/inventory/test-2").get_json()["data"]
        assert item["stock"] == 250

    def test_partial_update_does_not_wipe_other_fields(self, client):
        client.patch("/inventory/test-1", json={"price": 4.49})
        item = client.get("/inventory/test-1").get_json()["data"]
        # brand should be untouched
        assert item["brands"] == "TestBrand"

    def test_returns_404_for_unknown_id(self, client):
        resp = client.patch("/inventory/ghost-id", json={"price": 1.00})
        assert resp.status_code == 404

    def test_400_when_body_is_not_json(self, client):
        resp = client.patch("/inventory/test-1", data="bad", content_type="text/plain")
        assert resp.status_code == 400


# ── DELETE /inventory/<id> ─────────────────────────────────────────────────────

class TestDeleteItem:
    def test_returns_200_on_success(self, client):
        resp = client.delete("/inventory/test-1")
        assert resp.status_code == 200

    def test_item_no_longer_in_inventory(self, client):
        client.delete("/inventory/test-1")
        resp = client.get("/inventory/test-1")
        assert resp.status_code == 404

    def test_inventory_count_decreases_by_one(self, client):
        before = len(client.get("/inventory").get_json()["data"])
        client.delete("/inventory/test-2")
        after = len(client.get("/inventory").get_json()["data"])
        assert after == before - 1

    def test_returns_deleted_item_in_response(self, client):
        body = client.delete("/inventory/test-1").get_json()
        assert body["data"]["deleted"]["product_name"] == "Test Almond Milk"

    def test_returns_404_for_unknown_id(self, client):
        resp = client.delete("/inventory/no-such-item")
        assert resp.status_code == 404


# ── GET /inventory/search/barcode/<barcode> ────────────────────────────────────

class TestSearchBarcode:
    def test_returns_product_on_valid_barcode(self, client, mocker):
        mock_product = {
            "barcode": "0041570050057",
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "category": "Beverages",
            "ingredients_text": "Water, almonds",
            "quantity": "64 fl oz",
            "image_url": "",
            "nutriments": {"energy_kcal": 30, "fat": 2, "carbohydrates": 1, "proteins": 1},
        }
        mocker.patch("app.routes.fetch_by_barcode", return_value=mock_product)
        resp = client.get("/inventory/search/barcode/0041570050057")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["product_name"] == "Organic Almond Milk"

    def test_returns_404_when_barcode_not_found(self, client, mocker):
        mocker.patch("app.routes.fetch_by_barcode", return_value=None)
        resp = client.get("/inventory/search/barcode/0000000000000")
        assert resp.status_code == 404


# ── GET /inventory/search/name/<name> ─────────────────────────────────────────

class TestSearchName:
    def test_returns_results_list(self, client, mocker):
        mocker.patch("app.routes.fetch_by_name", return_value=[
            {"product_name": "Cheerios", "brands": "General Mills", "category": "Cereal",
             "ingredients_text": "", "quantity": "", "image_url": "", "nutriments": {}}
        ])
        resp = client.get("/inventory/search/name/cheerios")
        assert resp.status_code == 200
        assert isinstance(resp.get_json()["data"], list)

    def test_returns_404_when_no_results(self, client, mocker):
        mocker.patch("app.routes.fetch_by_name", return_value=[])
        resp = client.get("/inventory/search/name/xyznotaproduct")
        assert resp.status_code == 404


# ── POST /inventory/import/<barcode> ──────────────────────────────────────────

class TestImportFromApi:
    def test_imports_product_into_inventory(self, client, mocker):
        mock_product = {
            "barcode": "0041570050057",
            "product_name": "Mocked Milk",
            "brands": "MockBrand",
            "category": "Dairy",
            "ingredients_text": "",
            "quantity": "1L",
            "image_url": "",
            "nutriments": {},
        }
        mocker.patch("app.routes.fetch_by_barcode", return_value=mock_product)
        resp = client.post("/inventory/import/0041570050057",
                           json={"price": 2.49, "stock": 40})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["data"]["product_name"] == "Mocked Milk"
        assert body["data"]["price"] == 2.49
        assert body["data"]["stock"] == 40

    def test_returns_404_when_api_fails(self, client, mocker):
        mocker.patch("app.routes.fetch_by_barcode", return_value=None)
        resp = client.post("/inventory/import/0000000000000", json={})
        assert resp.status_code == 404