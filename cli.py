#!/usr/bin/env python3
"""
cli/cli.py
----------
Command-Line Interface for the Inventory Management System.

Connects to the Flask API running at http://127.0.0.1:5000 and lets
employees manage inventory without leaving the terminal.

Usage:
    python cli/cli.py
"""

import sys
import json
import requests

API_BASE = "http://127.0.0.1:5000/inventory"


# ── Low-level HTTP helpers ────────────────────────────────────────────────────

def _get(path=""):
    try:
        r = requests.get(API_BASE + path, timeout=5)
        return r.json()
    except requests.ConnectionError:
        _fatal("Cannot reach the API server. Is 'python run.py' running?")
    except Exception as exc:
        _fatal(f"Unexpected error: {exc}")


def _post(path="", body=None):
    try:
        r = requests.post(API_BASE + path, json=body or {}, timeout=5)
        return r.json()
    except requests.ConnectionError:
        _fatal("Cannot reach the API server. Is 'python run.py' running?")
    except Exception as exc:
        _fatal(f"Unexpected error: {exc}")


def _patch(path, body):
    try:
        r = requests.patch(API_BASE + path, json=body, timeout=5)
        return r.json()
    except requests.ConnectionError:
        _fatal("Cannot reach the API server. Is 'python run.py' running?")
    except Exception as exc:
        _fatal(f"Unexpected error: {exc}")


def _delete(path):
    try:
        r = requests.delete(API_BASE + path, timeout=5)
        return r.json()
    except requests.ConnectionError:
        _fatal("Cannot reach the API server. Is 'python run.py' running?")
    except Exception as exc:
        _fatal(f"Unexpected error: {exc}")


# ── Display helpers ───────────────────────────────────────────────────────────

DIVIDER = "─" * 60


def _fatal(msg: str):
    print(f"\n  ✖  ERROR: {msg}\n")
    sys.exit(1)


def _print_item(item: dict):
    """Pretty-print a single inventory item."""
    print(f"\n  {'ID':<18} {item.get('id', '')}")
    print(f"  {'Product':<18} {item.get('product_name', '')}")
    print(f"  {'Brand':<18} {item.get('brands', '')}")
    print(f"  {'Category':<18} {item.get('category', '')}")
    print(f"  {'Barcode':<18} {item.get('barcode', '')}")
    print(f"  {'Quantity':<18} {item.get('quantity', '')}")
    print(f"  {'Price':<18} ${item.get('price', 0):.2f}")
    print(f"  {'Stock':<18} {item.get('stock', 0)} units")
    ingredients = item.get('ingredients_text', '')
    if ingredients:
        short = ingredients[:80] + ("…" if len(ingredients) > 80 else "")
        print(f"  {'Ingredients':<18} {short}")
    nutriments = item.get('nutriments', {})
    if nutriments:
        print(f"  {'Nutrition(/100g)':<18} "
              f"kcal {nutriments.get('energy_kcal', 0)}  "
              f"fat {nutriments.get('fat', 0)}g  "
              f"carbs {nutriments.get('carbohydrates', 0)}g  "
              f"protein {nutriments.get('proteins', 0)}g")
    print()


def _print_item_row(item: dict):
    """Print a compact table row."""
    print(f"  {item['id']:<10} {item['product_name']:<30} "
          f"${item['price']:<8.2f} {item['stock']:<8} {item.get('category', '')}")


def _prompt(label: str, default=None) -> str:
    """Prompt user and return stripped input (returns default if blank)."""
    hint = f" [{default}]" if default is not None else ""
    val = input(f"  {label}{hint}: ").strip()
    return val if val else (str(default) if default is not None else "")


# ── Feature functions ─────────────────────────────────────────────────────────

def view_all_inventory():
    """List all inventory items in a compact table."""
    result = _get()
    if result["status"] != "success":
        print(f"\n  Error: {result['message']}\n")
        return
    items = result["data"]
    if not items:
        print("\n  Inventory is empty.\n")
        return
    print(f"\n  {DIVIDER}")
    print(f"  {'ID':<10} {'Product':<30} {'Price':<9} {'Stock':<8} Category")
    print(f"  {DIVIDER}")
    for item in items:
        _print_item_row(item)
    print(f"  {DIVIDER}")
    print(f"  Total items: {len(items)}\n")


def view_single_item():
    """Fetch and display one inventory item by id."""
    item_id = _prompt("Enter item ID")
    if not item_id:
        print("  Cancelled.\n")
        return
    result = _get(f"/{item_id}")
    if result["status"] != "success":
        print(f"\n  ✖  {result['message']}\n")
        return
    print(f"\n  {DIVIDER}")
    _print_item(result["data"])


def add_new_item():
    """Interactively create a new inventory item."""
    print(f"\n  {DIVIDER}")
    print("  Add New Inventory Item  (press Enter to leave a field blank)")
    print(f"  {DIVIDER}")

    product_name = _prompt("Product name")
    if not product_name:
        print("  Product name is required. Cancelled.\n")
        return

    body = {
        "product_name": product_name,
        "brands":            _prompt("Brand"),
        "category":          _prompt("Category"),
        "barcode":           _prompt("Barcode (optional)"),
        "quantity":          _prompt("Quantity (e.g. 500g)"),
        "ingredients_text":  _prompt("Ingredients (optional)"),
    }

    try:
        body["price"] = float(_prompt("Price ($)", 0.0))
        body["stock"] = int(_prompt("Stock (units)", 0))
    except ValueError:
        print("  ✖  Invalid price or stock value. Cancelled.\n")
        return

    result = _post("", body)
    if result["status"] != "success":
        print(f"\n  ✖  {result['message']}\n")
        return
    print(f"\n  ✔  Item added successfully!")
    _print_item(result["data"])


