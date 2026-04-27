# Security

A small bookshop's website now holds customer names, hashed passwords and order histories — the same kind of data that draws attackers to the larger retailers. This document collects every claim the prototype makes about its security posture into one place: the threats treated as in-scope, the controls implemented against each of them, the design choices that were not obvious, the manual tests a reviewer can replay by hand, the traceability matrix that ties each row of the rubric to a line of code, and the adversarial pen-test pass that named the gaps still on the backlog.

The structure mirrors the order a reviewer would actually want to read it in:

1. **Threat model** — what we treated as in-scope and what each control buys us.
2. **Design decisions** — the non-obvious choices and what they trade away.
3. **Traceability matrix** — every coursework requirement mapped to one file and one test.
4. **Manual test walk-throughs** — the controls verified by a human at a browser.
5. **Pen-test pass** — adversarial findings, fixes, and the "what I'd do next" list.

Each section points back to file and line, so a reviewer can verify the claim rather than take it on trust.

---

## 1. Threat Model

The model is deliberately narrow. We covered the OWASP Top Ten classics that map onto the coursework's security brief — injection, XSS, CSRF, broken authentication, broken access control — and one shop-specific concern, order tampering, that the generic frameworks do not catch on their own.

### 1.1 SQL Injection

**Threat.** An attacker shapes a form field, query string, or JSON body to smuggle SQL into a query the database then runs on their behalf — at worst, dumping or destroying the books, accounts and orders tables in one request.

**Prevention.** The application uses the Django ORM exclusively. There is no `raw()`, no cursor-level `execute`, and no string concatenation building a query anywhere in the codebase. All user-supplied filter values are bound through the database driver as parameters — `author__icontains=author`, `price__gte=min_price` — so the attack surface that injection requires simply does not exist here.

**Where in the code:**
- `catalogue/models.py` — `Book` model and its queries.
- `catalogue/api.py:50-88` — search and filter parameters bound via ORM.
- `orders/models.py` — every read and write goes through Django querysets.
- `orders/views.py` — basket and submit operations use ORM helpers.
- `accounts/views.py` — login routes through Django's own `authenticate()`.

**Residual risk.** None — provided the rule "ORM only, no raw SQL" is held in future development. A pre-commit grep for `RawSQL`, `cursor()`, and `.raw(` would make that rule mechanical rather than discretionary.

### 1.2 Cross-Site Scripting (XSS)

**Threat.** A script injected into a book title, a search box or a flash message executes in another customer's browser — the classic vehicle for cookie theft and silent account takeover.

**Prevention.** Django's template engine auto-escapes every variable by default, and a project-wide search confirmed the codebase contains no `|safe` filter, no `mark_safe` call, and no `{% autoescape off %}` block. The two side-channels that still permit XSS — content-type sniffing and clickjacking iframes — are closed by the `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` headers configured in settings.

**Where in the code:**
- All templates under `templates/` — every variable rendered as `{{ name }}` is auto-escaped.
- `config/settings.py:198` — `SECURE_CONTENT_TYPE_NOSNIFF = True` set explicitly.

**Residual risk.** Low — and confined to one specific failure mode: a future developer marking user-controlled HTML as safe. Not zero, but the cost of preventing it is a code-review check rather than a code change.

### 1.3 Cross-Site Request Forgery (CSRF)

**Threat.** A logged-in customer visits an attacker's page, which silently posts to `/orders/submit/` from inside their browser — placing an order, or worse, in their name.

**Prevention.** `CsrfViewMiddleware` sits in the middleware stack immediately after the session middleware, every POST template carries a `{% csrf_token %}` tag, and the cookie itself is marked `HttpOnly` and `SameSite=Lax`. The browser will neither leak the token to JavaScript on a different origin nor send the cookie alongside a cross-site POST.

**Where in the code:**
- `config/settings.py:52` — `CsrfViewMiddleware` registered.
- `config/settings.py:193-195` — CSRF cookie flags.
- `templates/registration/login.html`, `templates/accounts/register.html`, `templates/catalogue/book_detail.html`, `templates/orders/basket.html` — `{% csrf_token %}` on every state-changing form.

**Residual risk.** None for the HTML paths. The API path is a separate question — handled below in §1.5.

### 1.4 Session Hijacking

**Threat.** An attacker reuses a stolen session cookie to walk straight past the login screen — historically the cheapest way into a customer account.

