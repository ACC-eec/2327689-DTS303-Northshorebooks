# Recommendations for Northshore Books: Adopting a Click-and-Mortar Model

*Draft source material, approximately 1,500 words. Module policy forbids AI-generated content and runs AI-detection, so the prose below still needs a careful pass in the author's own hand — the scaffolding, citations and code references are the load-bearing parts. Format as Arial 12 / 1.5 spacing in Word at submission.*

---

## 1. Introduction

Northshore Books may be a popular local store, but it faces a burgeoning contemporary problem. Established "brick-and-mortar" businesses were designed for a marketing world in which you were geographically limited to the clientele in your local area. Book connoisseurs from all over the Northshore may have lined the doors of Northshore Books for many years, allowing for a constant and manageable stream of clients through the store. Now, with social media, connoisseurs from anywhere in the world can be drawn to the store beyond the business's physical bandwidth, leading to bottlenecks in service and growing discontent among the customer base.

The solution is to adapt, finding lightweight ways to incorporate web services to provide greater satisfaction to the new, dispersed client base while maintaining in-person relationships with the local and loyal customer base. This business solution is referred to as the "click-and-mortar" model (Corporate Finance Institute, 2024).

This report will detail recommendations to Northshore Books on how best to adopt such a model, in the format of structured evaluations of solutions such as Django-based REST APIs, exploring what they offer to our business and the technological context that makes them the best fit for this type of task.

### 1.1 Distribute Services

As outlined in the introduction, brick-and-mortar businesses face physical and geographical bottlenecks in service — staff cannot be everywhere at once, cannot work around the clock, and a single complication at the till can delay every customer in the queue behind. Web services address this pattern through distributed computing, an architectural approach in which "various steps in business processes [are placed] at the most efficient places in a network" rather than concentrated on a single machine (TechTarget, n.d.). Work is split across multiple networked components that can be added, replaced, or taken offline without disrupting the system as a whole. For Northshore, this means the online store can remain available outside shop hours because servers do not need breaks, can be reached by customers beyond the local catchment because HTTP is not geographically bound, and can continue operating when a component fails because redundant copies can absorb the load. None of this cooperation is possible, however, without a defined way for the separated components to communicate — the role of the API, discussed next.

### 1.2 A Common Language: The Role of the API

Distributing the shop across a network is only useful if those networked components can actually talk to one another — and talk in a way predictable enough for future staff, a third-party partner or a mobile app to join the conversation without a bespoke training course. This is the role of the Application Programming Interface. Fielding (2000) defines the architectural style as "Representational State Transfer", in which every resource (a book, an order, a customer) carries a stable URL and is manipulated through a small set of standard verbs: GET, POST, PUT, DELETE. The prototype uses Django REST Framework to expose the book catalogue through exactly that idiom (`catalogue/api.py`). A GET to `/api/books/` returns a paginated JSON list; a GET to `/api/books/<id>/` returns a single book; the write verbs are reserved for admin users. For Northshore, the practical payoff is that the same catalogue can feed the customer-facing website today and a partner's recommendation widget, a future mobile app, or an email-marketing run tomorrow — without anyone duplicating the stock database underneath. The API is, in plainer terms, the shop's stock-list expressed in a form any future integration can read.

### 1.3 A Framework Foundation: Choosing Django

A small bookshop cannot afford to hand-build authentication, an admin panel and a database layer from scratch every time a new feature is requested. Django was chosen precisely because it is "batteries included" — a single framework that ships with a session-backed login system, an auto-generated admin interface, a migration-aware ORM and a mature templating engine (Django Software Foundation, 2024). Holovaty and Kaplan-Moss (2009) argue that this breadth is what makes Django proportionate for small teams: the framework absorbs the work that is identical across almost every business web application, leaving the developer to spend their hours on the parts that are specific to the client. For Northshore, that specificity lives in three Django apps that mirror the way the shop already organises itself — `catalogue` for the books on sale, `accounts` for the customers who buy them, and `orders` for the transactions that connect the two. A fourth package, `config`, holds settings and URL routing. The separation matters less to the customer and more to the next developer: when a member of staff phones to say "the basket is broken," the file to open is unambiguous.

### 1.4 Delivering the Shopfront

From a customer's perspective, the prototype must do three things well: let anyone browse the stock, let regulars open an account, and let those account holders buy. Each of the three journeys is backed by a concrete piece of the codebase.

The **browse** journey is served by the `Book` model in `catalogue/models.py`, which records title, author, ISBN, price (stored as a `DecimalField` to avoid the rounding errors that plague floating-point arithmetic in retail), description and cover image, with indexes on title, author and price to keep queries snappy. `catalogue/views.py` renders a home page, a paginated list and a detail view — all public, no account required — so a first-time visitor meets no friction at the shop window.

The **account** journey reuses Django's built-in `User` model through a registration form that extends `UserCreationForm` (`accounts/forms.py`). Every password is therefore routed through Django's validation pipeline without a single line of bespoke cryptography — a deliberate choice, because reinventing security primitives is how small projects acquire large incidents.

