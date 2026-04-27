# Documentation

A working reference for the Northshore Books prototype — the architectural shape of the codebase, the visual language the templates were built against, and the conventions a future contributor would want to know before opening a file. Two companion documents sit alongside this one: `SECURITY.md` covers the threat model, the controls, and the pen-test pass; `API.md` covers the REST and JWT surface in detail.

A note on style: this is a reference document, scanned in pieces rather than read end to end, so much of the content is structured lists. Flowing prose is reserved for the report; here, lists earn their place.

---

## 1. Architecture

The project is a Django 5.0 application split into three domain apps plus a project-wide configuration package. The split mirrors the way the bookshop already organises itself, so a member of staff phoning to say "the basket is broken" maps unambiguously to one folder.

### 1.1 The four packages

- **`config/`** — project-wide settings, URL routing, security logging.
- **`catalogue/`** — books and the public REST API.
- **`accounts/`** — registration, login, and the layered rate-limit and JWT throttle.
- **`orders/`** — basket, order submission, history, and the admin order view.

### 1.2 Why split it this way

The customer journey naturally separates into three concerns: *what the shop sells*, *who the customer is*, and *what they bought*. Each of those becomes one Django app. A fourth concern — *how the project is wired together* — does not belong inside any of them and lives in `config/`.

The separation matters less to the customer at the till and more to the next developer at the keyboard. When stock-handling moves from "track it on the basket" to "track it as a model field with migrations," only `catalogue/` and `orders/` are touched; `accounts/` and the security logger keep working without a change.

### 1.3 What sits where

- **Models.** `catalogue/models.py` carries `Book` (with `stock`); `orders/models.py` carries `Order` and `OrderItem`. There is no custom user model — the project leans on Django's built-in `User` and extends only the registration form.
- **Views.** Customer-facing HTML lives in `catalogue/views.py` (browse) and `orders/views.py` (basket and history). The admin site is customised lightly in each app's `admin.py` — list filters, inline order items, a coloured stock badge for the change list.
- **API.** `catalogue/api.py` exposes the catalogue as a DRF `ModelViewSet`; `catalogue/serializers.py` defines the JSON shape. JWT authentication endpoints are mounted in `config/urls.py` from `rest_framework_simplejwt` and a throttle-wrapped subclass in `accounts/views.py`.
- **Tests.** Each app carries two test modules: `tests.py` for the happy path, `tests_security.py` for the negative path. Adversarial coverage of the auth layer specifically lives in `accounts/tests_pentest.py`.

### 1.4 Settings

`config/settings.py` is structured in roughly the order Django itself reads it — core constants, the app and middleware registries, templating, database, password validators, static and media files, then the security headers and DRF configuration. The security block at the foot of the file is the one most often consulted during review; every value there has a matching entry in `SECURITY.md`.

The project supports both MySQL (default for production / coursework submission) and SQLite (for local development) via `USE_SQLITE=True` in `.env`.

---

## 2. Project Structure

```
northshore/
├── manage.py
├── config/
│   ├── settings.py            # all settings, in Django-read order
│   ├── urls.py                # routing, including JWT and Spectacular
│   └── security_logger.py     # JSON-per-line audit trail helpers
├── catalogue/
│   ├── models.py              # Book (with stock)
│   ├── views.py               # public HTML browse
│   ├── api.py                 # DRF ModelViewSet
│   ├── serializers.py
│   ├── admin.py               # stock badge, list filters
│   ├── tests.py               # happy-path API tests
│   ├── tests_security.py      # injection / XSS / IDOR
│   └── management/commands/
│       └── seed_from_openlibrary.py
├── accounts/
│   ├── forms.py               # UserRegistrationForm + clean_username
│   ├── views.py               # CustomLoginView (layered lockout) + JWT throttle
│   ├── tests.py               # happy-path + security log formatter
│   └── tests_pentest.py       # adversarial pass against auth
├── orders/
│   ├── models.py              # Order, OrderItem (price snapshots)
│   ├── views.py               # basket, submit (atomic + select_for_update)
│   ├── admin.py               # inline order items, derived-field readonlys
│   ├── tests.py               # happy-path basket-to-order
│   └── tests_security.py      # CSRF, ownership 404, price tampering, stock guard
├── templates/                 # Django templates
├── static/                    # CSS and SVG icons
├── docs/                      # SECURITY.md, DOCUMENTATION.md, API.md
└── storage/logs/              # security.log (JSON per line)
```

