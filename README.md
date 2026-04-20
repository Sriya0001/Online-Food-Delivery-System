# QuickBite — Online Food Delivery System

A beginner-friendly, full-stack web application built as a Software Engineering academic project.

## Tech Stack

| Layer    | Technology                         |
|----------|------------------------------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript    |
| Backend  | Python 3 + Flask                   |
| Database | SQLite (via Python's `sqlite3`)    |

---

## Folder Structure

```
Online-Food-Delivery-System/
├── backend/
│   ├── app.py          ← Flask entry point & route registration
│   ├── database.py     ← SQLite connection + schema creation
│   ├── auth.py         ← /api/register, /api/login, /api/logout, /api/me
│   ├── menu.py         ← /api/menu  (CRUD, admin-gated writes)
│   ├── orders.py       ← /api/orders  (place, view, update status)
│   ├── delivery.py     ← /api/delivery  (agent pickup + status updates)
│   ├── admin.py        ← /api/admin/orders, /api/admin/users
│   └── food_delivery.db  ← SQLite DB (auto-created on first run)
│
├── frontend/
│   ├── index.html              ← Login / Register landing page
│   ├── css/style.css           ← Shared design system
│   ├── js/api.js               ← Shared fetch helper + utilities
│   ├── customer/
│   │   ├── dashboard.html      ← Browse menu + add to cart + place order
│   │   └── orders.html         ← View order history + status tracker
│   ├── restaurant/
│   │   └── dashboard.html      ← Accept / Reject / Prepare orders
│   ├── delivery/
│   │   └── dashboard.html      ← Pick up and mark deliveries complete
│   └── admin/
│       └── dashboard.html      ← System-wide orders + users overview
│
├── sample_data.py      ← Seeds DB with 4 demo users + 12 menu items
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- `pip` package manager

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed the database with sample data

```bash
python sample_data.py
```

This creates 4 demo user accounts and 12 food menu items.

### 4. Start the server

```bash
python backend/app.py
```

### 5. Open the app

Navigate to **http://localhost:5000** in your browser.

---

## Demo Login Credentials

All demo accounts use the password: **`password123`**

| Role          | Email                   | What they can do                                   |
|---------------|-------------------------|----------------------------------------------------|
| Customer      | `customer@demo.com`     | Browse menu, add to cart, place orders, track status |
| Restaurant    | `restaurant@demo.com`   | Accept/reject orders, mark orders as preparing      |
| Delivery      | `delivery@demo.com`     | Pick up accepted orders, mark as delivered          |
| Admin         | `admin@demo.com`        | View all orders, all users, revenue stats           |

---

## API Reference

### Authentication

| Method | Endpoint        | Description                     |
|--------|-----------------|---------------------------------|
| POST   | `/api/register` | Create a new user account       |
| POST   | `/api/login`    | Log in (returns a session)      |
| POST   | `/api/logout`   | Log out (clears session)        |
| GET    | `/api/me`       | Get current logged-in user info |

**Register request body:**
```json
{ "name": "Alice", "email": "alice@example.com", "password": "secret", "role": "customer" }
```

**Login request body:**
```json
{ "email": "alice@example.com", "password": "secret" }
```

---

### Menu

| Method | Endpoint            | Auth         | Description                |
|--------|---------------------|--------------|----------------------------|
| GET    | `/api/menu`         | Public       | List all available items   |
| POST   | `/api/menu`         | Admin only   | Add a menu item            |
| PUT    | `/api/menu/<id>`    | Admin only   | Update a menu item         |
| DELETE | `/api/menu/<id>`    | Admin only   | Delete a menu item         |

**Optional query param:** `?category=Burgers`

---

### Orders

| Method | Endpoint                        | Auth              | Description                        |
|--------|---------------------------------|-------------------|------------------------------------|
| POST   | `/api/orders`                   | Customer          | Place a new order                  |
| GET    | `/api/orders`                   | Customer          | Get own orders                     |
| GET    | `/api/orders/all`               | Restaurant, Admin | Get all orders                     |
| GET    | `/api/orders/pending`           | Restaurant        | Get all orders with status Placed  |
| PUT    | `/api/orders/<id>/status`       | Restaurant/Delivery/Admin | Update order status       |

**Place order body:**
```json
{ "items": [{ "menu_item_id": 1, "quantity": 2 }, { "menu_item_id": 5, "quantity": 1 }] }
```

**Status update body:**
```json
{ "status": "Accepted" }
```

**Status flow by role:**
- Restaurant: `Placed → Accepted` or `Placed → Rejected`, then `Accepted → Preparing`
- Delivery: `Accepted → Out for Delivery → Delivered`

---

### Delivery

| Method | Endpoint                         | Auth     | Description                              |
|--------|----------------------------------|----------|------------------------------------------|
| GET    | `/api/delivery/available`        | Delivery | Orders accepted but no agent assigned    |
| GET    | `/api/delivery/assigned`         | Delivery | Orders assigned to this agent            |
| PUT    | `/api/delivery/<id>/status`      | Delivery | Update: "Out for Delivery" or "Delivered"|

---

### Admin

| Method | Endpoint             | Auth  | Description                         |
|--------|----------------------|-------|-------------------------------------|
| GET    | `/api/admin/orders`  | Admin | All orders with full details        |
| GET    | `/api/admin/users`   | Admin | All users (passwords excluded)      |

---

## Order Status Lifecycle

```
Customer places order
        │
        ▼
    [ Placed ]
        │
    Restaurant
   ┌────┴────┐
   ▼         ▼
[Accepted] [Rejected]
   │
   ▼
[Preparing]
   │
Delivery Agent picks up
   │
   ▼
[Out for Delivery]
   │
   ▼
[Delivered]
```

---

## SE Design Notes

- **Modular structure**: each concern (auth, menu, orders, delivery, admin) is a separate Flask Blueprint
- **Passwords**: stored as SHA-256 hex digests — never plain-text
- **Price integrity**: totals are calculated server-side to prevent client tampering
- **Single-origin deployment**: Flask serves both API and frontend — no CORS configuration needed
- **Database**: SQLite with `PRAGMA foreign_keys = ON` — referential integrity enforced
- **Session**: server-side Flask sessions (signed cookie) — stateless clients