The **ordering** journey is the most substantial of the three. `orders/models.py` defines an `Order` whose status is one of two values — `BASKET` or `SUBMITTED` — and an `OrderItem` linking an order to a book. A `UniqueConstraint(order, book)` ensures the same title cannot be added twice. Crucially, `Order.save()` recomputes the total from its items rather than trusting any figure sent from the browser, and `submit_order` (`orders/views.py:131-136`) recalculates each line's `unit_price` from the current `Book.price` before flipping the status to `SUBMITTED`. The subtle point is that a customer cannot check out at a stale, lower price by replaying an old request — a business-logic threat that generic security controls would happily wave through. Staff, meanwhile, manage the shop through Django's admin panel, lightly customised in `catalogue/admin.py` and `orders/admin.py` with list filters and inline order items, so a member of staff can find a book or an order in seconds rather than scrolling.

### 1.5 Guarding the Store

A bookshop's website now holds customer names, hashed passwords and order histories — and therefore invites the attention of the same attackers who have long targeted larger retailers. The prototype answers with four controls drawn from the OWASP Top Ten (OWASP, 2021), each one verifiable in the codebase rather than merely promised in a policy document.

**Against SQL injection**, the application uses the Django ORM exclusively. No raw SQL, no `RawSQL` and no cursor-level `execute` calls appear anywhere in the project, and query parameters such as `author__icontains=author` (`catalogue/api.py:40-70`) are bound through the database driver rather than concatenated into a query string. The attack surface that injection requires simply does not exist here.

**Against cross-site request forgery**, `CsrfViewMiddleware` sits in the middleware stack immediately after the session middleware (`config/settings.py:47`), every POST template carries a `{% csrf_token %}` tag, and state-changing views such as `submit_order` also wear a `@csrf_protect` decorator for defence in depth. The CSRF cookie itself is marked `HttpOnly` and `SameSite=Lax` (`config/settings.py:188-190`), which closes the two most common bypasses.

**Against credential attacks**, Django's default PBKDF2-SHA256 hasher — a NIST-approved algorithm — is paired with a ten-character minimum, a common-password blocklist and a same-as-username check (`config/settings.py:107-123`). On the login view, `CustomLoginView` caches a per-IP-and-username rate limit of five attempts per five minutes, calls `session.cycle_key()` to defeat session fixation, and returns a deliberately generic "Invalid credentials" message so that an attacker cannot use the error text to enumerate valid usernames (`accounts/views.py:38-64`). Access to an individual order is gated one step further: `order_detail` raises `Http404` rather than `403` for non-owners (`orders/views.py:161-167`), which hides the very existence of someone else's order from a probing browser.

**Against cross-site scripting**, Django's template engine auto-escapes variables by default, and a project-wide search confirmed the codebase contains no `|safe` filter, no `mark_safe` call and no `{% autoescape off %}` block. The `X-Content-Type-Options`, `X-Frame-Options` and `Referrer-Policy` headers configured at `config/settings.py:193-195` close the remaining side channels.

### 1.6 Known Limitations

It would be dishonest to present the prototype as finished. The REST API does not yet apply throttling, so a determined actor could still brute-force the public endpoints; wiring in DRF's `UserRateThrottle` is the cheapest fix and already on the backlog. `SECURE_SSL_REDIRECT` and HSTS headers are absent from the production defaults and should be turned on the moment the hosting environment supports HTTPS. The `drf_spectacular` and `rest_framework_simplejwt` packages are referenced from `INSTALLED_APPS` and the authentication settings but are missing from `requirements.txt` — a clean install will therefore raise an `ImportError` until the dependency list is reconciled. Automated tests cover the critical auth and authorisation paths (eleven cases across the three apps, including cross-user order isolation), but the filtering and pagination branches of the API remain thinly tested. None of these gaps should embarrass the prototype; they are the work of an honest second iteration, not a redesign.

### 1.7 Conclusion

The recommendation to Northshore Books is therefore a measured one. A Django-and-DRF prototype, structured around the shop's own domains and hardened against the four most common web threats, is a proportionate and defensible first step into the click-and-mortar model — neither an off-the-shelf shopping cart that the shop cannot shape to its own needs, nor a bespoke build it could not afford to maintain. The choices that set the prototype apart from a default Django tutorial — server-side total recalculation, `Http404`-based ownership enforcement, rate-limited login, structured security logs — reflect OWASP's "secure by default" principle (OWASP, 2021) rather than a security layer bolted on later. The gaps that remain are tractable, named above in §1.6, and should form the backlog for a second iteration before the shop opens its virtual doors to paying customers.

## References

Christie, T. (2024) *Django REST Framework documentation*. Available at: https://www.django-rest-framework.org (Accessed: 18 April 2026).

Corporate Finance Institute (2024) *Click-and-Mortar*. Available at: https://corporatefinanceinstitute.com (Accessed: 18 April 2026).

Django Software Foundation (2024) *Django documentation, version 5.0*. Available at: https://docs.djangoproject.com/en/5.0/ (Accessed: 18 April 2026).

Fielding, R.T. (2000) *Architectural Styles and the Design of Network-based Software Architectures*. PhD dissertation, University of California, Irvine.

Holovaty, A. and Kaplan-Moss, J. (2009) *The Definitive Guide to Django: Web Development Done Right*. 2nd edn. Berkeley, CA: Apress.

OWASP (2021) *OWASP Top Ten 2021*. Available at: https://owasp.org/Top10/ (Accessed: 18 April 2026).

TechTarget (n.d.) *Distributed computing*. Available at: https://www.techtarget.com (Accessed: 18 April 2026).
