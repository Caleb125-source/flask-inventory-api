"""
run.py
------
Entry point – starts the Flask development server.

Usage:
    python run.py
"""

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)