---

## 3. Conventions

### 3.1 Code style

- PEP 8 throughout, tightened where it helps readability — four-space indent, `snake_case` for everything that is not a class.
- Docstrings on every module, class, and public method. Terse is fine; vague is not.
- UK spelling in prose comments and docstrings (`customised`, `behaviour`, `defence`).
- `from __future__ import annotations` is not used — Django 5.0 + Python 3.11 makes string-form annotations unnecessary.

### 3.2 Test naming

- `tests.py` for the happy path. Class names describe the area under test (`OrderTestCase`); method names start with `test_` and read as a sentence (`test_owner_can_view_order`).
- `tests_security.py` for the negative path — every method asserts that an attack *fails*.
- `tests_pentest.py` (in `accounts/`) for the adversarial pass — every method asserts that an attack *succeeds in the current build*. A failing assertion there is a passing security control.

### 3.3 Migrations

- One purpose per migration. `0003_book_stock.py` adds the stock field and nothing else.
- Migration filenames carry a short verb-noun hint after the number — easier to scan than auto-generated `auto_20240101_1200`.

### 3.4 Templates

- One folder per app under `templates/`.
- Variables interpolated as `{{ name }}` only — never `|safe`, never `mark_safe`, never `{% autoescape off %}`. The XSS posture in `SECURITY.md` depends on this rule being absolute.
- CSRF token on every state-changing form. No exceptions.

---

## 4. UI Style Guide — Editorial Bookshop Look

The prototype's visual language is borrowed, deliberately, from the editorial side of online bookselling — the kind of catalogue page that feels closer to a literary magazine than to a generic e-commerce template. The reference point is Fable.co, but no asset, copy or trademark is copied from it; the goal is to capture the *rhythm* — the generous whitespace, the serif-on-sans typography, the pill-shaped controls — rather than the surface.

### 4.1 Layout grid

#### Container
- **Max-width**: 1100–1200 px for the main content column.
- **Padding**:
  - Desktop: 64–96 px vertical, 24–32 px horizontal.
  - Mobile: 40–64 px vertical, 16–24 px horizontal.

#### Breakpoints
- Mobile: `< 640 px`.
- Tablet: `640 px – 1024 px`.
- Desktop: `> 1024 px`.

#### Grid system
- Product grid: three columns desktop, two tablet, one mobile.
- Gap: 24–32 px between cards.

### 4.2 Typography

#### Font families
- **Serif display**: 'DM Serif Display' (Google Fonts) — used for headlines and section titles.
- **Sans**: 'Inter' (Google Fonts) — used for body copy and UI controls.

#### Type scale
- **Hero serif**: `clamp(44px, 5vw, 72px)`, line-height 0.95–1.05.
- **Section serif**: 32–44 px.
- **Page title**: `clamp(32px, 4vw, 44px)`.
- **Body**: 16–18 px, line-height 1.5–1.7.
- **Small meta** (price, author): 14–15 px.

#### Usage
- Headlines: serif, tight letter-spacing (`-0.02em`).
- Body: sans, relaxed line-height.
- UI controls: sans, medium weight (500).

The pairing matters: a sans-only page reads as generic, a serif-only page reads as a printed brochure rather than a working shop. The serif carries the editorial register; the sans carries the work the customer has actually come to do.

### 4.3 Spacing system

#### Tokens
- `--spacing-xs`: 8 px.
- `--spacing-sm`: 16 px.
- `--spacing-md`: 24 px.
- `--spacing-lg`: 32 px.
- `--spacing-xl`: 64 px.
- `--spacing-2xl`: 96 px.

#### Usage
- Section padding: `--spacing-xl` to `--spacing-2xl`.
- Component gaps: `--spacing-md` to `--spacing-lg`.
- Internal spacing: `--spacing-xs` to `--spacing-sm`.

The rule of thumb when in doubt: err on the side of more space. Tightening spacing later is cheap; loosening it later means re-thinking adjacent components.