def update_item_menu():
    """Update price and/or stock of an existing item."""
    item_id = _prompt("Enter item ID to update")
    if not item_id:
        print("  Cancelled.\n")
        return

    # Show current state first
    current = _get(f"/{item_id}")
    if current["status"] != "success":
        print(f"\n  ✖  {current['message']}\n")
        return

    item = current["data"]
    print(f"\n  Updating: {item['product_name']} (id={item['id']})")
    print("  Leave any field blank to keep the current value.\n")

    updates = {}

    new_price = _prompt(f"New price", item["price"])
    try:
        updates["price"] = float(new_price)
    except (ValueError, TypeError):
        print("  ✖  Invalid price – skipping price update.")

    new_stock = _prompt(f"New stock", item["stock"])
    try:
        updates["stock"] = int(new_stock)
    except (ValueError, TypeError):
        print("  ✖  Invalid stock – skipping stock update.")

    new_name = _prompt(f"New product name (blank to keep)")
    if new_name:
        updates["product_name"] = new_name

    new_cat = _prompt(f"New category (blank to keep)")
    if new_cat:
        updates["category"] = new_cat

    if not updates:
        print("  No changes made.\n")
        return

    result = _patch(f"/{item_id}", updates)
    if result["status"] != "success":
        print(f"\n  ✖  {result['message']}\n")
        return
    print(f"\n  ✔  Item updated successfully!")
    _print_item(result["data"])


def delete_item_menu():
    """Delete an inventory item after confirmation."""
    item_id = _prompt("Enter item ID to delete")
    if not item_id:
        print("  Cancelled.\n")
        return

    current = _get(f"/{item_id}")
    if current["status"] != "success":
        print(f"\n  ✖  {current['message']}\n")
        return

    item = current["data"]
    print(f"\n  About to delete: {item['product_name']} (id={item['id']})")
    confirm = input("  Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("  Deletion cancelled.\n")
        return

    result = _delete(f"/{item_id}")
    if result["status"] != "success":
        print(f"\n  ✖  {result['message']}\n")
        return
    print(f"\n  ✔  Item '{item['product_name']}' deleted.\n")


def search_external_api():
    """Search OpenFoodFacts by barcode or name."""
    print(f"\n  {DIVIDER}")
    print("  Search OpenFoodFacts API")
    print(f"  {DIVIDER}")
    print("  1) Search by barcode")
    print("  2) Search by product name")
    choice = input("  Choice: ").strip()

    if choice == "1":
        barcode = _prompt("Barcode")
        if not barcode:
            print("  Cancelled.\n")
            return
        result = _get(f"/search/barcode/{barcode}")
        if result["status"] != "success":
            print(f"\n  ✖  {result['message']}\n")
            return
        print(f"\n  Found on OpenFoodFacts:")
        _print_item(result["data"])

        # Offer to import
        if input("  Add this product to local inventory? (yes/no): ").strip().lower() == "yes":
            try:
                price = float(_prompt("Price ($)", 0.0))
                stock = int(_prompt("Stock (units)", 0))
            except ValueError:
                print("  ✖  Invalid values. Import cancelled.\n")
                return
            import_result = _post(f"/import/{barcode}", {"price": price, "stock": stock})
            if import_result["status"] != "success":
                print(f"\n  ✖  {import_result['message']}\n")
            else:
                print(f"\n  ✔  Product imported! Assigned id: {import_result['data']['id']}\n")

    elif choice == "2":
        name = _prompt("Product name")
        if not name:
            print("  Cancelled.\n")
            return
        result = _get(f"/search/name/{name}")
        if result["status"] != "success":
            print(f"\n  ✖  {result['message']}\n")
            return
        products = result["data"]
        print(f"\n  Found {len(products)} result(s):\n")
        for i, p in enumerate(products, start=1):
            print(f"  [{i}] {p.get('product_name', 'Unknown')}  |  {p.get('brands', '')}  |  {p.get('quantity', '')}")
        print()
    else:
        print("  Invalid choice.\n")


# ── Main menu loop ────────────────────────────────────────────────────────────

MENU = """
  ╔══════════════════════════════════════════════╗
  ║      INVENTORY MANAGEMENT SYSTEM  v1.0       ║
  ╠══════════════════════════════════════════════╣
  ║  1  View all inventory                       ║
  ║  2  View single item                         ║
  ║  3  Add new item                             ║
  ║  4  Update item (price / stock / name)       ║
  ║  5  Delete item                              ║
  ║  6  Search OpenFoodFacts API                 ║
  ║  0  Exit                                     ║
  ╚══════════════════════════════════════════════╝
"""

ACTIONS = {
    "1": view_all_inventory,
    "2": view_single_item,
    "3": add_new_item,
    "4": update_item_menu,
    "5": delete_item_menu,
    "6": search_external_api,
}


def main():
    print(MENU)
    while True:
        choice = input("  > Select an option: ").strip()
        if choice == "0":
            print("\n  Goodbye!\n")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("  Invalid option. Please enter 0–6.\n")
        input("  Press Enter to continue…")
        print(MENU)


if __name__ == "__main__":
    main()