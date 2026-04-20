"""
auth.py
=======
Authentication Blueprint — handles user registration, login, logout, and
the /api/me endpoint that returns the currently logged-in user.

Security approach (kept simple for academic use):
  - Passwords are stored as SHA-256 hex digests (never plain-text).
  - Authentication state is maintained with a server-side Flask session
    (a signed, HTTPOnly cookie).

Routes:
  POST /api/register  → create a new account
  POST /api/login     → authenticate and start a session
  POST /api/logout    → clear the session
  GET  /api/me        → return current session info
"""

import hashlib
from flask import Blueprint, request, jsonify, session
from database import get_db

# Register this file as a Flask Blueprint called 'auth'
auth_bp = Blueprint('auth', __name__)


# ── Helper ────────────────────────────────────────────────────────────────────

def hash_password(plaintext: str) -> str:
    """Return the SHA-256 hex digest of a plain-text password string."""
    return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user account.

    Request JSON body:
        {
            "name":     "Alice",
            "email":    "alice@example.com",
            "password": "secret123",
            "role":     "customer"   // customer | restaurant | delivery | admin
        }

    Success (201):   { "message": str, "user_id": int }
    Error   (400):   { "error": str }
    Error   (409):   { "error": str }  ← email already in use
    """
    data = request.get_json() or {}

    # Validate that all required fields are present and non-empty
    for field in ('name', 'email', 'password', 'role'):
        if not str(data.get(field, '')).strip():
            return jsonify({'error': f'Field "{field}" is required.'}), 400

    allowed_roles = ('customer', 'restaurant', 'delivery', 'admin')
    if data['role'] not in allowed_roles:
        return jsonify({'error': f'Role must be one of: {list(allowed_roles)}'}), 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (
                data['name'].strip(),
                data['email'].strip().lower(),
                hash_password(data['password']),
                data['role'],
            )
        )
        db.commit()
        return jsonify({'message': 'Registration successful!', 'user_id': cur.lastrowid}), 201

    except Exception as exc:
        # SQLite raises an IntegrityError with 'UNIQUE' when email is duplicate
        if 'UNIQUE' in str(exc).upper():
            return jsonify({'error': 'An account with this email already exists.'}), 409
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

    finally:
        db.close()


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """
    Log in a user.

    Request JSON body:
        { "email": "alice@example.com", "password": "secret123" }

    Success (200):
        {
            "message": str,
            "user": { "id": int, "name": str, "email": str, "role": str }
        }
    Error (401): { "error": str }
    """
    data     = request.get_json() or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, hash_password(password))
        ).fetchone()

        if user is None:
            return jsonify({'error': 'Invalid email or password.'}), 401

        # Store minimal info in the server-side session cookie
        session.clear()
        session['user_id'] = user['id']
        session['name']    = user['name']
        session['role']    = user['role']

        return jsonify({
            'message': f'Welcome back, {user["name"]}!',
            'user': {
                'id':    user['id'],
                'name':  user['name'],
                'email': user['email'],
                'role':  user['role'],
            }
        })

    finally:
        db.close()


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """Clear the session to log out the current user."""
    session.clear()
    return jsonify({'message': 'You have been logged out successfully.'})


@auth_bp.route('/api/me', methods=['GET'])
def me():
    """
    Return the currently authenticated user's info.
    Returns 401 if the user is not logged in.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated.'}), 401

    return jsonify({
        'id':   session['user_id'],
        'name': session['name'],
        'role': session['role'],
    })
