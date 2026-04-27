# Security Documentation

## Threat Model Summary

This document outlines the security threats addressed in the Northshore Books application and the controls implemented to mitigate them.

### 1. SQL Injection

**Threat**: Attackers inject malicious SQL code through user input to manipulate database queries.

**Prevention**: 
- Django ORM exclusively used for all database queries
- No raw SQL queries (`raw()`, `cursor()`, string concatenation)
- All queries use parameterized ORM methods

**File Locations**:
- `catalogue/models.py` - Book model queries
- `catalogue/api.py` - API filtering (lines 45-80)
- `orders/models.py` - Order and OrderItem queries
- `orders/views.py` - All order operations use ORM
- `accounts/views.py` - User authentication uses Django's `authenticate()`

**Residual Risk**: None - ORM provides complete protection when used correctly.

---

### 2. Cross-Site Scripting (XSS)

**Threat**: Attackers inject malicious scripts into web pages viewed by other users.

**Prevention**:
- Django auto-escaping enabled by default
- Never use `|safe` filter on user-controlled content
- All templates use Django template tags which auto-escape

**File Locations**:
- `config/settings.py` - Auto-escaping enabled (default Django behavior)
- All templates in `templates/` - Use `{{ variable }}` which auto-escapes
- Security headers: `SECURE_CONTENT_TYPE_NOSNIFF = True` (config/settings.py:421)

**Residual Risk**: Low - Only if developers manually mark user input as safe.

---

### 3. Cross-Site Request Forgery (CSRF)

**Threat**: Attackers trick authenticated users into submitting malicious requests.

**Prevention**:
- `CsrfViewMiddleware` enabled in settings
- All POST forms include `{% csrf_token %}`
- CSRF cookie configured with secure flags

**File Locations**:
- `config/settings.py` - CsrfViewMiddleware in MIDDLEWARE (line 45)
- `config/settings.py` - CSRF cookie settings (lines 406-409)
- All templates with POST forms:
  - `templates/registration/login.html`
  - `templates/accounts/register.html`
  - `templates/catalogue/book_detail.html` (add to basket)
  - `templates/orders/basket.html` (update, remove, submit)

**Residual Risk**: None - Middleware provides complete protection.

---

### 4. Session Hijacking

**Threat**: Attackers steal or reuse user session cookies to impersonate users.

**Prevention**:
- Secure cookie flags: `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True` (with HTTPS)
- Session regeneration on login: `request.session.cycle_key()`
- Session timeout: `SESSION_COOKIE_AGE = 1800` (30 minutes)
- Session expires on browser close: `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`

**File Locations**:
- `config/settings.py` - Session security settings (lines 379-386)
- `accounts/views.py` - Session regeneration on login (line 388)

**Residual Risk**: Low - Mitigated by secure flags and regeneration. User-Agent binding optional (documented tradeoff).

---

### 5. Authentication Bypass

**Threat**: Unauthorized users gain access to protected resources.

**Prevention**:
- `@login_required` decorator on all order views
- User ownership checks: `order.user == request.user or request.user.is_staff`
- Admin-only API endpoints: `IsAdminUser` permission class

**File Locations**:
- `orders/views.py` - All views use `@login_required` (lines 332, 340, 348, 356, 364, 372)
- `orders/views.py` - Ownership check in `order_detail` (line 442)
- `catalogue/api.py` - Admin-only permissions (lines 30-36)

**Residual Risk**: None - Decorators and checks enforced server-side.

---

### 6. Password Theft

**Threat**: Attackers steal or crack user passwords.

**Prevention**:
- Django password hashing: `User.set_password()` uses `password_hash()`
- Password validators: Minimum length 10, common password check, numeric check
- Rate limiting: 5 attempts → 5 minute lockout (keyed by IP+username)
- Generic error messages: "Invalid credentials" for all failures

**File Locations**:
- `config/settings.py` - Password validators (lines 459-462)
- `accounts/views.py` - Rate limiting (lines 464-467)
- `accounts/views.py` - Generic error messages (line 468)

**Residual Risk**: Low - Strong hashing and rate limiting provide good protection.

---

### 7. Order Tampering

**Threat**: Attackers modify order totals or prices client-side.

**Prevention**:
- Server-side total recalculation: `Order.calculate_total()` from database prices
- Price snapshots: `OrderItem.unit_price` stored at time of order
- Transaction safety: `@transaction.atomic` on submit

**File Locations**:
- `orders/models.py` - `calculate_total()` method (lines 28-32)
- `orders/views.py` - Server-side recalculation in `submit_order` (lines 490-494)
- `orders/views.py` - Price snapshot on add/update (lines 496-498)

**Residual Risk**: None - All calculations server-side.

---

## Controls Implemented + File Locations

| Control | Implementation | File Location |
|---------|---------------|---------------|
| SQL Injection Prevention | Django ORM only | All models, views, serializers |
| XSS Prevention | Auto-escaping | All templates, config/settings.py |
| CSRF Protection | Middleware + tokens | config/settings.py, all form templates |
| Session Security | Secure cookies, regeneration | config/settings.py, accounts/views.py |
| Password Security | Hashing, rate limiting | config/settings.py, accounts/views.py |
| Authentication | @login_required | orders/views.py, accounts/views.py |
| Authorization | Ownership checks | orders/views.py, catalogue/api.py |
| Input Validation | Allowlists, numeric checks | catalogue/api.py, orders/views.py |
| Security Logging | JSON logs | config/security_logger.py |
| Order Protection | Server-side recalculation | orders/models.py, orders/views.py |

## Residual Risks + Mitigations

### Session Fixation
- **Risk**: Attacker sets session ID before user logs in
- **Mitigation**: Session regeneration on login (`accounts/views.py:388`)
- **Rationale**: Regenerating session ID prevents reuse of attacker-set sessions

### User-Agent Binding
- **Risk**: Legitimate users may change user-agent (mobile app, proxy)
- **Mitigation**: Optional feature, documented tradeoff
- **Rationale**: Balance security vs usability

### CSP Policy
- **Risk**: Minimal CSP may allow some XSS vectors
- **Mitigation**: Start minimal, tighten incrementally
- **Rationale**: Avoid breaking Django admin functionality

### Rate Limiting Bypass
- **Risk**: Distributed attacks from multiple IPs
- **Mitigation**: Keyed by IP+username, 5-minute lockout
- **Rationale**: Prevents most brute force while allowing legitimate retries
