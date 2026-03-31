"""
__init__.py
-----------
Flask application factory for the Inventory Management API.
"""

from flask import Flask


def create_app(testing: bool = False) -> Flask:
    """
    Create and configure the Flask application.

    Parameters
    ----------
    testing : bool
        When True the app runs with TESTING=True (useful in unit tests).
    """
    app = Flask(__name__)
    app.config["TESTING"] = testing

    # Register blueprints
    from app.routes import inventory_bp
    app.register_blueprint(inventory_bp)

    @app.route("/")
    def index():
        return {
            "message": "Inventory Management API",
            "version": "1.0.0",
            "endpoints": {
                "list_inventory":   "GET  /inventory",
                "get_item":         "GET  /inventory/<id>",
                "create_item":      "POST /inventory",
                "update_item":      "PATCH /inventory/<id>",
                "delete_item":      "DELETE /inventory/<id>",
                "search_barcode":   "GET  /inventory/search/barcode/<barcode>",
                "search_name":      "GET  /inventory/search/name/<name>",
                "import_from_api":  "POST /inventory/import/<barcode>",
            },
        }

    return app