**Prevention.** Three controls work together. The cookie is marked `HttpOnly` and (under HTTPS) `Secure`, so JavaScript on a malicious page cannot read it; `request.session.cycle_key()` runs on every successful login, so a session ID set before the login no longer means anything; and `SESSION_COOKIE_AGE = 1800` plus `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` together ensure that an unattended laptop in the staffroom is not a permanent open door.

**Where in the code:**
- `config/settings.py:184-190` — session cookie flags and timeout.
- `accounts/views.py:171,193` — `cycle_key()` on successful authentication (both the form-valid path and the lockout-bypass path).

**Residual risk.** Low. User-Agent binding was considered and rejected — the false-positive rate from legitimate browser updates and proxy hops outweighed the marginal hijacking protection it would have added on top of cookie flags and key cycling.

### 1.5 Authentication Bypass

**Threat.** An unauthenticated request slips past `@login_required`, or a logged-in customer reaches a page that should only be admin-visible — broken access control, in OWASP's vocabulary.

**Prevention.** Three layers. Every order view wears `@login_required`. Order-detail enforces ownership with `order.user == request.user or request.user.is_staff`, and crucially raises `Http404` rather than `403` for non-owners — leaking "you are not the owner" still leaks "this order exists." The API tier downgrades to `IsAdminUser` on writes via `BookViewSet.get_permissions()`, so the same endpoint that a member of the public can `GET` cannot be used by them to `POST` a book.

**Where in the code:**
- `orders/views.py:27,42,87,109,151,200,211` — `@login_required` on every basket/order view.
- `orders/views.py:218-220` — ownership check; 404 not 403 for non-owners.
- `catalogue/api.py:42-48` — `get_permissions()` returns `IsAdminUser` for `POST`/`PUT`/`PATCH`/`DELETE`.

**Residual risk.** None at the controller level — the decorators and the permission classes are enforced on the server, not the client.

### 1.6 Password Theft

**Threat.** An attacker either steals the password store wholesale (offline crack) or guesses passwords one at a time against the live login (online brute-force).

**Prevention.** Against the offline case, Django's default PBKDF2-SHA256 hasher — a NIST-approved algorithm — is paired with a ten-character minimum, a common-password blocklist, and a same-as-username check. Against the online case, `CustomLoginView` caches a per-(IP, username) counter that locks out after five wrong attempts within five minutes, returns a deliberately generic "Invalid credentials" message regardless of which half of the pair was wrong, and never logs the candidate password — so a leaked log file does not become a credential dump. The JWT path inherits its own anonymous throttle so the JSON door cannot be used to side-step the HTML lockout.

**Where in the code:**
- `config/settings.py:112-128` — password validators.
- `accounts/views.py:137-186` — layered (per-IP and per-(IP, username)) rate-limit and lockout in `CustomLoginView.post`.
- `accounts/views.py:217` — generic "Invalid credentials." error string.
- `accounts/views.py:240-248` — `ThrottledTokenObtainPairView` closes the JWT brute-force bypass.

**Residual risk.** Low for credential stuffing from a single attacker; higher under a distributed spray, since the lockout is keyed by IP. The honest mitigation is a per-account counter on top of the per-IP one, on the backlog.

### 1.7 Order Tampering

**Threat.** A customer manipulates the basket on the way to the till — editing the displayed total in the browser, replaying an old request to lock in a stale price, or sending a quantity the form would not normally allow.

**Prevention.** The total is never trusted. `Order.calculate_total()` recomputes from the order's items, `submit_order` recalculates each line's `unit_price` from the current `Book.price` before flipping the order's status, and the whole submission runs inside `@transaction.atomic` with `select_for_update` so a half-submitted order cannot exist and concurrent shoppers cannot oversell a title. The subtle point is that the price snapshot stored in `OrderItem.unit_price` is set on the server, from the database, at the moment of the action — not read back from a hidden field on the form.

**Where in the code:**
- `orders/models.py:43-48` — `calculate_total()`.
- `orders/views.py:174-189` — `submit_order` re-reads each book row with `select_for_update`, recalculates the price, and decrements stock atomically.
- `orders/views.py:185-186` — `unit_price` snapshot from the live database price.

**Residual risk.** None at submit. The prototype now tracks stock movement: `submit_order` decrements `Book.stock` inside `select_for_update`, and `add_to_basket` / `update_quantity` refuse to add or grow a basket beyond the live stock count. What remains for a second iteration is observability — a stock-movement audit log so under-counting can be traced to a specific submit event, rather than reconstructed from order history.

### 1.8 Controls at a Glance

