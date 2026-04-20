"""
delivery.py
===========
Delivery Agent Blueprint.

Delivery agents can:
  1. Browse orders that have been accepted by the restaurant but not yet assigned.
  2. Pick up an order ("Out for Delivery") — this auto-assigns them to that order.
  3. Mark their assigned order as "Delivered".

Routes:
  GET /api/delivery/available        → unassigned accepted orders
  GET /api/delivery/assigned         → orders assigned to this agent
  PUT /api/delivery/<id>/status      → update delivery status
"""

from flask import Blueprint, request, jsonify, session
from database import get_db

delivery_bp = Blueprint('delivery', __name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def _require_delivery_agent():
    """
    Guard helper — returns a (Response, status) pair if the current user is
    not a logged-in delivery agent, otherwise returns None.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Login required.'}), 401
    if session.get('role') != 'delivery':
        return jsonify({'error': 'Delivery agent access required.'}), 403
    return None


def _build_order(db, row):
    """Attach line items to an order row dict."""
    items = db.execute(
        """
        SELECT oi.quantity, mi.name AS item_name
        FROM   order_items oi
        JOIN   menu_items  mi ON oi.menu_item_id = mi.id
        WHERE  oi.order_id = ?
        """,
        (row['id'],)
    ).fetchall()
    return {**dict(row), 'items': [dict(i) for i in items]}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@delivery_bp.route('/api/delivery/available', methods=['GET'])
def get_available():
    """
    Return all orders that:
      - Have status = 'Accepted'  (restaurant has confirmed them)
      - Have no delivery_agent_id  (not yet picked up by anyone)

    These are orders a delivery agent can volunteer to take.
    """
    err = _require_delivery_agent()
    if err:
        return err

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT  o.*, u.name AS customer_name
            FROM    orders o
            JOIN    users  u ON o.customer_id = u.id
            WHERE   o.status = 'Accepted'
              AND   o.delivery_agent_id IS NULL
            ORDER BY o.created_at ASC
            """
        ).fetchall()
        return jsonify([_build_order(db, r) for r in rows])
    finally:
        db.close()


@delivery_bp.route('/api/delivery/assigned', methods=['GET'])
def get_assigned():
    """
    Return all orders that have been assigned (or delivered by) this agent.
    Sorted newest first so the agent sees their most recent deliveries.
    """
    err = _require_delivery_agent()
    if err:
        return err

    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT  o.*, u.name AS customer_name
            FROM    orders o
            JOIN    users  u ON o.customer_id = u.id
            WHERE   o.delivery_agent_id = ?
            ORDER BY o.created_at DESC
            """,
            (session['user_id'],)
        ).fetchall()
        return jsonify([_build_order(db, r) for r in rows])
    finally:
        db.close()


@delivery_bp.route('/api/delivery/<int:order_id>/status', methods=['PUT'])
def update_delivery_status(order_id):
    """
    Update the delivery status of a specific order.

    Allowed statuses:
        'Out for Delivery' → agent picks up the order (and is auto-assigned)
        'Delivered'        → agent marks the order complete

    Request JSON body:
        { "status": "Out for Delivery" }

    Success (200): { "message": str }
    """
    err = _require_delivery_agent()
    if err:
        return err

    data       = request.get_json() or {}
    new_status = data.get('status', '').strip()
    allowed    = ['Out for Delivery', 'Delivered']

    if new_status not in allowed:
        return jsonify({'error': f'Status must be one of: {allowed}'}), 400

    db = get_db()
    try:
        order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return jsonify({'error': f'Order #{order_id} not found.'}), 404

        if new_status == 'Out for Delivery':
            # Assign this agent to the order when they pick it up
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
        return jsonify({'message': f'Order #{order_id} updated to "{new_status}".'})

    finally:
        db.close()
