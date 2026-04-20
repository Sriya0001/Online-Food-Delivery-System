/**
 * api.js
 * ======
 * Shared JavaScript utilities used by EVERY frontend page.
 *
 * Provides:
 *   apiFetch(endpoint, method, body) → generic JSON fetch wrapper
 *   getCurrentUser()                 → reads the current session (/api/me)
 *   requireAuth(expectedRole)        → redirect to login if not authenticated
 *   showToast(message, type)         → display a temporary notification
 *   logout()                         → POST /api/logout then redirect home
 *   getStatusBadgeClass(status)      → returns the CSS class for a status badge
 *   formatDate(isoString)            → human-friendly date string
 *   formatCurrency(amount)           → "₹ 12.50" formatted string
 */

const API_BASE = ''; // Same origin as Flask at http://localhost:5000

// ── API Fetch Helper ──────────────────────────────────────────────────────────

/**
 * Makes a JSON fetch request to the Flask API.
 *
 * @param {string}  endpoint  - URL path, e.g. '/api/login'
 * @param {string}  method    - HTTP verb: 'GET', 'POST', 'PUT', 'DELETE'
 * @param {object}  body      - Request payload (will be JSON-stringified)
 * @returns {Promise<object>}   Parsed JSON response from the server
 * @throws  {Error}             Thrown if the response status is not 2xx
 */
async function apiFetch(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',   // Include the session cookie
    };
    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(API_BASE + endpoint, options);
    const data     = await response.json();

    if (!response.ok) {
        // Throw an error with the server's error message (shown in the UI)
        throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
}

// ── Session Helpers ───────────────────────────────────────────────────────────

/**
 * Return the currently logged-in user object, or null if not logged in.
 * Calls GET /api/me and returns { id, name, role }.
 */
async function getCurrentUser() {
    try {
        return await apiFetch('/api/me');
    } catch {
        return null;
    }
}

/**
 * Guard function — call at the top of every protected page's script.
 *
 * If the user is not logged in → redirect to /
 * If expectedRole is provided and does not match → redirect to /
 *
 * @param {string|null} expectedRole  - 'customer' | 'restaurant' | 'delivery' | 'admin' | null
 * @returns {Promise<object|null>}      The user object, or null (after redirect)
 */
async function requireAuth(expectedRole = null) {
    const user = await getCurrentUser();

    if (!user) {
        window.location.href = '/';
        return null;
    }

    if (expectedRole && user.role !== expectedRole) {
        window.location.href = '/';
        return null;
    }

    return user;
}

/**
 * Redirect the logged-in user to their role-appropriate dashboard.
 * @param {string} role
 */
function redirectToDashboard(role) {
    const routes = {
        customer:   '/customer/dashboard.html',
        restaurant: '/restaurant/dashboard.html',
        delivery:   '/delivery/dashboard.html',
        admin:      '/admin/dashboard.html',
    };
    window.location.href = routes[role] || '/';
}

// ── Logout ────────────────────────────────────────────────────────────────────

/**
 * Log out the current user: POST /api/logout then redirect to the login page.
 */
async function logout() {
    try {
        await apiFetch('/api/logout', 'POST');
    } catch { /* ignore */ }
    window.location.href = '/';
}

// ── UI Helpers ────────────────────────────────────────────────────────────────

/**
 * Show a temporary pop-up notification at the bottom-right of the screen.
 *
 * @param {string} message  - Text to display
 * @param {string} type     - 'success' | 'error' | 'warning' | 'info'
 */
function showToast(message, type = 'success') {
    // Remove any existing toast
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger the show animation on the next frame
    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('show'));
    });

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 350);
    }, 3000);
}

/**
 * Populate the navbar user pill with the logged-in user's info.
 * Expects an element with id="user-name" and id="role-badge" in the page.
 *
 * @param {object} user  - { name, role }
 */
function populateNavbar(user) {
    const nameEl = document.getElementById('user-name');
    const roleEl = document.getElementById('role-badge');
    const avatarEl = document.getElementById('user-avatar');

    if (nameEl)   nameEl.textContent  = user.name;
    if (roleEl)   roleEl.textContent  = user.role;
    if (avatarEl) avatarEl.textContent = user.name.charAt(0).toUpperCase();
}

// ── Formatting Helpers ────────────────────────────────────────────────────────

/**
 * Return the CSS badge class for a given order status.
 * Spaces are stripped so "Out for Delivery" → "badge-outfordelivery".
 *
 * @param {string} status
 * @returns {string}  e.g. 'badge-placed'
 */
function getStatusBadgeClass(status) {
    return 'badge badge-' + status.toLowerCase().replace(/\s+/g, '');
}

/**
 * Format an ISO 8601 UTC date string into a readable local date/time.
 * @param {string} iso  - e.g. "2024-04-20 09:15:00"
 * @returns {string}      e.g. "20 Apr 2024, 2:45 PM"
 */
function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso.replace(' ', 'T') + 'Z');
    return d.toLocaleString('en-IN', {
        day:    '2-digit',
        month:  'short',
        year:   'numeric',
        hour:   'numeric',
        minute: '2-digit',
    });
}

/**
 * Format a numeric price as Indian Rupee currency.
 * @param {number} amount
 * @returns {string}  e.g. "₹ 245.00"
 */
function formatCurrency(amount) {
    return '₹ ' + Number(amount).toFixed(2);
}

/**
 * Build an HTML string for the order items list.
 * @param {Array} items  - [{ item_name, quantity, price }, ...]
 * @returns {string}       HTML string
 */
function renderItemsList(items) {
    if (!items || items.length === 0) return '<li class="text-muted">No items</li>';
    return items.map(i =>
        `<li>
            <span>${i.item_name} × ${i.quantity}</span>
            <span>${formatCurrency(i.price * i.quantity)}</span>
        </li>`
    ).join('');
}