| Control | Implementation | File location |
|---------|----------------|---------------|
| SQL injection prevention | Django ORM only | All models, views, serialisers |
| XSS prevention | Auto-escaping, no `\|safe` | All templates, `config/settings.py` |
| CSRF protection | Middleware + token | `config/settings.py`, all form templates |
| Session security | `HttpOnly`, `Secure`, key cycling | `config/settings.py`, `accounts/views.py` |
| Password security | PBKDF2 hashing + rate limit | `config/settings.py`, `accounts/views.py` |
| Authentication | `@login_required` | `orders/views.py`, `accounts/views.py` |
| Authorisation | Ownership + admin checks | `orders/views.py`, `catalogue/api.py` |
| Input validation | Allowlists, numeric checks | `catalogue/api.py`, `orders/views.py` |
| Security logging | Structured JSON | `config/security_logger.py` |
| Order integrity | Server-side recalculation | `orders/models.py`, `orders/views.py` |

---

## 2. Design Decisions

A record of the security choices that were not obvious — the ones where two reasonable defaults pulled against each other and the prototype had to pick one. Each entry names what was decided, what the alternatives were, and what we knowingly traded away. Nothing here is meant to be defended in the abstract, only on its merits for a small bookshop's first online prototype.

### 2.1 Session cookie `SameSite`

**Decision.** `SESSION_COOKIE_SAMESITE = 'Lax'`.

**Why.** A customer who follows a friend's tweet linking to `/books/12/` should arrive logged in if they were already logged in — that is a normal shop-floor expectation. `Lax` permits the cookie on top-level GETs while still withholding it from cross-site POSTs, which is where the CSRF risk actually lives.

**Alternatives.**
- `Strict`: more secure, but breaks the shared-link case. The first time a customer follows a link from outside and lands logged-out, they will distrust the rest of the experience.
- `None`: only legal alongside `Secure`, and even then surrenders the protection that makes `SameSite` worth setting.

**Trade.** Slightly weaker than `Strict` against a hypothetical CSRF chain that begins with a top-level GET — accepted in exchange for the social-traffic case that matters to a bookshop trying to grow online.

### 2.2 Session timeout

**Decision.** `SESSION_COOKIE_AGE = 1800` (thirty minutes), and `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`.

**Why.** Thirty minutes is long enough that a customer browsing on a slow connection does not get logged out mid-checkout, and short enough that a laptop left open in a café is not a permanent open door. Expiring on browser close adds a second guard for the shared-machine case.

**Alternatives.**
- Fifteen minutes: sound on paper, painful in practice — readers comparing two books often spend longer than that on a single page.
- Sixty minutes: the opposite trade; comfortable for the user, and a much larger window for a stolen cookie to be useful.
- Absolute timeout only, with no browser-close clause: lets sessions persist across reboots, which is exactly the failure mode we wanted to close.

**Trade.** A small usability cost on long browsing sessions in exchange for a meaningful cap on hijack windows.

### 2.3 Login rate-limit

**Decision.** Five wrong attempts within five minutes, keyed by `(IP, username)`, layered with a per-IP global counter at twenty wrong attempts.

**Why.** The combination prevents the textbook single-attacker brute force without locking legitimate customers out of their own account whenever someone else on the same network mistypes a password. The per-IP layer catches the horizontal sweep that a per-(IP, username) lock would never see.

**Alternatives.**
- IP only: one customer's mistakes lock out the whole café. A self-inflicted denial of service.
- Username only: trivially defeated by an attacker rotating IPs — and the attacker, by definition, has more IPs available than the legitimate user.
- Fifteen-minute lockout: deters more strongly, frustrates the wrong-password customer more visibly. Marginal security gain, real usability cost.
- One-minute lockout: a script can wait that out. Cosmetic.

**Trade.** A distributed spray (a botnet across many IPs sweeping many usernames) is not blocked. Honestly named in §5 below and queued as the next iteration's fix — a per-account counter on top of the per-(IP, username) one.

### 2.4 Content Security Policy

**Decision.** Start minimal — allow `'self'`, permit inline styles where Django admin requires them — and tighten once the admin path has been retested under a stricter policy.

**Why.** A strict CSP that breaks the admin panel breaks the shop's *operations*: the staff member adding a new book in the morning, the manager fielding a returns query in the afternoon. A working admin under a permissive CSP is more secure than a perfect CSP that the team has had to disable to ship.

**Alternatives.**
- Strict from day one with full nonce machinery: the right end state, the wrong starting point. The refactor cost up front exceeds the marginal benefit until the rest of the codebase is stable.
- No CSP at all: surrenders defence-in-depth against XSS for no compensating reason.

