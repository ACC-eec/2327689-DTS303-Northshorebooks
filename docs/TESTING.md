# Security Testing Guide

This document provides manual security test cases to verify that security controls are working correctly.

## SQL Injection Tests

### Test 1: SQL Injection in Search Filter
1. Navigate to `/api/books/`
2. Add query parameter: `?search=' OR '1'='1`
3. **Expected**: No SQL errors, returns all books (or empty if no matches)
4. **Verify**: Check browser console and server logs for SQL errors → None

### Test 2: SQL Injection in Author Filter
1. Navigate to `/api/books/`
2. Add query parameter: `?author='; DROP TABLE books--`
3. **Expected**: No SQL errors, safe handling (returns empty or filtered results)
4. **Verify**: Check database - books table still exists

### Test 3: SQL Injection in Price Filter
1. Navigate to `/api/books/`
2. Add query parameter: `?min_price=' OR 1=1--`
3. **Expected**: Invalid input ignored, uses default filtering
4. **Verify**: No SQL errors in logs

---

## XSS Tests

### Test 1: Script Injection in Product Title (Admin)
1. Log in as admin
2. Create a book via admin panel with title: `<script>alert('XSS')</script>`
3. View the book detail page
4. **Expected**: Title displays as text, no script execution
5. **Verify**: Check page source - script tags are HTML-encoded

### Test 2: Script Injection in Search Query
1. Navigate to `/api/books/`
2. Add query parameter: `?search=<img src=x onerror=alert(1)>`
3. View results in browser
4. **Expected**: Search query is escaped, no script execution
5. **Verify**: Check page source - angle brackets are encoded

### Test 3: XSS in Order Item Display
1. As admin, create a book with XSS payload in title
2. Add to basket as regular user
3. View basket page
4. **Expected**: Title displays safely, no script execution

---

## CSRF Tests

### Test 1: Remove CSRF Token from Form
1. Log in as a user
2. Open browser DevTools → Network tab
3. Navigate to book detail page
4. Remove `{% csrf_token %}` from form (or modify token value)
5. Submit "Add to Basket" form
6. **Expected**: 403 Forbidden error
7. **Verify**: Check response status code → 403

### Test 2: CSRF Token Missing in API (if using forms)
1. Create a POST request to `/api/books/` without CSRF token
2. **Expected**: 403 Forbidden (if using SessionAuthentication)
3. **Verify**: Response status → 403

---

## Session Tests

### Test 1: Session Regeneration on Login
1. Note current session ID (from browser cookies)
2. Log out
3. Log in again
4. **Expected**: New session ID generated
5. **Verify**: Check cookies - session ID changed

### Test 2: Session Invalidation on Logout
1. Log in as a user
2. Copy session cookie value
3. Log out
4. Try to reuse the copied session cookie
5. **Expected**: Session invalid, requires re-authentication
6. **Verify**: Access protected page → Redirect to login

### Test 3: Session Timeout
1. Log in as a user
2. Wait 30+ minutes without activity
3. Try to access protected page
4. **Expected**: Session expired, redirect to login
5. **Verify**: Check `SESSION_COOKIE_AGE` setting → 1800 seconds

---

## Authentication Tests

### Test 1: Access Protected View Without Login
1. Log out (or use incognito window)
2. Navigate to `/orders/basket/`
3. **Expected**: Redirect to `/accounts/login/`
4. **Verify**: URL changes to login page

### Test 2: Access Order History Without Login
1. Log out
2. Navigate to `/orders/history/`
3. **Expected**: Redirect to login page

---

## Authorization Tests

