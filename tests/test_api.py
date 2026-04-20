import pytest
import json

# ── Auth API Tests ────────────────────────────────────────────────────────────

def test_register_user(client):
    """Test user registration endpoint creates a new user."""
    response = client.post('/api/register', json={
        'name': 'Test User',
        'email': 'test@demo.com',
        'password': 'password123',
        'role': 'customer'
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data['message'] == 'Registration successful!'
    assert 'user_id' in data
    assert data['user_id'] is not None

def test_login_user(client):
    """Test user login returns a valid session via cookies."""
    # First register the user
    client.post('/api/register', json={
        'name': 'Test User',
        'email': 'testlogin@demo.com',
        'password': 'password123',
        'role': 'customer'
    })
    
    # Then attempt to log in
    response = client.post('/api/login', json={
        'email': 'testlogin@demo.com',
        'password': 'password123'
    })
    data = response.get_json()
    assert response.status_code == 200
    assert data['message'] == 'Welcome back, Test User!'
    assert data['user']['email'] == 'testlogin@demo.com'

    # Check that a session cookie was set
    assert 'session=' in response.headers.get('Set-Cookie', '')

# ── Menu API Tests ────────────────────────────────────────────────────────────

def test_fetch_empty_menu(client):
    """Test menu fetch returns 200 OK list even if DB is empty."""
    response = client.get('/api/menu')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_menu_is_veg_filter(client, db_conn):
    """Test that menu filtering via ?is_veg=1 properly returns only vegetarian items."""
    
    # Populate the testing database directly using the db_conn fixture
    db_conn.execute("INSERT INTO menu_items (name, price, category, is_veg) VALUES ('Salad', 10.0, 'Salads', 1)")
    db_conn.execute("INSERT INTO menu_items (name, price, category, is_veg) VALUES ('Chicken', 20.0, 'Mains', 0)")
    db_conn.commit()

    # Hit the API normally
    response = client.get('/api/menu?is_veg=1')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]['name'] == 'Salad'
    assert data[0]['is_veg'] == 1
