"""Negative-path security tests for the catalogue app.

Each test fires a real attack payload (SQL injection, XSS, ordering
parameter probing, anonymous write) and asserts the framework rejects
or neutralises it. These tests fail loudly if the protections regress.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Book


class SQLInjectionTests(TestCase):
    """Coursework requirement 6 — SQL injection protection via the ORM."""

    def setUp(self):
        """Seed three books we can use to verify the table is intact."""
        self.book_a = Book.objects.create(
            title='Tide Tables', author='M. Coast', price=12.50, stock=3,
        )
        self.book_b = Book.objects.create(
            title='Lighthouse Notes', author='J. Beam', price=18.00, stock=1,
        )
        self.book_c = Book.objects.create(
            title="O'Connor's Fish Stew", author='J. Beam',
            price=9.99, stock=2,
        )

    def test_drop_table_payload_is_treated_as_literal(self):
        """A ``DROP TABLE`` payload must not execute — books must survive."""
        payload = "'; DROP TABLE catalogue_book; --"
        response = self.client.get('/api/books/', {'search': payload})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # If the payload had executed, this query would raise. The fact
        # that it returns the seed rows untouched is the proof.
        self.assertEqual(Book.objects.count(), 3)
        # No book matches the literal payload string.
        self.assertEqual(response.data['count'], 0)

    def test_or_one_equals_one_does_not_leak_rows(self):
        """A classic ``OR 1=1`` payload must not bypass the WHERE clause."""
        payload = "anything' OR '1'='1"
        response = self.client.get('/api/books/', {'author': payload})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The ORM treats the payload as a literal substring, so the
        # filter matches no rows.
        self.assertEqual(response.data['count'], 0)

    def test_apostrophe_in_data_is_safe_to_search(self):
        """Legitimate apostrophes survive search escaping (regression)."""
        response = self.client.get('/api/books/', {'search': "O'Connor"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [b['title'] for b in response.data['results']]
        self.assertIn("O'Connor's Fish Stew", titles)

    def test_unknown_ordering_field_is_silently_ignored(self):
        """Ordering parameter is allow-listed — no probing private columns."""
        response = self.client.get(
            '/api/books/', {'ordering': 'auth_user.password'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Default ordering by title kicks in; books still returned.
        self.assertEqual(response.data['count'], 3)


class XSSTests(TestCase):
    """Coursework requirement 9 — output is auto-escaped."""

    def test_script_tag_in_book_description_is_escaped(self):
        """A book description containing ``<script>`` renders inert HTML."""
        payload = '<script>window.pwned = true;</script>'
        book = Book.objects.create(
            title='XSS Probe', author='Tester', price=1.00, stock=1,
            description=payload,
        )

        response = self.client.get(f'/books/{book.pk}/')
        self.assertEqual(response.status_code, 200)
        rendered = response.content.decode('utf-8')

        # The raw payload must NOT appear unescaped.
        self.assertNotIn('<script>window.pwned = true;</script>', rendered)
        # The escaped form MUST appear instead.
        self.assertIn('&lt;script&gt;', rendered)

    def test_script_tag_in_book_title_is_escaped(self):
        """Same for the title — escaped on both list and detail pages."""
        payload = '<img src=x onerror=alert(1)>'
        book = Book.objects.create(
            title=payload, author='Tester', price=1.00, stock=1,
        )

        list_response = self.client.get('/books/')
        detail_response = self.client.get(f'/books/{book.pk}/')

        for resp in (list_response, detail_response):
            self.assertEqual(resp.status_code, 200)
            html = resp.content.decode('utf-8')
            self.assertNotIn('<img src=x onerror=alert(1)>', html)
            self.assertIn('&lt;img', html)


class APIPermissionTests(TestCase):
    """Coursework requirement 2 — read public, write admin-only."""

    def setUp(self):
        """Create one book and two users (regular + admin)."""
        self.client = APIClient()
        self.book = Book.objects.create(
            title='Tide Tables', author='M. Coast', price=12.50, stock=3,
        )
        self.regular = User.objects.create_user(
            username='regular', password='SeasidePass1!',
        )
        self.admin = User.objects.create_user(
            username='admin', password='SeasidePass1!', is_staff=True,
        )

    def test_anonymous_cannot_create_book(self):
        """An unauthenticated POST returns 401 or 403 — never 201."""
        response = self.client.post(
            '/api/books/',
            {'title': 'Stowaway', 'author': 'X', 'price': '5.00'},
            format='json',
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        self.assertFalse(Book.objects.filter(title='Stowaway').exists())

    def test_regular_user_cannot_delete_book(self):
        """A logged-in non-staff user is also rejected on writes."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.delete(f'/api/books/{self.book.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_admin_can_update_book(self):
        """Staff can write — happy path complement to the negative tests."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/books/{self.book.pk}/',
            {'price': '15.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