### Test 1: User Cannot View Others' Orders
1. Create two users: User A and User B
2. Log in as User A
3. Create an order as User A
4. Note the order ID
5. Log out
6. Log in as User B
7. Navigate to `/orders/<order_id>/` (User A's order)
8. **Expected**: 404 Not Found (or 403 Forbidden)
9. **Verify**: Response status → 404

### Test 2: Admin Can View All Orders
1. Log in as admin (staff user)
2. Navigate to `/orders/<any_order_id>/`
3. **Expected**: Order details displayed
4. **Verify**: Page loads successfully

### Test 3: Non-Admin Cannot POST to API
1. Log in as regular user (not admin)
2. Send POST request to `/api/books/` with book data
3. **Expected**: 403 Forbidden
4. **Verify**: Response status → 403

### Test 4: Admin Can POST to API
1. Log in as admin
2. Send POST request to `/api/books/` with book data
3. **Expected**: 201 Created
4. **Verify**: Response status → 201, book created

---

## Password Security Tests

### Test 1: Rate Limiting
1. Log out
2. Attempt to log in with wrong password 5 times
3. On 6th attempt, try again
4. **Expected**: "Too many login attempts. Please try again in 5 minutes."
5. **Verify**: Error message displayed, login blocked

### Test 2: Generic Error Messages
1. Log out
2. Attempt login with wrong username
3. Attempt login with wrong password
4. **Expected**: Same generic message: "Invalid credentials"
5. **Verify**: No indication of whether username or password is wrong

### Test 3: Password Validation
1. Try to register with password length < 10
2. **Expected**: Validation error: "This password is too short. It must contain at least 10 characters."
3. **Verify**: Form does not submit

---

## Order Tampering Tests

### Test 1: Client-Side Total Modification
1. Log in as a user
2. Add items to basket
3. Open browser DevTools → Elements
4. Modify the total displayed in HTML
5. Submit order
6. **Expected**: Server recalculates total, correct total stored in database
7. **Verify**: Check database - order total matches server calculation

### Test 2: Price Change After Adding to Basket
1. Log in as a user
2. Add a book to basket (note price: $19.99)
3. As admin, change book price to $29.99
4. Submit order
5. **Expected**: Order uses original price ($19.99) from `unit_price` snapshot
6. **Verify**: Check `OrderItem.unit_price` in database → $19.99

### Test 3: Quantity Validation
1. Log in as a user
2. Add item to basket
3. Try to update quantity to -1
4. **Expected**: Error message, quantity not updated
5. **Verify**: Quantity remains at previous value

### Test 4: Quantity Maximum
1. Log in as a user
2. Add item to basket
3. Try to update quantity to 100
4. **Expected**: Error message: "Quantity cannot exceed 99"
5. **Verify**: Quantity limited to 99

---

## Input Validation Tests

### Test 1: Invalid Sort Parameter
1. Navigate to `/api/books/?ordering=DROP TABLE`
2. **Expected**: Invalid parameter ignored, default ordering used
3. **Verify**: Results ordered by title (default)

### Test 2: Numeric Validation for Price
1. Navigate to `/api/books/?min_price=abc`
2. **Expected**: Invalid input ignored, no error
3. **Verify**: All books returned (or filtered by valid params)

### Test 3: Search Length Limit
1. Navigate to `/api/books/?search=<very long string over 200 chars>`
2. **Expected**: Search truncated to 200 characters
3. **Verify**: Query processed with truncated search

---

## Security Headers Tests

### Test 1: Content-Type Options
1. Navigate to any page
2. Check response headers
3. **Expected**: `X-Content-Type-Options: nosniff`
4. **Verify**: Header present in response

### Test 2: Frame Options
1. Navigate to any page
2. Check response headers
3. **Expected**: `X-Frame-Options: DENY`
4. **Verify**: Header present, prevents clickjacking

### Test 3: Referrer Policy
1. Navigate to any page
2. Check response headers
3. **Expected**: `Referrer-Policy: strict-origin-when-cross-origin`
4. **Verify**: Header present

---

## Security Logging Tests

### Test 1: Login Success Logging
1. Log in successfully
2. Check `storage/logs/security.log`
3. **Expected**: JSON log entry with `event_type: login_success`
4. **Verify**: Log entry contains user info (hashed email), IP, timestamp

### Test 2: Login Failure Logging
1. Attempt failed login
2. Check `storage/logs/security.log`
3. **Expected**: JSON log entry with `event_type: login_failure`
4. **Verify**: Log entry contains username, IP, timestamp (no password)

### Test 3: Admin Access Denied Logging
1. As non-admin, try to access admin-only resource
2. Check `storage/logs/security.log`
3. **Expected**: JSON log entry with `event_type: admin_access_denied`
4. **Verify**: Log entry contains user info, resource, IP

---

## Test Execution Checklist

- [ ] SQL Injection tests passed
- [ ] XSS tests passed
- [ ] CSRF tests passed
- [ ] Session tests passed
- [ ] Authentication tests passed
- [ ] Authorization tests passed
- [ ] Password security tests passed
- [ ] Order tampering tests passed
- [ ] Input validation tests passed
- [ ] Security headers tests passed
- [ ] Security logging tests passed

## Notes

- All tests should be performed in a development environment
- Do not test on production data
- Some tests require admin access - create a test admin user
- Security logs are in `storage/logs/security.log` (JSON format)