### 4.4 Colour tokens

#### Primary
- `--forest-900`: `#1a4d3a` — the deep hero green.
- `--forest-800`: `#2d5a47` — pattern tones a step lighter.
- `--forest-700`: `#3d6b54` — pattern tones a further step lighter.

#### Neutral
- `--cream-50`: `#faf8f5` — warm off-white.
- `--ink-900`: `#1a1a1a` — near-black, used for text and icons.
- `--muted-600`: `#6b7280` — secondary text.
- `--border-200`: `#e5e7eb` — light hairline border.
- `--white`: `#ffffff`.

#### Usage
- Backgrounds: `--white`, `--cream-50`, `--forest-900`.
- Text: `--ink-900` for primary, `--muted-600` for secondary.
- Borders: `--border-200`.
- Icons: `--ink-900` on light grounds, `--white` on dark.

The palette is narrow on purpose. A small bookshop's website does not need a brand-system colour ramp; it needs three surfaces — light, cream, dark — and confidence about which one carries which content.

### 4.5 Component specifications

#### Navbar
- Height: 72 px desktop, 64 px mobile.
- Background: white on product pages; transparent overlay on a dark hero.
- Layout: hamburger (left), brand mark (centre), user/cart icons (right).
- Horizontal padding: at least 24 px.
- Border: 1 px solid `--border-200` along the bottom on white grounds.

#### Buttons
- **Pill button**:
  - Border-radius: `--radius-pill` (9999 px).
  - Padding: 14–16 px vertical, 26–30 px horizontal.
  - Background: white with a soft shadow.
  - Text: black, medium weight.
- **Small button**:
  - Padding: 8 px vertical, 16 px horizontal.
  - Font size: 14 px.

#### Search bar
- Height: 56–64 px.
- Border-radius: `--radius-pill` (9999 px).
- Border: 1 px solid `--border-200`.
- Shadow: `--shadow-soft`.
- Search icon: black circular button (44–48 px) embedded at the right edge.

#### Product cards
- **Image**:
  - Aspect ratio: 2 : 3.
  - Border-radius: `--radius-card` (16 px).
  - Shadow: `--shadow-card` (deliberately subtle).
- **Text layout**:
  - Title: sans, medium weight, 18 px.
  - Author: sans, lighter, 14 px, muted colour.
  - Price: sans, medium weight, 16 px, with breathing room above.

#### Hero sections

**Dark green hero**
- Background: `--forest-900` with a subtle geometric pattern.
- Text: white.
- Layout: headline and CTA on the left; an illustration placeholder on the right.
- Headline: large serif, two lines, tight letter-spacing.

**Cream hero**
- Background: `--cream-50`.
- Text: `--ink-900`.
- Layout: centred.
- Headline: giant serif, dramatic scale.
- Accent: a hand-drawn green scribble (SVG) overlaying one word — the only place a touch of irregularity is invited into the layout.

### 4.6 Component geometry and shadows

- `--radius-pill`: 9999 px (fully rounded).
- `--radius-card`: 16 px (within a 14–18 px tolerance).
- `--icon`: 24 px.
- `--nav-h`: 72 px.
- `--shadow-soft`: `0 8px 24px rgba(0, 0, 0, 0.06)` — for buttons and the search bar.
- `--shadow-card`: `0 2px 8px rgba(0, 0, 0, 0.04)` — for product cards.

### 4.7 Interaction states

#### Hover
- Buttons: a slight lift (`translateY(-1px)`) and a deepened shadow.
- Links: opacity 0.7.
- Icon buttons: background changes to `--border-200`.

#### Focus
- Visible ring: 2 px solid `--ink-900` with a 2 px offset.
- Every interactive element: must carry a visible focus state. No exceptions.

#### Active
- Buttons: scale down to `0.98`.
- Links: opacity 0.5.

#### Disabled
- Opacity: 0.5.
- Cursor: `not-allowed`.
- No hover effects.

### 4.8 Component classes

#### Layout
- `.container` — max-width container with padding.
- `.grid-3` — three-column responsive grid.

#### Navigation
- `.nav` — navbar container.
- `.nav-brand` — brand mark and word.
- `.icon-btn` — icon button (24 px).

