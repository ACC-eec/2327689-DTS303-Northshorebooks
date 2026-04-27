# Security Design Decisions

This document explains key security design choices made during development and the rationale behind them.

## Session Cookie SameSite

**Decision**: `SESSION_COOKIE_SAMESITE = 'Lax'`

**Rationale**: 
- Allows GET requests from external sites (e.g., book links shared on social media)
- Still protects against CSRF for state-changing POST requests
- Better user experience than `Strict`

**Alternative Considered**: 
- `Strict`: More secure but breaks external links and some legitimate use cases
- `None`: Requires `Secure` flag and HTTPS, less secure for HTTP development

**Tradeoff**: Slightly less secure than `Strict` but much better usability.

---

## Session Timeout

**Decision**: `SESSION_COOKIE_AGE = 1800` (30 minutes) + `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`

**Rationale**:
- 30 minutes balances security (prevents long-lived sessions) with usability (users don't get logged out too frequently)
- Expiring on browser close adds extra security layer
- Common industry practice

**Alternative Considered**:
- 15 minutes: Too short, poor user experience
- 60 minutes: Too long, increases risk of session hijacking
- Absolute timeout only: Less secure, sessions persist across browser sessions

**Tradeoff**: Balance between security and user experience.

---

## Rate Limiting

**Decision**: 5 attempts → 5 minute lockout, keyed by IP+username

**Rationale**:
- Prevents brute force attacks while allowing legitimate retries
- Keyed by IP+username prevents one user from blocking others
- 5-minute lockout is sufficient deterrent without being too harsh

**Alternative Considered**:
- IP-only: One attacker could block all users from same IP
- Username-only: Easy to bypass with multiple IPs
- Longer lockout (15+ minutes): Too harsh for legitimate mistakes
- Shorter lockout (1 minute): Too easy to bypass

**Tradeoff**: Balance between security and usability.

---

## CSP Policy

**Decision**: Start minimal (allow self, inline styles for Django admin)

**Rationale**:
- Django admin requires inline styles and scripts
- Can be tightened incrementally after testing
- Avoids breaking existing functionality

**Alternative Considered**:
- Strict CSP from start: Would break Django admin, requires significant refactoring
- No CSP: Less secure, allows XSS vectors

**Tradeoff**: Security vs. functionality - incremental approach preferred.

**Future Improvement**: Implement nonce-based CSP for Django admin.

---

## User-Agent Binding

**Decision**: Optional feature, documented tradeoff

**Rationale**:
- Can break legitimate users (mobile apps, proxy changes, VPN)
- Adds complexity for minimal security gain
- Session regeneration on login provides good protection

**Alternative Considered**:
- Always enforce: Too many false positives, poor user experience
- Never enforce: Slightly less secure

**Tradeoff**: Security vs. usability - optional is best balance.

---

## Password Minimum Length

**Decision**: 10 characters minimum

**Rationale**:
- Stronger than Django default (8)
- Still reasonable for users
- Aligns with modern security best practices

**Alternative Considered**:
- 8 characters: Too weak, easy to brute force
- 12+ characters: Too strict, poor user experience

**Tradeoff**: Security vs. usability.

---

## Generic Error Messages

**Decision**: "Invalid credentials" for all login failures

**Rationale**:
- Prevents username enumeration attacks
- Standard security practice
- Doesn't reveal whether username or password is wrong

**Alternative Considered**:
- Specific errors: "Username not found" vs "Wrong password" - reveals usernames
- No error message: Poor user experience

**Tradeoff**: Security vs. user experience - security wins.

---

## Order Total Recalculation

**Decision**: Always recalculate from database on submit

**Rationale**:
- Never trust client-side data
- Prevents price tampering
- Ensures consistency

**Alternative Considered**:
- Trust client total: Vulnerable to tampering
- Only recalculate if changed: Still vulnerable, adds complexity

**Tradeoff**: Performance vs. security - security wins (recalculation is fast).

---

## Price Snapshots

**Decision**: Store `unit_price` in `OrderItem` at time of order

**Rationale**:
- Preserves historical pricing
- Prevents price changes from affecting submitted orders
- Standard e-commerce practice

**Alternative Considered**:
- Always use current price: Unfair to customers if prices increase
- Only snapshot on submit: Could allow price manipulation during basket stage

**Tradeoff**: None - best practice.

---

## Security Logging Format

**Decision**: JSON lines to `storage/logs/security.log`

**Rationale**:
- Structured logging enables easy parsing and analysis
- JSON format is standard and tool-friendly
- Separate security log for focused monitoring

**Alternative Considered**:
- Plain text: Harder to parse and analyze
- Database logging: Adds database load, harder to rotate
- Syslog: Requires additional infrastructure

**Tradeoff**: Simplicity vs. functionality - JSON provides good balance.

---

## Email Hashing in Logs

**Decision**: Hash emails (SHA256, first 16 chars) instead of storing full addresses

**Rationale**:
- Reduces PII exposure in logs
- Still allows correlation of events
- Complies with privacy best practices

**Alternative Considered**:
- Full email: Privacy risk, PII exposure
- No email info: Harder to correlate events

**Tradeoff**: Privacy vs. functionality - hashing provides good balance.

---

## CSRF for API Endpoints

**Decision**: Use `SessionAuthentication` for API (CSRF required) or `TokenAuthentication` (no CSRF)

**Rationale**:
- SessionAuthentication provides CSRF protection automatically
- TokenAuthentication is stateless, no CSRF needed
- Documented in settings

**Alternative Considered**:
- Always require CSRF: Breaks some API clients
- Never require CSRF: Less secure for browser-based API calls

**Tradeoff**: Security vs. API usability - SessionAuthentication is good default.

---

## Summary

All security decisions prioritize:
1. **Security by default**: Secure configurations unless explicitly needed otherwise
2. **Usability balance**: Don't break legitimate use cases
3. **Industry standards**: Follow Django and security best practices
4. **Incremental improvement**: Can tighten security over time

Most decisions follow the principle of "secure by default, configurable when needed."
