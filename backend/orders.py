"""
orders.py
=========
Order management Blueprint.

Order status lifecycle:
    Customer places order → "Placed"
    Restaurant accepts   → "Accepted"
    Restaurant rejects   → "Rejected"
    Restaurant prepares  → "Preparing"
    Delivery picks up    → "Out for Delivery"
    Delivery delivers    → "Delivered"

Routes:
  POST /api/orders                  → place a new order          (customer)
  GET  /api/orders                  → get own orders             (customer)
  GET  /api/orders/all              → get ALL orders             (restaurant, admin)
  GET  /api/orders/pending          → get only 'Placed' orders   (restaurant)
  PUT  /api/orders/<id>/status      → change order status        (restaurant, delivery, admin)
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from database import get_db

orders_bp = Blueprint('orders', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_login():
    """Return (None) if logged in, or a (Response, status_code) tuple if not."""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required.'}), 401
    return None


def _build_order(db, order_row):
    """
    Enrich an order row with its line items and return as a plain dict.
    This is used by every endpoint that returns order data.
    """
    items = db.execute(
        """
        SELECT oi.quantity, oi.price, mi.name AS item_name
        FROM   order_items oi
        JOIN   menu_items  mi ON oi.menu_item_id = mi.id
        WHERE  oi.order_id = ?
        """,
        (order_row['id'],)
    ).fetchall()
    return {**dict(order_row), 'items': [dict(i) for i in items]}


# ── Customer Endpoints ────────────────────────────────────────────────────────

@orders_bp.route('/api/orders', methods=['POST'])
def place_order():
    """
    Place a new food order.

    Request JSON body:
        {
            "items": [
                { "menu_item_id": 1, "quantity": 2 },
                { "menu_item_id": 4, "quantity": 1 }
            ]
        }

    The total price is calculated server-side to prevent tampering.

    Success (201):
        { "message": str, "order_id": int, "total": float }
    """
    err = _require_login()
    if err:
        return err

    if session['role'] != 'customer':
        return jsonify({'error': 'Only customers can place orders.'}), 403

    data  = request.get_json() or {}
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'Your cart is empty — add at least one item.'}), 400

    db = get_db()
    try:
        total     = 0.0
        validated = []   # list of (menu_item_row, quantity)

        # Validate each item and compute the total price
        for entry in items:
            menu_item = db.execute(
                "SELECT * FROM menu_items WHERE id = ? AND available = 1",
                (entry['menu_item_id'],)
            ).fetchone()

            if not menu_item:
                return jsonify({
                    'error': f"Item ID {entry['menu_item_id']} is not available."
                }), 400

            qty    = max(1, int(entry.get('quantity', 1)))
            total += menu_item['price'] * qty
            validated.append((menu_item, qty))

        # Insert the order header row
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        cur = db.execute(
            "INSERT INTO orders (customer_id, status, total_price, created_at) VALUES (?, 'Placed', ?, ?)",
            (session['user_id'], round(total, 2), now)
        )
        order_id = cur.lastrowid

        # Insert each line item
        for menu_item, qty in validated:
            db.execute(
                "INSERT INTO order_items (order_id, menu_item_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, menu_item['id'], qty, menu_item['price'])
            )

        db.commit()
        return jsonify({
            'message':  'Your order has been placed successfully!',
            'order_id': order_id,
            'total':    round(total, 2),
        }), 201

    finally:
        db.close()


@orders_bp.route('/api/orders', methods=['GET'])
def get_my_orders():
    """Return all orders placed by the currently logged-in customer."""
    err = _require_login()
    if err:
        return err

    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (session['user_id'],)
        ).fetchall()
        return jsonify([_build_order(db, r) for r in rows])
    finally:
        db.close()


# ── Restaurant / Admin Endpoints ──────────────────────────────────────────────

@orders_bp.route('/api/orders/all', methods=['GET'])
def get_all_orders():
    """Return every order in the system. Accessible by restaurant and admin."""
    err = _require_login()
    if err:
        return err

    if session['role'] not in ('restaurant', 'admin'):
        return jsonify({'error': 'Access denied.'}), 403

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT  o.*,
                    c.name  AS customer_name,
                    da.name AS agent_name
            FROM    orders o
            JOIN    users c  ON o.customer_id       = c.id
            LEFT JOIN users da ON o.delivery_agent_id = da.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()
        return jsonify([_build_order(db, r) for r in rows])
    finally:
        db.close()


@orders_bp.route('/api/orders/pending', methods=['GET'])
def get_pending_orders():
    """Return orders with status='Placed' for the restaurant to action."""
    err = _require_login()
    if err:
        return err

    if session['role'] != 'restaurant':
        return jsonify({'error': 'Restaurant access required.'}), 403

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT  o.*, u.name AS customer_name
            FROM    orders o
            JOIN    users  u ON o.customer_id = u.id
            WHERE   o.status = 'Placed'
            ORDER BY o.created_at ASC
            """
        ).fetchall()
        return jsonify([_build_order(db, r) for r in rows])
    finally:
        db.close()


@orders_bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Update the status of a specific order.

    Role-based permissions:
        restaurant → can set: Accepted, Rejected, Preparing
        delivery   → can set: Out for Delivery, Delivered
        admin      → can set any status

    Request JSON body:
        { "status": "Accepted" }

    Success (200): { "message": str }
    """
    err = _require_login()
    if err:
        return err

    role       = session['role']
    data       = request.get_json() or {}
    new_status = data.get('status', '').strip()

    # Define which statuses each role is allowed to assign
    role_permissions = {
        'restaurant': ['Accepted', 'Rejected', 'Preparing'],
        'delivery':   ['Out for Delivery', 'Delivered'],
        'admin':      ['Placed', 'Accepted', 'Rejected', 'Preparing', 'Out for Delivery', 'Delivered'],
    }

    if role not in role_permissions:
        return jsonify({'error': 'Access denied.'}), 403

    if new_status not in role_permissions[role]:
        return jsonify({
            'error': f'"{new_status}" is not a valid transition for your role.'
        }), 400

    db = get_db()
    try:
        order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return jsonify({'error': f'Order #{order_id} not found.'}), 404

        # When a delivery agent picks up an order, assign them automatically
        if role == 'delivery' and new_status == 'Out for Delivery':
            db.execute(
                "UPDATE orders SET status = ?, delivery_agent_id = ? WHERE id = ?",
                (new_status, session['user_id'], order_id)
            )
        else:
            db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id)
            )

        db.commit()
        return jsonify({'message': f'Order #{order_id} is now "{new_status}".'})

    finally:
        db.close()
