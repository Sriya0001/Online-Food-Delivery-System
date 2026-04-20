"""
database.py
===========
Database connection helper and schema initializer.

This module is the single source of truth for SQLite access.
All other modules call get_db() to obtain a connection and
init_db() is called once at app startup to create the tables.

Tables:
  - users       : Registered accounts with role-based access
  - menu_items  : Food items a customer can order
  - orders      : A customer's placed order (header)
  - order_items : Individual line items within an order
"""

import sqlite3
import os

# ── Database file location (sits alongside this module in backend/) ──────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'food_delivery.db')


def get_db():
    """
    Open and return a SQLite connection.

    sqlite3.Row is used as the row factory so columns can be accessed
    by name (e.g. row['email']) instead of by index.
    Foreign-key enforcement is switched on for every connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Create all tables if they don't already exist.
    Safe to call on every startup (CREATE TABLE IF NOT EXISTS).
    """
    conn = get_db()
    c = conn.cursor()

    # ── Users ────────────────────────────────────────────────────────────────
    # Roles:  customer | restaurant | delivery | admin
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,          -- SHA-256 hex digest
            role     TEXT    NOT NULL DEFAULT 'customer'
                     CHECK(role IN ('customer', 'restaurant', 'delivery', 'admin'))
        )
    """)

    # ── Menu Items ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            price       REAL    NOT NULL,
            category    TEXT    NOT NULL,
            available   INTEGER NOT NULL DEFAULT 1,  -- 1 = available, 0 = hidden
            is_veg      INTEGER NOT NULL DEFAULT 0,  -- 1 = vegetarian, 0 = non-vegetarian
            calories    INTEGER NOT NULL DEFAULT 0   -- kcal per serving
        )
    """)

    # ── Orders ───────────────────────────────────────────────────────────────
    # Status lifecycle:
    #   Placed → Accepted / Rejected
    #   Accepted → Preparing → Out for Delivery → Delivered
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id       INTEGER NOT NULL REFERENCES users(id),
            status            TEXT    NOT NULL DEFAULT 'Placed',
            total_price       REAL    NOT NULL,
            created_at        TEXT    NOT NULL,          -- ISO 8601 UTC timestamp
            delivery_agent_id INTEGER          REFERENCES users(id)  -- assigned later
        )
    """)

    # ── Order Items (line items) ─────────────────────────────────────────────
    # price column stores the menu price at the time of ordering (snapshot),
    # so historical orders remain accurate even if the menu price changes later.
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     INTEGER NOT NULL REFERENCES orders(id),
            menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
            quantity     INTEGER NOT NULL DEFAULT 1,
            price        REAL    NOT NULL   -- price snapshot
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Schema initialised successfully.")


def migrate_db():
    """
    Add new columns to existing databases without destroying data.
    Uses PRAGMA table_info to check before running ALTER TABLE,
    so it is completely safe to call on every app startup.
    """
    conn = get_db()
    c    = conn.cursor()

    # Fetch the names of all existing columns in menu_items
    existing_cols = [
        row[1] for row in c.execute("PRAGMA table_info(menu_items)").fetchall()
    ]

    # Add is_veg if not present
    if 'is_veg' not in existing_cols:
        c.execute("ALTER TABLE menu_items ADD COLUMN is_veg INTEGER NOT NULL DEFAULT 0")
        print("[DB] Migration: added column 'is_veg' to menu_items.")

    # Add calories if not present
    if 'calories' not in existing_cols:
        c.execute("ALTER TABLE menu_items ADD COLUMN calories INTEGER NOT NULL DEFAULT 0")
        print("[DB] Migration: added column 'calories' to menu_items.")

    conn.commit()
    conn.close()