**Trade.** A small notional XSS surface remains while inline styles are permitted — accepted explicitly as the cost of an incremental migration. Nonce-based CSP is the named follow-up.

### 2.5 User-Agent binding

**Decision.** Not implemented. Documented as a deliberate omission rather than an oversight.

**Why.** Sessions are already cycled on login, the cookie is `HttpOnly`, and it is `Secure` under HTTPS. Layering a User-Agent comparison on top would catch a narrow class of attack — the cookie smuggled to a different browser — at the cost of logging out every customer whose Chrome ticked over to the next major version mid-session.

**Trade.** A thin, low-likelihood attack remains theoretically possible — accepted because the controls already in place address the realistic version of the same threat.

### 2.6 Password minimum length

**Decision.** Ten characters minimum.

**Why.** Eight, the Django default, is comfortably brute-forceable on a modern GPU once a hash leak is in the attacker's hands. Ten lifts the cost meaningfully without crossing into territory where customers reach for sticky notes.

**Trade.** A two-character lift over the framework default; combined with the common-password blocklist and the same-as-username check, the realistic attack surface is closer than the raw number suggests.

### 2.7 Generic login error message

**Decision.** Return "Invalid credentials" regardless of which half of the username/password pair was wrong.

**Why.** A specific message ("no such user", "wrong password for that user") is a username-enumeration oracle — it lets an attacker map valid usernames before they ever try to brute-force a password. Generic messages hide the boundary between "user exists" and "user does not exist", and that boundary is precisely what reconnaissance wants to find.

**Trade.** A small usability cost — the returning customer who cannot remember whether they registered at all has to use the password-reset flow rather than seeing it spelt out — in exchange for closing the enumeration channel. Security wins this one cleanly.

### 2.8 Order total recalculation

**Decision.** The total is always recalculated from the database at submit time. No figure sent from the browser is trusted.

**Why.** Anything submitted by the browser was, by definition, in reach of an attacker — whether through DevTools, a custom client, or an intercepting proxy. The total is the most obvious figure to tamper with, and the rule "never trust the client for money" is one of the few near-universal e-commerce maxims that genuinely earns the strong wording.

**Trade.** None worth the name. Recalculation is one query and a sum; a small fixed cost in exchange for closing the most obvious tamper vector in the basket.

### 2.9 Price snapshots on `OrderItem`

**Decision.** Store `unit_price` on each `OrderItem` at the moment the line is created or updated, not at submit.

**Why.** A customer who sees `£12.99` next to a book and adds it to their basket has, by ordinary retail convention, formed an expectation that the book will be charged at `£12.99`. Snapshotting per line preserves that expectation while still allowing the shop to change list prices freely.

**Trade.** A small storage cost (one decimal field per line item) for a clean reconciliation between what the customer agreed to and what the system charged.

### 2.10 Security-log format

**Decision.** Structured JSON, one event per line, written to `storage/logs/security.log`.

**Why.** A separate file means the monitoring pipeline can be tuned to security-relevant events without sifting through application chatter; JSON-per-line means a future log-aggregator can ingest the file with no parsing rules to write. Plain text would have looked simpler today and cost more tomorrow.

### 2.11 Email hashing in logs

**Decision.** Truncated SHA-256 (first sixteen hex characters) in place of the address itself.

**Why.** An incident investigator does not actually need the email to correlate events — they need a stable identifier that points to the same person across log entries. The hash provides that identifier without putting personal data into a file that, by the nature of logs, will end up in backups, archives and the screens of people who do not need to see customer addresses.

### 2.12 CSRF on the API

**Decision.** Session-authenticated API calls go through `CsrfViewMiddleware` exactly as the HTML paths do; token-authenticated calls (JWT) do not, by design — they do not carry the cookie that CSRF protects.

**Why.** The two authentication modes carry different threat models. A browser making a session-cookie request is exactly the case CSRF was invented for. A backend service holding a bearer token is not browsing — it cannot be tricked into sending the request, because no cross-origin page is in the loop.

---

## 3. Traceability Matrix

A bridge between the threat model in §1, the controls in the codebase, and the manual tests in §4. Every coursework requirement is followed through the same chain: the attack it is meant to prevent, the control that prevents it, the file and line where that control lives, and the test that demonstrates it.

