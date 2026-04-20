"""
sample_data.py
==============
Seeds the database with demo users and a full menu.

Run once before starting the server:
    python sample_data.py

Creates 4 demo users (one of each role) and 12 menu items.
All demo user passwords are: password123
"""

import sys
import os
import hashlib

# Allow importing from the backend/ folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from database import init_db, migrate_db, get_db


def hash_password(plaintext: str) -> str:
    """SHA-256 hash matching the backend auth.py implementation."""
    return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()


# ── Demo Users ────────────────────────────────────────────────────────────────
DEMO_USERS = [
    {
        'name':     'Customer',
        'email':    'customer@demo.com',
        'password': 'password123',
        'role':     'customer',
    },
    {
        'name':     'Restaurant',
        'email':    'restaurant@demo.com',
        'password': 'password123',
        'role':     'restaurant',
    },
    {
        'name':     'Delivery',
        'email':    'delivery@demo.com',
        'password': 'password123',
        'role':     'delivery',
    },
    {
        'name':     'Admin',
        'email':    'admin@demo.com',
        'password': 'password123',
        'role':     'admin',
    },
]

# ── Demo Menu Items ───────────────────────────────────────────────────────────
# is_veg : 1 = vegetarian (green dot), 0 = non-vegetarian (red dot)
# calories: approximate kcal per standard serving
DEMO_MENU = [
    # ── Burgers ──────────────────────────────────────────────────────────────
    {'name': 'Classic Aloo Tikki Burger',
     'description': 'Crispy spiced potato tikki with lettuce, tomato, cheese and our secret green chutney sauce.',
     'price': 189.00, 'category': 'Burgers', 'is_veg': 1, 'calories': 380},
    {'name': 'Chicken Crispy Burger',
     'description': 'Golden fried chicken fillet with coleslaw and smoky chipotle mayo.',
     'price': 159.00, 'category': 'Burgers', 'is_veg': 0, 'calories': 485},
    {'name': 'Veggie Delight Burger',
     'description': 'House-made lentil & spinach patty with avocado, sprouts and jalapeños.',
     'price': 139.00, 'category': 'Burgers', 'is_veg': 1, 'calories': 320},

    # ── Pizza ─────────────────────────────────────────────────────────────────
    {'name': 'Margherita Pizza',
     'description': 'Classic tomato base with fresh mozzarella, cherry tomatoes and fresh basil.',
     'price': 249.00, 'category': 'Pizza', 'is_veg': 1, 'calories': 266},
    {'name': 'BBQ Chicken Pizza',
     'description': 'Smoky BBQ base, grilled chicken strips, red onions and cheddar cheese.',
     'price': 299.00, 'category': 'Pizza', 'is_veg': 0, 'calories': 380},
    {'name': 'Paneer Tikka Pizza',
     'description': 'Tandoori-spiced paneer cubes with bell peppers and mint chutney base.',
     'price': 279.00, 'category': 'Pizza', 'is_veg': 1, 'calories': 340},

    # ── Rice & Biryani ────────────────────────────────────────────────────────
    {'name': 'Chicken Biryani',
     'description': 'Slow-cooked basmati rice with whole spices, tender chicken and caramelised onions.',
     'price': 219.00, 'category': 'Rice & Biryani', 'is_veg': 0, 'calories': 520},
    {'name': 'Veg Dum Biryani',
     'description': 'Layered basmati rice with seasonal vegetables, saffron and crispy fried onions.',
     'price': 179.00, 'category': 'Rice & Biryani', 'is_veg': 1, 'calories': 380},
    {'name': 'Mutton Biryani',
     'description': 'Rich slow-cooked mutton with aromatic whole spices, served with raita.',
     'price': 279.00, 'category': 'Rice & Biryani', 'is_veg': 0, 'calories': 580},

    # ── Drinks ────────────────────────────────────────────────────────────────
    {'name': 'Fresh Lime Soda',
     'description': 'Zingy freshly squeezed lime with sparkling water. Choose sweet or salted.',
     'price': 49.00, 'category': 'Drinks', 'is_veg': 1, 'calories': 45},
    {'name': 'Mango Lassi',
     'description': 'Thick and creamy blended Alphonso mango with chilled yogurt.',
     'price': 79.00, 'category': 'Drinks', 'is_veg': 1, 'calories': 180},
    {'name': 'Masala Chai',
     'description': 'Ginger-cardamom spiced Indian tea brewed with whole milk and jaggery.',
     'price': 39.00, 'category': 'Drinks', 'is_veg': 1, 'calories': 80},
]


def seed():
    """Seed demo users and refresh all menu items with the latest data."""
    init_db()     # Ensure tables exist
    migrate_db()  # Add any new columns (is_veg, calories) to existing DBs
    db = get_db()

    print("\nSeeding demo users...")
    for u in DEMO_USERS:
        try:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (u['name'], u['email'], hash_password(u['password']), u['role'])
            )
            print(f"  +  {u['role']:12s}  {u['email']}")
        except Exception:
            print(f"  -  {u['email']} already exists, skipped.")

    # ── Refresh ALL menu items ────────────────────────────────────────────────
    # We DELETE all existing menu items and re-insert so that new fields
    # (is_veg, calories) are always populated correctly, even on an existing DB.
    print("\nRefreshing menu items (delete + re-insert)...")
    # order_items → orders → menu_items have FK relationships.
    # We must delete child rows before the parent to satisfy constraints.
    db.execute("DELETE FROM order_items")
    db.execute("DELETE FROM orders")
    db.execute("DELETE FROM menu_items")

    for item in DEMO_MENU:
        db.execute(
            """INSERT INTO menu_items
                   (name, description, price, category, available, is_veg, calories)
               VALUES (?, ?, ?, ?, 1, ?, ?)""",
            (
                item['name'],
                item['description'],
                item['price'],
                item['category'],
                item['is_veg'],
                item['calories'],
            )
        )
        veg_label = "VEG" if item['is_veg'] else "non-veg"
        print(f"  +  [{item['category']:15s}]  {item['name']:<35s}  {item['calories']} kcal  ({veg_label})")

    db.commit()
    db.close()

    print("\n" + "=" * 54)
    print("  Database seeded successfully!")
    print("=" * 54)
    print("\n  Demo login credentials (all passwords: password123)")
    print("  -------------------------------------------------")
    for u in DEMO_USERS:
        print(f"  {u['role']:12s}  ->  {u['email']}")
    print()


if __name__ == '__main__':
    seed()
