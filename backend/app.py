"""
app.py
======
Flask application entry point for the Online Food Delivery System.

How to run:
    cd <project-root>
    python backend/app.py

The server starts at: http://localhost:5000

This file:
  1. Creates the Flask app and sets the session secret key.
  2. Registers all route Blueprints.
  3. Sets up URL rules to serve the frontend HTML / CSS / JS files.
  4. Calls init_db() on startup to create tables if they don't exist.
"""

import os
import sys

# ── Allow Python to find the sibling modules (database, auth, etc.) ──────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory

# Import the DB initialiser and all route blueprints
from database import init_db, migrate_db
from auth     import auth_bp
from menu     import menu_bp
from orders   import orders_bp
from delivery import delivery_bp
from admin    import admin_bp

# ── Path resolution ───────────────────────────────────────────────────────────
BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))   # …/backend/
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)                 # …/Online-Food-Delivery-System/
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')       # …/frontend/

# ── Create Flask App ──────────────────────────────────────────────────────────
app = Flask(__name__)

# Secret key used to sign the session cookie.
# ⚠️  Change this to a long random string before any real deployment!
app.secret_key = 'ofds_super_secret_key_change_in_production_2024'

# ── Register API Blueprints ───────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(delivery_bp)
app.register_blueprint(admin_bp)

# ── Frontend Static File Serving ─────────────────────────────────────────────
# Each route below maps a URL path to the corresponding folder in frontend/.
# The HTML pages use relative "../css/style.css" etc. which resolves correctly.

@app.route('/')
def index():
    """Serve the main login / register landing page."""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/css/<path:filename>')
def css(filename):
    """Serve CSS files from frontend/css/."""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def js(filename):
    """Serve JavaScript files from frontend/js/."""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)

@app.route('/customer/<path:filename>')
def customer(filename):
    """Serve customer dashboard pages."""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'customer'), filename)

@app.route('/restaurant/<path:filename>')
def restaurant(filename):
    """Serve restaurant dashboard pages."""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'restaurant'), filename)

@app.route('/delivery/<path:filename>')
def delivery(filename):
    """Serve delivery agent dashboard pages."""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'delivery'), filename)

@app.route('/admin/<path:filename>')
def admin_page(filename):
    """Serve admin dashboard pages. (Does NOT conflict with /api/admin/ routes.)"""
    return send_from_directory(os.path.join(FRONTEND_DIR, 'admin'), filename)

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()      # Create all tables on first run (safe to call every time)
    migrate_db()   # Add any new columns to existing databases (safe to repeat)
    print()
    print("=" * 54)
    print("   Online Food Delivery System")
    print("=" * 54)
    print("   URL  : http://localhost:5000")
    print("   Mode : Development (debug=True)")
    print("=" * 54)
    print()
    app.run(debug=True, port=5000)
