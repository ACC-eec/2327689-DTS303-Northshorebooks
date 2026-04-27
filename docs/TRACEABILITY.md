# Security Traceability Matrix

This document provides traceability from security requirements to implementation, showing how each requirement is addressed in code.

## Format

Requirement → Attack Prevented → Control → Code Reference → Manual Test

## Traceability Matrix

| Requirement | Attack | Control | Code Location | Test |
|-------------|--------|---------|---------------|------|
| SQL Injection Prevention | SQLi in search filter | Django ORM only | `catalogue/api.py:45-80` | Attempt SQLi in `?search=' OR '1'='1` parameter |
| SQL Injection Prevention | SQLi in author filter | Django ORM filter() | `catalogue/api.py:52-54` | Attempt SQLi in `?author='; DROP TABLE--` |
| XSS Prevention | Script injection in product title | Auto-escaping, no \|safe | `templates/catalogue/book_detail.html:12` | Inject `<script>alert('XSS')</script>` in product name (as admin) |
| XSS Prevention | Script injection in search query | Auto-escaping in template | `templates/catalogue/book_list.html` | Inject `<img src=x onerror=alert(1)>` in search query |
| CSRF Prevention | Unauthorized form submission | CSRF token + middleware | All templates with forms + `config/settings.py:45` | Remove `{% csrf_token %}`, submit form → 403 Forbidden |
| CSRF Prevention | API CSRF bypass | SessionAuthentication | `config/settings.py:300` | POST to API without session → 403 |
| Session Hijacking Prevention | Session cookie theft | Secure cookie flags | `config/settings.py:379-386` | Check cookie flags in browser DevTools |
| Session Hijacking Prevention | Session reuse after logout | Session flush | `accounts/views.py:396` | Login, copy cookie, logout, reuse cookie → Invalid |
| Session Hijacking Prevention | Session fixation | Session regeneration | `accounts/views.py:388` | Set session ID, login → New session ID generated |
| Authentication Bypass Prevention | Access protected views | @login_required | `orders/views.py:332,340,348,356,364,372` | Access `/orders/basket/` without login → Redirect to login |
| Authorization Prevention | Access others' orders | Ownership check | `orders/views.py:442` | User A tries to access User B's order → 404 |
| Admin Access Control | Non-admin POST to API | IsAdminUser permission | `catalogue/api.py:30-36` | Non-admin POST to `/api/books/` → 403 Forbidden |
| Password Theft Prevention | Brute force attack | Rate limiting | `accounts/views.py:464-467` | 6 failed login attempts → Lockout message |
| Password Theft Prevention | Password in logs | Never log passwords | `accounts/views.py` | Check logs for password strings → None found |
| Order Tampering Prevention | Client-side total modification | Server-side recalculation | `orders/views.py:490-494` | Modify cart total in browser, submit → Correct total stored |
| Order Tampering Prevention | Price change after add | Price snapshot | `orders/views.py:496-498` | Add book, change price in DB, submit → Original price used |
| Input Validation | Invalid quantity | Numeric validation | `orders/views.py:480-482` | Submit quantity = -1 or 1000 → Error message |
| Input Validation | SQLi in sort parameter | Allowlist | `catalogue/api.py:75-78` | Attempt `?ordering=DROP TABLE` → Ignored, default ordering used |

## Code References

### SQL Injection Prevention
- **catalogue/api.py:45-80**: `get_queryset()` method uses ORM `.filter()`, `.exclude()`, Q objects
- **orders/models.py**: All queries use ORM methods
- **orders/views.py**: `get_object_or_404()`, `get_or_create()` use ORM

### XSS Prevention
- **templates/base.html**: All variables use `{{ }}` which auto-escapes
- **templates/catalogue/book_detail.html:12**: `{{ book.title }}` auto-escaped
- **config/settings.py:421**: `SECURE_CONTENT_TYPE_NOSNIFF = True`

### CSRF Prevention
- **config/settings.py:45**: `CsrfViewMiddleware` in MIDDLEWARE
- **templates/registration/login.html**: `{% csrf_token %}`
- **templates/orders/basket.html**: `{% csrf_token %}` in all forms

### Session Security
- **config/settings.py:379-386**: Session cookie security settings
- **accounts/views.py:388**: `request.session.cycle_key()` on login

### Authentication/Authorization
- **orders/views.py:332**: `@login_required` decorator
- **orders/views.py:442**: Ownership check: `order.user == request.user or request.user.is_staff`
- **catalogue/api.py:30-36**: `get_permissions()` returns `IsAdminUser` for write operations

### Password Security
- **config/settings.py:459-462**: Password validators (min length 10)
- **accounts/views.py:464-467**: Rate limiting with cache

### Order Protection
- **orders/models.py:28-32**: `calculate_total()` method
- **orders/views.py:490-494**: Server-side recalculation in `submit_order`

### Input Validation
- **catalogue/api.py:75-78**: Allowlist for ordering
- **orders/views.py:480-482**: Quantity validation (1-99)

## Manual Test Procedures

See `docs/TESTING.md` for detailed manual security test procedures.
