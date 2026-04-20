"""
menu.py
=======
Menu Blueprint — exposes food menu items to customers and
provides admin-only endpoints to manage the menu catalogue.

Routes:
  GET    /api/menu           → list all available items  (public)
  POST   /api/menu           → add a new item            (admin only)
  PUT    /api/menu/<id>      → update an existing item   (admin only)
  DELETE /api/menu/<id>      → remove an item            (admin only)
"""

from functools import wraps
from flask import Blueprint, request, jsonify, session
from database import get_db

menu_bp = Blueprint('menu', __name__)


# ── Auth Decorator ────────────────────────────────────────────────────────────

def admin_required(fn):
    """
    Route decorator that blocks non-admin users.
    Must be applied AFTER @menu_bp.route(...).
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required.'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required.'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Public Endpoints ──────────────────────────────────────────────────────────

@menu_bp.route('/api/menu', methods=['GET'])
def get_menu():
    """
    Return all available menu items, sorted by category then name.

    Optional query params:
        ?category=Burgers   → filter to a single category
        ?is_veg=1           → show only vegetarian items

    Success (200): list of menu item objects
    """
    category = request.args.get('category')
    is_veg   = request.args.get('is_veg')   # '1' for veg-only, None for all
    db = get_db()
    try:
        conditions = ["available = 1"]
        params     = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if is_veg == '1':
            conditions.append("is_veg = 1")

        where_clause = " AND ".join(conditions)
        rows = db.execute(
            f"SELECT * FROM menu_items WHERE {where_clause} ORDER BY category, name",
            params
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        db.close()


# ── Admin Endpoints ───────────────────────────────────────────────────────────

@menu_bp.route('/api/menu', methods=['POST'])
@admin_required
def add_menu_item():
    """
    Add a new menu item to the catalogue. Admin only.

    Request JSON body:
        {
            "name":        "Margherita Pizza",
            "description": "Classic tomato and mozzarella",
            "price":       12.99,
            "category":    "Pizza",
            "is_veg":      1,
            "calories":    266
        }

    Success (201): { "message": str, "id": int }
    """
    data = request.get_json() or {}

    for field in ('name', 'price', 'category'):
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required.'}), 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO menu_items (name, description, price, category, available, is_veg, calories) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (
                data['name'],
                data.get('description', ''),
                float(data['price']),
                data['category'],
                int(data.get('is_veg', 0)),
                int(data.get('calories', 0)),
            )
        )
        db.commit()
        return jsonify({'message': 'Menu item added successfully.', 'id': cur.lastrowid}), 201
    finally:
        db.close()


@menu_bp.route('/api/menu/<int:item_id>', methods=['PUT'])
@admin_required
def update_menu_item(item_id):
    """
    Update an existing menu item. Admin only.
    Accepts any subset of: name, description, price, category, available, is_veg, calories.
    """
    data = request.get_json() or {}
    db = get_db()
    try:
        # Fetch current values so unspecified fields are preserved
        existing = db.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        if not existing:
            return jsonify({'error': 'Menu item not found.'}), 404

        db.execute(
            "UPDATE menu_items SET name=?, description=?, price=?, category=?, available=?, is_veg=?, calories=? WHERE id=?",
            (
                data.get('name',        existing['name']),
                data.get('description', existing['description']),
                float(data.get('price', existing['price'])),
                data.get('category',    existing['category']),
                int(data.get('available', existing['available'])),
                int(data.get('is_veg',  existing['is_veg'])),
                int(data.get('calories', existing['calories'])),
                item_id,
            )
        )
        db.commit()
        return jsonify({'message': 'Menu item updated successfully.'})
    finally:
        db.close()


@menu_bp.route('/api/menu/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_menu_item(item_id):
    """Remove a menu item from the catalogue. Admin only."""
    db = get_db()
    try:
        db.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        db.commit()
        return jsonify({'message': 'Menu item deleted.'})
    finally:
        db.close()
