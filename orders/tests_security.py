"""Negative-path security and stock-integrity tests for the orders app.

These tests prove four protections by attacking them:

* CSRF: a POST without the token is rejected (req 7).
* Price tampering: a server-side recalculation overrides any altered
  ``unit_price`` on submit (req 8).
* Stock guard: a sold-out book cannot be added to a basket (innovation).
* Stock decrement: submitting an order reduces stock atomically.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from catalogue.models import Book

from .models import Order, OrderItem


class CSRFEnforcementTests(TestCase):
    """Requirement 7 — every state-changing POST requires a CSRF token."""

    def setUp(self):
        """Spin up a CSRF-enforcing client and a logged-in user."""
        self.user = User.objects.create_user(
            username='ada', password='SeasidePass1!',
        )
        self.book = Book.objects.create(
            title='Tide Tables', author='M. Coast', price=12.50, stock=5,
        )
        # The default test client disables CSRF — opt back in to prove
        # the middleware actually rejects token-less posts.
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.login(username='ada', password='SeasidePass1!')

    def test_add_to_basket_without_csrf_token_is_rejected(self):
        """A POST missing the CSRF cookie/token returns 403."""
        response = self.csrf_client.post(f'/orders/add/{self.book.pk}/')
        self.assertEqual(response.status_code, 403)
        # Crucially: nothing was added to a basket.
        self.assertFalse(
            OrderItem.objects.filter(book=self.book).exists(),
        )

    def test_submit_order_without_csrf_token_is_rejected(self):
        """The submit endpoint is also gated on the token."""
        response = self.csrf_client.post('/orders/submit/')
        self.assertEqual(response.status_code, 403)


class PriceTamperingTests(TestCase):
    """Requirement 8 — order totals are recomputed server-side at submit."""

    def setUp(self):
        """Seed a user, a book at $20, and a basket holding it at $0.01."""
        self.user = User.objects.create_user(
            username='ada', password='SeasidePass1!',
        )
        self.book = Book.objects.create(
            title='Tide Tables', author='M. Coast',
            price=Decimal('20.00'), stock=5,
        )
        self.basket = Order.objects.create(user=self.user, status='BASKET')
        # Imagine a malicious client that wrote a bogus unit_price into
        # the database directly — say via a tampered request we missed.
        self.item = OrderItem.objects.create(
            order=self.basket, book=self.book,
            quantity=1, unit_price=Decimal('0.01'),
        )
        self.client.login(username='ada', password='SeasidePass1!')

    def test_submit_restamps_unit_price_from_database(self):
        """Submitting the order restores the canonical book price."""
        self.client.post('/orders/submit/')

        self.item.refresh_from_db()
        self.basket.refresh_from_db()

        # The line item now reflects the real catalogue price, not the
        # tampered one. Total follows.
        self.assertEqual(float(self.item.unit_price), 20.00)
        self.assertEqual(float(self.basket.total), 20.00)
        self.assertEqual(self.basket.status, 'SUBMITTED')


class StockGuardTests(TestCase):
    """Innovation feature — admin-managed stock is enforced on the basket."""

    def setUp(self):
        """Two books: one in stock (qty 2), one sold out (qty 0)."""
        self.user = User.objects.create_user(
            username='ada', password='SeasidePass1!',
        )
        self.in_stock = Book.objects.create(
            title='Tide Tables', author='M. Coast', price=12.50, stock=2,
        )
        self.sold_out = Book.objects.create(
            title='Lighthouse Notes', author='J. Beam', price=18.00, stock=0,
        )
        self.client.login(username='ada', password='SeasidePass1!')

    def test_cannot_add_sold_out_book(self):
        """Adding a stock=0 book leaves no order item behind."""
        response = self.client.post(f'/orders/add/{self.sold_out.pk}/')
        # Redirects back to the book detail with a flash message.
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            OrderItem.objects.filter(book=self.sold_out).exists(),
        )

    def test_submitting_decrements_stock(self):
        """A successful submit reduces ``Book.stock`` by the ordered qty."""
        # Add the book twice — basket holds quantity 2.
        self.client.post(f'/orders/add/{self.in_stock.pk}/')
        self.client.post(f'/orders/add/{self.in_stock.pk}/')

        self.client.post('/orders/submit/')

        self.in_stock.refresh_from_db()
        self.assertEqual(self.in_stock.stock, 0)

    def test_cannot_oversell_at_submit(self):
        """If stock drops between basket and submit, the submit aborts."""
        # Pre-fill the basket while stock is 2.
        self.client.post(f'/orders/add/{self.in_stock.pk}/')
        self.client.post(f'/orders/add/{self.in_stock.pk}/')

        # Admin reduces stock behind the scenes.
        self.in_stock.stock = 1
        self.in_stock.save(update_fields=['stock'])

        response = self.client.post('/orders/submit/')
        # Redirects back to the basket with an error message.
        self.assertEqual(response.status_code, 302)

        basket = Order.objects.get(user=self.user, status='BASKET')
        # Basket is still a basket — submit was refused.
        self.assertEqual(basket.status, 'BASKET')

        # Stock is unchanged: nothing was deducted.
        self.in_stock.refresh_from_db()
        self.assertEqual(self.in_stock.stock, 1)


class OrderIsolationTests(TestCase):
    """Requirement 4/8 — one user must not see another user's order."""

    def setUp(self):
        """Two users, one book, one submitted order belonging to user1."""
        self.user1 = User.objects.create_user(
            username='ada', password='SeasidePass1!',
        )
        self.user2 = User.objects.create_user(
            username='grace', password='SeasidePass1!',
        )
        self.book = Book.objects.create(
            title='Tide Tables', author='M. Coast', price=12.50, stock=5,
        )
        self.order = Order.objects.create(
            user=self.user1, status='SUBMITTED', total=12.50,
        )
        OrderItem.objects.create(
            order=self.order, book=self.book,
            quantity=1, unit_price=Decimal('12.50'),
        )

    def test_other_user_gets_404(self):
        """A different logged-in user gets 404, not 403 — order ids stay opaque."""
        self.client.login(username='grace', password='SeasidePass1!')
        response = self.client.get(f'/orders/{self.order.pk}/')
        self.assertEqual(response.status_code, 404)