| Requirement | Attack | Control | Code location | Test |
|-------------|--------|---------|---------------|------|
| SQL-injection prevention | Injection in the search filter | Django ORM only | `catalogue/api.py:50-88` | `?search=' OR '1'='1` returns valid JSON, no SQL error |
| SQL-injection prevention | Injection in the author filter | ORM `filter()` with bound parameter | `catalogue/api.py:56-58` | `?author='; DROP TABLE--` leaves the table intact |
| XSS prevention | Script tag in a book title | Auto-escape, no `\|safe` | `templates/catalogue/book_detail.html:29` | `<script>alert('XSS')</script>` renders as text |
| XSS prevention | Image-error payload in a search query | Auto-escape on reflection | `templates/catalogue/book_list.html:48` | `<img src=x onerror=alert(1)>` does not fire |
| CSRF prevention | Forged form submission | CSRF middleware + token | every form template + `config/settings.py:52` | Strip the token; submit; receive `403` |
| CSRF prevention | API CSRF on session paths | `SessionAuthentication` | `config/settings.py:215-216` | Cross-origin `POST` without token returns `403` |
| Session-hijacking prevention | Cookie theft | `HttpOnly`, `Secure`, `SameSite` | `config/settings.py:184-190` | DevTools › Cookies confirms the flags |
| Session-hijacking prevention | Cookie reuse after logout | Session flush on logout | `accounts/views.py:226` | Captured cookie no longer authenticates |
| Session-hijacking prevention | Session fixation | `cycle_key()` on login | `accounts/views.py:171,193` | A pre-set session ID is replaced after login |
| Authentication-bypass prevention | Anonymous access to a protected view | `@login_required` | `orders/views.py:27,42,87,109,151,200,211` | `/orders/basket/` redirects to login |
| Authorisation enforcement | Reading another customer's order | Ownership check returning `404` | `orders/views.py:218-220` | Customer B receives `404` for A's order |
| Admin-only writes | Non-admin `POST /api/books/` | `IsAdminUser` permission | `catalogue/api.py:42-48` | Regular customer's `POST` is `403` |
| Brute-force resistance | Repeated wrong passwords | Layered (per-IP + per-(IP, username)) lockout | `accounts/views.py:137-186` | The sixth attempt against one user is locked out; the twenty-first across any user trips the per-IP layer |
| Brute-force resistance (API) | Credential brute-force on JWT login | Anonymous-rate throttle on `/api/auth/token/` | `accounts/views.py:240-248` | Rapid wrong-password POSTs are answered with `429` |
| Credential hygiene | Passwords in logs | Never logged in plaintext | `accounts/views.py` | Grep the security log; no candidate password appears |
| Order-tampering prevention | Edited total in the browser | Server-side recalculation | `orders/views.py:174-189` | The submitted total matches the database, not the DOM |
| Order-tampering prevention | Price change after add-to-basket | `unit_price` snapshot | `orders/views.py:185-186` | The order is charged at the snapshotted price |
| Input validation | Invalid quantity | Bounded numeric check (1–99) | `orders/views.py:121-138` and `orders/models.py:92-97` | `-1` and `1000` are rejected |
| Input validation | Injection in the sort parameter | Allowlist of permitted fields | `catalogue/api.py:22-25,84-86` | `?ordering=DROP TABLE` falls back to the default |

---

## 4. Manual Test Walk-Throughs

Each test names the control, the steps a tester would actually run, and the response the application is expected to give back. The companion to this section is `tests_security.py` in each app, which automates the same walk-throughs as part of the test suite; the manual procedures here exist for the cases where a human at a browser is the more honest evidence.

### 4.1 SQL Injection

**Test 4.1.1 — payload in the search filter**
1. Open `/api/books/`.
2. Append `?search=' OR '1'='1`.
3. **Expected.** A normal JSON response — either the matching books or an empty list — and no SQL in the error log.
4. **Verify.** Browser console clean; `storage/logs/django.log` shows no `OperationalError`.

**Test 4.1.2 — `DROP TABLE` payload in the author filter**
1. Open `/api/books/?author='; DROP TABLE books--`.
2. **Expected.** The response is well-formed JSON, the books table still exists, and nothing in the database has changed.
3. **Verify.** A second `GET /api/books/` returns the catalogue intact.

**Test 4.1.3 — payload in a numeric filter**
1. Open `/api/books/?min_price=' OR 1=1--`.
2. **Expected.** The non-numeric value is silently ignored — the query falls back to the default.

### 4.2 Cross-Site Scripting

**Test 4.2.1 — script tag in a book title (admin path)**
1. Sign in as admin.
2. Create a book through `/admin/` with title `<script>alert('XSS')</script>`.
3. View the book's detail page.
4. **Expected.** The title renders as text — no alert fires.
5. **Verify.** The page source shows `&lt;script&gt;`, not `<script>`.

