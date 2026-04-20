"""
admin.py
========
Admin Blueprint — read-only system-wide visibility.

Admins can view all orders (with customer and agent names) and all
registered users. No passwords are ever returned.

Routes:
  GET /api/admin/orders   → all orders in the system
  GET /api/admin/users    → all registered users
"""

from flask import Blueprint, jsonify, session
from database import get_db

admin_bp = Blueprint('admin', __name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def _require_admin():
    """Return a 401/403 response if the caller is not an admin, else None."""
    if 'user_id' not in session:
        return jsonify({'error': 'Login required.'}), 401
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required.'}), 403
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/orders', methods=['GET'])
def all_orders():
    """
    Return every order in the system enriched with:
      - customer_name  (the person who placed the order)
      - agent_name     (the delivery agent, if assigned)
      - items          (line items with product name, quantity, price)

    Success (200): list of order objects
    """
    err = _require_admin()
    if err:
        return err

    db = get_db()
    try:
        orders = db.execute(
            """
            SELECT  o.*,
                    c.name  AS customer_name,
                    da.name AS agent_name
            FROM    orders o
            JOIN    users  c  ON o.customer_id       = c.id
            LEFT JOIN users da ON o.delivery_agent_id = da.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()

        result = []
        for order in orders:
            items = db.execute(
                """
                SELECT oi.quantity, oi.price, mi.name AS item_name
                FROM   order_items oi
                JOIN   menu_items  mi ON oi.menu_item_id = mi.id
                WHERE  oi.order_id = ?
                """,
                (order['id'],)
            ).fetchall()
            result.append({**dict(order), 'items': [dict(i) for i in items]})

        return jsonify(result)

    finally:
        db.close()


@admin_bp.route('/api/admin/users', methods=['GET'])
def all_users():
    """
    Return all registered users sorted by role then name.
    Passwords are intentionally excluded from the response.

    Success (200): list of { id, name, email, role }
    """
    err = _require_admin()
    if err:
        return err

    db = get_db()
    try:
        users = db.execute(
            "SELECT id, name, email, role FROM users ORDER BY role, name"
        ).fetchall()
        return jsonify([dict(u) for u in users])
    finally:
        db.close()
