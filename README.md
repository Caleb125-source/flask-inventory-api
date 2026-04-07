# Flask Inventory API

A lightweight inventory management system built with Flask. It exposes a RESTful API persisted to a local JSON file and includes an interactive command-line interface for day-to-day stock management. Products can be added manually or imported directly from the [OpenFoodFacts](https://world.openfoodfacts.org/) public database by barcode or name.

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the server](#running-the-server)
  - [Running the CLI](#running-the-cli)
- [API reference](#api-reference)
  - [Response format](#response-format)
  - [Inventory CRUD endpoints](#inventory-crud-endpoints)
  - [OpenFoodFacts endpoints](#openfoodfacts-endpoints)
  - [Full request & response examples](#full-request--response-examples)
- [Item schema](#item-schema)
- [CLI usage](#cli-usage)
  - [Menu overview](#menu-overview)
  - [CLI walkthrough](#cli-walkthrough)
- [Data persistence](#data-persistence)
- [Running tests](#running-tests)
- [Error handling](#error-handling)
- [Known limitations & future improvements](#known-limitations--future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Full **CRUD** operations on inventory items via a REST API
- **JSON file persistence** — no database installation required
- **OpenFoodFacts integration** — search by barcode or product name, preview results, and import directly into inventory
- **Interactive CLI** — a menu-driven terminal interface that wraps every API endpoint, designed for non-technical users
- **Auto-seeded** — ships with five real products so the system is usable immediately after cloning
- **Consistent API responses** — every endpoint returns the same `status / data / message` envelope

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Web framework | Flask |
| HTTP client (CLI & external API) | Requests |
| Data store | JSON flat file (`inventory.json`) |
| External product data | OpenFoodFacts REST API |
| Testing | pytest, pytest-mock |

---

## Project structure

```
flask-inventory-api/
│
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── database.py          # All read/write logic against inventory.json
│   ├── external_api.py      # OpenFoodFacts API client
│   └── routes.py            # Flask Blueprint — all HTTP endpoints live here
│
├── cli.py                   # Interactive terminal interface
├── run.py                   # Development server entry point
├── conftest.py              # Shared pytest fixtures
├── inventory.json           # Auto-generated on first run; gitignored by default
├── Pipfile                  # Pipenv lock file (alternative to requirements.txt)
├── requirements.txt         # pip-compatible dependency list
└── README.md
```

---

## Getting started

### Prerequisites

- Python 3.12.3 or higher
- pip (comes with Python)
- git

### Installation

**1. Clone the repository**

```bash
git clone 
cd flask-inventory-api
```

**2. Create and activate a virtual environment**

```bash
pipenv install
pipenv shell
```


### Running the server

```bash
python run.py
```

You should see:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

On the very first run, `inventory.json` is created automatically and seeded with five sample products. The file will appear in the project root.

> **Note:** `run.py` starts Flask with `debug=True` and `port=5000`. Keep this terminal open — the server must be running for the CLI and any API calls to work.

### Running the CLI

Open a **second terminal** in the same project directory, activate the virtual environment again, and run:

```bash
python cli.py
```

The CLI connects to `http://127.0.0.1:5000` and wraps every API endpoint in a friendly menu. If you see a connection error, make sure the server terminal is still running.

---

## API reference

The base URL for all endpoints is:

```
http://127.0.0.1:5000
```

### Response format

Every endpoint returns JSON in this shape:

```json
{
  "status": "success",
  "data": { ... }
}
```

On failure:

```json
{
  "status": "error",
  "message": "Human-readable explanation of what went wrong."
}
```

HTTP status codes follow standard conventions: `200` OK, `201` Created, `400` Bad Request, `404` Not Found.

---

### Inventory CRUD endpoints

#### `GET /inventory`

Returns every item currently in the inventory.

**Response `200`**

```json
{
  "status": "success",
  "data": [
    { "id": "1", "product_name": "Organic Almond Milk", "price": 4.99, "stock": 120, ... },
    { "id": "2", "product_name": "Cheerios", "price": 3.79, "stock": 85, ... }
  ]
}
```

---

#### `GET /inventory/<id>`

Fetch a single item by its string ID.

**Response `200`**

```json
{
  "status": "success",
  "data": { "id": "1", "product_name": "Organic Almond Milk", ... }
}
```

**Response `404`** — if the ID does not exist.

---

#### `POST /inventory`

Create a new inventory item.

**Required body fields:** `product_name`

**Optional body fields:** `barcode`, `brands`, `category`, `quantity`, `ingredients_text`, `nutriments`, `image_url`, `price` (default `0.0`), `stock` (default `0`)

**Request body**

```json
{
  "product_name": "Oat Milk",
  "brands": "Oatly",
  "category": "Beverages",
  "barcode": "7394376616843",
  "quantity": "1L",
  "price": 3.49,
  "stock": 50
}
```

**Response `201`**

```json
{
  "status": "success",
  "data": {
    "id": "6",
    "product_name": "Oat Milk",
    "brands": "Oatly",
    "category": "Beverages",
    "barcode": "7394376616843",
    "quantity": "1L",
    "price": 3.49,
    "stock": 50,
    "ingredients_text": "",
    "nutriments": {},
    "image_url": ""
  }
}
```

**Response `400`** — if the body is missing or `product_name` is not provided.

---

#### `PATCH /inventory/<id>`

Partially update an existing item. Only fields present in the request body are changed; everything else is left as-is.

**Request body** (any subset of item fields)

```json
{
  "price": 2.99,
  "stock": 200
}
```

**Response `200`**

```json
{
  "status": "success",
  "data": { "id": "1", "price": 2.99, "stock": 200, ... }
}
```

**Response `404`** — if the ID does not exist.

---

#### `DELETE /inventory/<id>`

Permanently remove an item from inventory.

**Response `200`**

```json
{
  "status": "success",
  "data": {
    "deleted": { "id": "1", "product_name": "Organic Almond Milk", ... }
  }
}
```

**Response `404`** — if the ID does not exist.

---

### OpenFoodFacts endpoints

These endpoints talk to the [OpenFoodFacts](https://world.openfoodfacts.org/) public API. They **do not modify your local inventory** unless you explicitly use the `/import` endpoint.

> **Heads up:** OpenFoodFacts servers can be slow. Requests time out after 20 seconds. If a lookup fails, wait a moment and try again.

---

#### `GET /inventory/search/barcode/<barcode>`

Look up a product on OpenFoodFacts by its barcode. Returns product details without saving anything locally.

**Example**

```
GET /inventory/search/barcode/0041570050057
```

**Response `200`**

```json
{
  "status": "success",
  "data": {
    "product_name": "Organic Almond Milk",
    "brands": "Silk",
    "category": "Beverages",
    "barcode": "0041570050057",
    "quantity": "64 fl oz",
    "ingredients_text": "Filtered water, almonds...",
    "nutriments": {
      "energy_kcal": 30,
      "fat": 2.5,
      "carbohydrates": 1,
      "proteins": 1
    },
    "image_url": "https://images.openfoodfacts.org/..."
  }
}
```

**Response `404`** — if the barcode is not in the OpenFoodFacts database.

---

#### `GET /inventory/search/name/<name>`

Search OpenFoodFacts by product name. Returns up to 5 matching results.

**Example**

```
GET /inventory/search/name/cheerios
```

**Response `200`**

```json
{
  "status": "success",
  "data": [
    { "product_name": "Cheerios", "brands": "General Mills", ... },
    { "product_name": "Honey Nut Cheerios", "brands": "General Mills", ... }
  ]
}
```

**Response `404`** — if no matching products are found.

---

#### `POST /inventory/import/<barcode>`

Fetch a product from OpenFoodFacts by barcode and add it directly to your local inventory in one step.

**Optional request body** — use these to supply store-specific fields that OpenFoodFacts doesn't track:

```json
{
  "price": 4.99,
  "stock": 30,
  "category": "Beverages"
}
```

`price` and `stock` default to `0` if omitted. `category` falls back to whatever OpenFoodFacts returns.

**Response `201`** — the newly created inventory item (same shape as `POST /inventory`).

**Response `404`** — if the barcode is not found on OpenFoodFacts.

---

### Full request & response examples

Below are curl examples you can run directly while the server is up.

```bash
# List all inventory
curl http://127.0.0.1:5000/inventory

# Get item with id 1
curl http://127.0.0.1:5000/inventory/1

# Create a new item
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Oat Milk", "price": 3.49, "stock": 50}'

# Update price and stock on item 1
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 3.99, "stock": 90}'

# Delete item 3
curl -X DELETE http://127.0.0.1:5000/inventory/3

# Search OpenFoodFacts by barcode
curl http://127.0.0.1:5000/inventory/search/barcode/044000030032

# Search OpenFoodFacts by name
curl http://127.0.0.1:5000/inventory/search/name/oreo

# Import from OpenFoodFacts into local inventory
curl -X POST http://127.0.0.1:5000/inventory/import/044000030032 \
  -H "Content-Type: application/json" \
  -d '{"price": 4.49, "stock": 150}'
```

---

## Item schema

Every item in the inventory follows this structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | auto | Auto-incrementing integer stored as a string |
| `product_name` | string | yes | Display name of the product |
| `barcode` | string | no | EAN/UPC barcode number |
| `brands` | string | no | Brand name(s) |
| `category` | string | no | Product category (defaults to `"Uncategorized"`) |
| `quantity` | string | no | Pack size e.g. `"500g"`, `"1L"` |
| `ingredients_text` | string | no | Raw ingredients list |
| `nutriments` | object | no | Nutrition info per 100g — see below |
| `image_url` | string | no | URL to a product image |
| `price` | float | no | Store price in dollars (defaults to `0.0`) |
| `stock` | integer | no | Units currently in stock (defaults to `0`) |

---

## CLI usage

### Menu overview

```
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
```

### CLI walkthrough

**Option 1 — View all inventory**

Prints a compact table showing ID, product name, price, stock count, and category for every item.

**Option 2 — View single item**

Prompts for an item ID and prints the full detail card including ingredients and nutrition info.

**Option 3 — Add new item**

Walks through a prompt-by-prompt form. Only `product_name` is required; all other fields can be left blank. After submission, the new item is displayed with its assigned ID.

**Option 4 — Update item**

Prompts for an item ID, shows the current values, then lets you overwrite price, stock, product name, or category. Leave any field blank to keep the existing value.

**Option 5 — Delete item**

Prompts for an item ID, shows what's about to be deleted, and asks you to type `yes` to confirm before removing it.

**Option 6 — Search OpenFoodFacts API**

Offers two sub-options:

- **Search by barcode** — enter a barcode, see the product card, then optionally import it into your local inventory
- **Search by name** — enter a product name, see a numbered list of up to 5 results, pick one, and optionally import it (you'll be prompted for price, stock, and category before import)

---

## Data persistence

All inventory data is stored in `inventory.json` at the project root. The file is created automatically if it doesn't exist, seeded with five products:

| ID | Product | Brand | Category |
|----|---------|-------|----------|
| 1 | Organic Almond Milk | Silk | Beverages |
| 2 | Cheerios | General Mills | Breakfast Cereals |
| 3 | Kraft Mac & Cheese | Kraft | Pasta & Grains |
| 4 | Lay's Classic Potato Chips | Lay's | Snacks |
| 5 | Oreo Cookies | Nabisco | Cookies & Biscuits |

Every write operation (create, update, delete) immediately reloads the file from disk, applies the change, and writes the entire file back. This is safe for single-user, single-process use but is not suitable for concurrent access.

> If you want to reset to the seeded defaults, just delete `inventory.json` and restart the server.

---

## Running tests

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

Shared fixtures are defined in `conftest.py` in the project root. `pytest-mock` is available for patching external calls (e.g. mocking the OpenFoodFacts HTTP requests in tests).

---

## Error handling

The API returns structured errors for all failure cases:

| Scenario | HTTP status | Example message |
|----------|-------------|-----------------|
| Missing or non-JSON request body | `400` | `"Request body must be valid JSON."` |
| Missing required field | `400` | `"'product_name' is required."` |
| Item not found by ID | `404` | `"Item with id '99' not found."` |
| Barcode not in OpenFoodFacts | `404` | `"No product found for barcode '000'."` |
| Name search returns no results | `404` | `"No products found matching 'xyz'."` |

The CLI surfaces these messages with a ✖ prefix and returns you to the menu without crashing.

If the server is unreachable, the CLI prints a connection error and exits cleanly:

```
  ✖  ERROR: Cannot reach the API server. Is 'python run.py' running?
```

---

## Known limitations & future improvements

**Current limitations**

- The JSON file is read and rewritten on every request — not suitable for high-traffic or concurrent use
- No authentication or authorisation — the API is open to anyone who can reach port 5000
- OpenFoodFacts search returns at most 5 results; there is no pagination in the CLI
- Nutrition data from OpenFoodFacts may be missing or incomplete for some products
- `run.py` uses Flask's built-in development server, which is not production-ready

**Possible improvements**

- Swap `inventory.json` for SQLite (via SQLAlchemy or Flask-SQLAlchemy) for proper concurrent access and query support
- Add API key authentication or JWT-based auth for multi-user environments
- Paginate the `/inventory` list endpoint and the name-search results
- Add filtering and sorting to `GET /inventory` (e.g. by category, stock level, price range)
- Dockerise the application so it runs consistently across environments
- Add more comprehensive test coverage, especially integration tests for the OpenFoodFacts client
- Replace the development server with gunicorn behind nginx for production deployment

---

## Contributing

Pull requests are welcome. For larger changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests where appropriate
4. Run the test suite: `pytest`
5. Commit with a clear message: `git commit -m "Add barcode validation on import"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a pull request against `main`

Please follow existing code style — clear docstrings, descriptive variable names, and comments for anything non-obvious.

---

## License

This project is open source. Add your preferred license here (e.g. MIT, Apache 2.0).