**Test 4.2.2 — image-error payload in a search query**
1. Open `/api/books/?search=<img src=x onerror=alert(1)>`.
2. **Expected.** No alert; the query string is rendered escaped wherever it is reflected.

**Test 4.2.3 — XSS payload riding through the basket**
1. As admin, create a book whose title carries an XSS payload.
2. As a regular customer, add it to the basket.
3. **Expected.** The title renders harmlessly. The payload survives the round-trip without becoming live HTML.

### 4.3 Cross-Site Request Forgery

**Test 4.3.1 — strip the CSRF token from a form**
1. Sign in as a customer.
2. Open DevTools on a book detail page.
3. Delete the `<input name="csrfmiddlewaretoken">` from the "Add to basket" form, or change its value.
4. Submit.
5. **Expected.** `403 Forbidden`.

**Test 4.3.2 — CSRF on a session-authenticated API call**
1. While signed in via the website, send a `POST` to `/api/books/` from a separate origin without the CSRF token.
2. **Expected.** `403 Forbidden` — the session authentication path enforces CSRF.

### 4.4 Sessions

**Test 4.4.1 — session ID rotates on login**
1. Note the `sessionid` cookie.
2. Sign out, then sign in again.
3. **Expected.** A new `sessionid` value — the old one was retired by `cycle_key()` on login.

**Test 4.4.2 — session is invalidated on logout**
1. Sign in. Copy the `sessionid` cookie value.
2. Sign out.
3. Reattach the captured cookie to a fresh request.
4. **Expected.** The request is treated as anonymous — protected pages redirect to login.

**Test 4.4.3 — session timeout**
1. Sign in. Leave the tab idle for thirty minutes.
2. Try to open a protected page.
3. **Expected.** Redirect to `/accounts/login/`.

### 4.5 Authentication

**Test 4.5.1 — protected view, unauthenticated**
1. Sign out (or use a private window).
2. Open `/orders/basket/`.
3. **Expected.** Redirect to `/accounts/login/?next=/orders/basket/`.

**Test 4.5.2 — order history, unauthenticated**
1. Sign out.
2. Open `/orders/history/`.
3. **Expected.** Redirect to login.

### 4.6 Authorisation

**Test 4.6.1 — one customer cannot see another's order**
1. Create two customers, A and B.
2. Sign in as A; submit an order; note the ID.
3. Sign out and sign in as B.
4. Open `/orders/<A's order id>/`.
5. **Expected.** `404 Not Found` — not 403. The 404 hides even the existence of the order from a probing customer.

**Test 4.6.2 — admin can view any order**
1. Sign in as a staff user.
2. Open the same `/orders/<id>/`.
3. **Expected.** The order detail renders.

**Test 4.6.3 — non-admin cannot write to the API**
1. Sign in as a regular customer.
2. `POST /api/books/` with a valid book payload.
3. **Expected.** `403 Forbidden`.

**Test 4.6.4 — admin can write to the API**
1. Sign in as a staff user.
2. `POST /api/books/` with the same payload.
3. **Expected.** `201 Created`; the book appears in `GET /api/books/`.

### 4.7 Password Security

**Test 4.7.1 — login rate-limit**
1. Sign out.
2. Submit five wrong passwords for the same username from the same client.
3. On the sixth attempt, submit the *correct* password.
4. **Expected.** "Too many login attempts. Please try again in 5 minutes."

**Test 4.7.2 — generic error message**
1. Sign out.
2. Submit a wrong username with any password, then a real username with a wrong password.
3. **Expected.** Both responses return the same "Invalid credentials" message — no hint as to which half failed.

**Test 4.7.3 — password length validator**
1. Open the registration form.
2. Submit with a password of fewer than ten characters.
3. **Expected.** "This password is too short. It must contain at least 10 characters."

### 4.8 Order Tampering

**Test 4.8.1 — edit the displayed total in the browser**
1. Sign in. Add items to the basket.
2. In DevTools, change the rendered total to `£0.01`.
3. Submit.
4. **Expected.** The order is created with the *server-recalculated* total — the displayed figure is ignored.

**Test 4.8.2 — price change between add-to-basket and submit**
1. Sign in. Add a book whose price is, say, £19.99.
2. As admin, change `Book.price` to £29.99.
3. Submit the original basket.
4. **Expected.** The line is charged at the price that was current *when the line was last touched*, not the new list price.

