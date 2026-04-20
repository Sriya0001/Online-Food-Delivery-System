import pytest
import os
import sys
import sqlite3

# Insert project root into sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our backend application and database helpers
from backend.app import app
import database

# Define a path for a temporary testing database
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_delivery.db')

@pytest.fixture
def client():
    """
    Sets up a Pytest test client for the Flask app.
    Before returning the client, it patches the database path to use
    a clean test database and runs the initialize schema script.
    """
    # Configure Flask app for testing
    app.config['TESTING'] = True
    
    # 1. Patch database path to point to test_delivery.db
    original_db_path = database.DB_PATH
    database.DB_PATH = TEST_DB_PATH

    # 2. Cleanup old test DB if it exists (very unlikely, but safe)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # 3. Create fresh schema in the test database
    database.init_db()
    database.migrate_db()

    # 4. Provide the test client to the test case
    with app.test_client() as client:
        yield client

    # Cleanup after test runs
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass
    # Restore original path
    database.DB_PATH = original_db_path

@pytest.fixture
def db_conn():
    """
    Yields a direct raw sqlite3 connection to the test database.
    Useful for populating mock data directly without going
    through the API.
    """
    conn = database.get_db()
    yield conn
    conn.close()