#### Buttons
- `.btn`, `.btn--pill`, `.btn--primary`, `.btn--small`, `.btn--danger`.

#### Hero
- `.hero--dark`, `.hero--cream`.

#### Forms
- `.auth-form-container`, `.auth-form`, `.form-group`, `.form-input`, `.form-errors`.

#### Product
- `.product-card`, `.product-card-image`, `.product-card-title`, `.product-card-author`, `.product-card-price`.

#### Search
- `.search-pill`.

#### Orders
- `.basket-item`, `.order-card`, `.order-detail`.

### 4.9 Visual QA checklist

A pass through this list should be repeated whenever a template changes shape:

- [ ] Navbar padding sits at 24 px horizontally.
- [ ] Hero headline scales as `clamp(44px, 5vw, 72px)`.
- [ ] Pill controls are fully rounded (9999 px).
- [ ] Grid gaps are 24–32 px.
- [ ] Product card shadows stay subtle.
- [ ] Typography hierarchy reads serif-headline plus sans-body.
- [ ] Palette stays inside the forest / cream / ink ramp.
- [ ] Icons are 24 px, monochrome, thin-stroke.
- [ ] Spacing reads "editorial" — generous, not cramped.
- [ ] Mobile collapses cleanly to one or two columns.

### 4.10 Accessibility

- **Focus rings**: 2 px solid with a 2 px offset, behind `:focus-visible` so a mouse user is not punished with a ring on every click.
- **Contrast**: WCAG AA floor (4.5:1 for body text); checked against the four token-pairings used most often (ink on white, ink on cream, white on forest, muted on white).
- **Semantic HTML**: heading hierarchy and landmarks used as intended.
- **Alt text**: descriptive on every image; never empty for content images.
- **Keyboard navigation**: every interaction reachable without a mouse.
- **ARIA labels**: carry the meaning of icon-only buttons.

The honest position: AAA is the right ambition, AA is the floor, and the current build clears AA on every pairing checked.

### 4.11 Implementation notes

- **No CSS framework.** Plain CSS only — no Tailwind, no Bootstrap. The cost is more lines of CSS to maintain; the benefit is no fight with a framework's defaults when the design diverges from them.
- **Mobile first.** Styles are written for the small screen and progressively enhanced.
- **Component-first naming.** Reusable classes; no page-specific selectors.
- **Original content.** All copy, photography, and marks are original to the project — no Fable text, image or logo is copied.
- **Vanilla JavaScript only**, and only where a feature genuinely cannot be done in HTML and CSS.

### 4.12 File locations

- CSS: `static/assets/css/ui.css`.
- Icons: `static/assets/icons/*.svg`.
- Templates: `templates/*.html`.

---

## 5. Logging

A separate `'security'` logger writes one JSON line per event to `storage/logs/security.log`. The helpers live in `config/security_logger.py`:

- `log_login_success(request, user)` — username, hashed email, IP.
- `log_login_failure(request, username)` — candidate username and IP only; never the candidate password.
- `log_admin_access_denied(request, user, resource)` — authorisation failures on staff-only paths.
- `log_csrf_failure(request)` — path, verb, IP.
- `log_suspicious_input(request, input_type, value)` — pattern-matched hostile input, recorded but never blocked.
- `log_session_mismatch(request, user)` — user-agent or IP change, recorded for after-the-fact review.

Email addresses are hashed (truncated SHA-256) before they touch the file. The investigator who needs to map a hash back to a real customer can do so through the live database.

The custom `SecurityJSONFormatter` ensures the structured fields the helpers attach via `extra={...}` actually land in the file — Python's stdlib formatter would otherwise drop them silently.

---

## 6. Running the Project

The launcher scripts at the project root (`start.bat` for Windows, `start.sh` for Mac/Linux) handle the full setup-and-run sequence: virtual environment, dependencies, `.env`, migrations, admin user, sample books, dev server. The README at the project root documents both the one-click path and the manual setup for the cases where it isn't the right fit.

For the API surface — endpoints, parameters, JWT flow — see `API.md`.
For the security posture — threat model, design choices, manual tests, pen-test pass — see `SECURITY.md`.