**Test 4.8.3 — negative quantity**
1. Sign in. Add an item.
2. Update its quantity to `-1`.
3. **Expected.** Form rejects the input; the existing line is unchanged.

**Test 4.8.4 — quantity over the cap**
1. Sign in. Add an item.
2. Update its quantity to `100`.
3. **Expected.** "Quantity cannot exceed 99."

### 4.9 Input Validation

**Test 4.9.1 — sort parameter outside the allowlist**
1. Open `/api/books/?ordering=DROP TABLE`.
2. **Expected.** The unknown ordering is dropped silently; the response uses the default order.

**Test 4.9.2 — non-numeric input on a numeric filter**
1. Open `/api/books/?min_price=abc`.
2. **Expected.** The filter is ignored; the response is the unfiltered (or otherwise-filtered) list.

**Test 4.9.3 — overlong search string**
1. Open `/api/books/?search=<a 250-character string>`.
2. **Expected.** The search is truncated to 200 characters before the query runs. No error.

### 4.10 Security Headers

**Test 4.10.1 — `X-Content-Type-Options`**
1. Open any page with DevTools › Network.
2. **Expected.** `X-Content-Type-Options: nosniff`.

**Test 4.10.2 — `X-Frame-Options`**
1. Same path.
2. **Expected.** `X-Frame-Options: DENY` — closes the clickjacking iframe vector.

**Test 4.10.3 — `Referrer-Policy`**
1. Same path.
2. **Expected.** `Referrer-Policy: strict-origin-when-cross-origin`.

### 4.11 Security Logging

**Test 4.11.1 — login success is logged**
1. Sign in successfully.
2. Tail `storage/logs/security.log`.
3. **Expected.** A JSON line with `event_type: "login_success"`, the client IP, the truncated email hash, and a timestamp.

**Test 4.11.2 — login failure is logged**
1. Submit a wrong password.
2. **Expected.** A JSON line with `event_type: "login_failure"`, the candidate username, and the IP — and crucially, no password.

**Test 4.11.3 — denied admin access is logged**
1. As a regular customer, send `POST /api/books/`.
2. **Expected.** A JSON line with `event_type: "admin_access_denied"`, the username, the path, and the IP.

### 4.12 Notes for the Tester

- Run every test against a development database. None of these tests are destructive *by design*, but the SQL-injection payloads are written to be honestly hostile — they belong nowhere near production data.
- A staff user is needed for the admin-side tests; the project's seed script creates one (`admin` / `NorthshoreAdmin1234!`).
- The security log lives at `storage/logs/security.log` in JSON-per-line format. `jq` makes it pleasant to skim; `cat` works in a pinch.

---

## 5. Pen-Test Pass

A pen-tester's-eye review focused on the HTTP entry points an unauthenticated attacker can reach with a browser and `curl`. While §4 demonstrates that the controls work, this section starts where the defensive tests stop and asks the harder question: what would an attacker actually try, and what does it find?

### 5.1 Reconnaissance — how the test plan was built

The defensive suites in `catalogue/tests_security.py` and `orders/tests_security.py` already cover the OWASP-classic risks the brief calls out. A productive pen-test starts where those tests stop. The recon walked `config/urls.py`, the three app `urls.py` files, and the DRF router in `catalogue/urls.py` to enumerate every path that accepts unauthenticated traffic, then traced two authentication front doors (HTML form and JWT JSON) hitting the **same** Django `User` table through `ModelBackend`. Five observations shaped the attack plan — each became one attack class in `accounts/tests_pentest.py`:

1. **Authentication topology.** One front door (the HTML form) has a per-(IP, username) lockout. The other (JWT) inherits only DRF defaults — and DRF had no throttle classes configured. Lock one door, walk through the other.
2. **Form leakage.** The registration form extends `UserCreationForm`, which surfaces `'A user with that username already exists.'` verbatim. No `clean_username` override, no rate limit on registration — a free username-enumeration oracle.
3. **Cache-key hygiene.** The login lockout key embedded the raw POSTed username, untruncated and unhashed — cache-bloat under a long-username spray.
4. **Per-username scope.** Because the lockout was keyed per-(IP, username) only, horizontal brute-force (`ada`, `bob`, `cara`, …) was unbounded.
5. **Shared-NAT failure mode.** A legitimate user on the same NAT could be **denied even with the correct password** for five minutes once an attacker had burnt the per-(IP, username) counter — a self-inflicted DoS.

### 5.2 Findings (initial pen-test pass, 2026-04-27)

| # | Severity | Finding | Proof in test |
|---|----------|---------|---------------|
| 1 | 🔴 HIGH   | JWT token endpoint had no throttle; brute-force bypassed the HTML lockout entirely. | `JWTBypassesLoginLockoutTests.test_jwt_endpoint_throttles_after_five_attempts` |
| 2 | 🟠 MEDIUM | Registration distinguished existing usernames and was unthrottled — a free user-enumeration oracle. | `UsernameEnumerationTests.*` |
| 3 | 🟠 MEDIUM | Login lockout was per-(IP, username) only — horizontal sweeps unbounded. | `HorizontalBruteForceTests.*` |
| 4 | 🟡 LOW    | A correct password was rejected for five minutes when an attacker on the same NAT had burnt the counter. | `LockoutDoesNotBlockValidCredsTests.*` |
| 5 | 🟡 LOW    | Lockout cache key embedded the raw, uncapped username — cache-bloat amplification. | (deduced from the key construction) |

Finding 1 is the headline. Even if every defensive suite passes, an unthrottled JWT endpoint makes the HTML lockout cosmetic. It was the first thing fixed.

### 5.3 Mitigations applied in this iteration

| Finding | Fix |
|---------|-----|
| 1 | Custom JWT view subclass with a strict DRF anonymous throttle (`5/min`) — `accounts/views.py:240-248`. |
| 2 | `clean_username` override returns a generic, non-leaky error; per-IP throttle on `register_view`. |
| 3 | Per-IP global counter added alongside the existing per-(IP, username) counter in `CustomLoginView`. |
| 4 | `post()` no longer short-circuits a valid `authenticate()` when the lockout is active; the lock applies only to *wrong-credential* paths. |
| 5 | The username segment of the lockout cache key is now hashed (sha256, hex-truncated). |

Re-running `accounts/tests_pentest.py` after the fixes converts every attack assertion into a "the protection holds" assertion; the suite is the regression net for the next pass.

### 5.4 What I'd do next — attacks not yet run

A second pen-test pass would broaden the surface in roughly this order. None of these are presumed exploitable; each is a candidate worth a probe before sign-off.

1. **DRF browsable docs / schema endpoints.** `/api/docs/` and `/api/schema/` are unauthenticated. Verify they don't leak admin-only fields, internal field names, or write endpoints.
2. **JWT refresh-token replay.** With `BLACKLIST_AFTER_ROTATION=False`, a stolen refresh token stays valid until natural expiry. Attempt to reuse a rotated refresh token.
3. **Session fixation across the JWT path.** The HTML login calls `session.cycle_key()`; the JWT login does not touch the session. Probe whether a fixed session cookie set before login persists after a JWT-based login.
4. **Open-redirect on `?next=`.** Confirm `url_has_allowed_host_and_scheme` rejects `//evil.example.com`, `\\evil`, and protocol-relative URLs.
5. **Mass-assignment via the API.** Confirm there is no user-modifying endpoint reachable without the admin.
6. **`logout` over GET.** Verify Django 5.x rejects GET logout with 405 in the deployed version.
7. **Reflected content in flash messages.** Auto-escaped on render, but worth a manual check that no template uses `|safe` on `messages`.
8. **Quantity overflow paths.** `int(request.POST.get('quantity'))` accepts negatives and very large ints before the explicit caps fire. Probe edge cases (`1e308`, `-0`, ints with leading whitespace).
9. **Static / media path traversal.** Review the dev-mode static handler for `..`-prefixed paths even though `DEBUG=False` in production turns it off.
10. **Login timing-channel.** With the lockout removed for valid credentials, measure response-time deltas between "user exists, wrong password" and "user does not exist".

### 5.5 What's *not* an issue, despite looking like one

- The `OrderIsolationTests` 404-vs-403 distinction is correct — leaking "this id exists" is a worse outcome than leaking "you are not the owner." Keep the 404.
- The `is_staff` privilege gate in `BookViewSet.get_permissions` correctly downgrades to `IsAdminUser` on writes. The pen-test didn't find a way around it.
- CSRF coverage is solid — the `enforce_csrf_checks=True` test client in `orders/tests_security.py` is the right pattern.

### 5.6 Production posture

None of the findings warrant treating the app as broken — the catalogue, ordering, and admin paths remain protected. Findings 1 and 2 do, however, warrant fixing **before** any deployment that exposes the JWT or registration endpoints to the public internet, because together they form a complete account-takeover chain (enumerate → brute-force) on a default install. Both are fixed in this iteration; the regression test suite holds them shut.
