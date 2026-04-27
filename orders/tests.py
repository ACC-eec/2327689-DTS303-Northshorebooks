"""Happy-path tests for the orders app.

Negative-path / security cases live in :mod:`orders.tests_security`.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from catalogue.models import Book

from .models import Order, OrderItem


class OrderTestCase(TestCase):
    """Happy-path coverage of the basket-to-order journey.

    Cross-user isolation, CSRF and price-tampering live in
    :mod:`orders.tests_security`; this file checks that the ordinary
    submit-and-view sequence behaves the way a customer would expect.
    """

    def setUp(self):
        """Two users, a single in-stock book, one submitted order."""
        self.user1 = User.objects.create_user(
            username='user1', password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='user2', password='testpass123',
        )
        self.book = Book.objects.create(
            title='Test Book', author='Test Author',
            price=19.99, stock=10,
        )
        self.order1 = Order.objects.create(
            user=self.user1, status='SUBMITTED', total=19.99,
        )
        OrderItem.objects.create(
            order=self.order1, book=self.book,
            quantity=1, unit_price=Decimal('19.99'),
        )

    def test_user_cannot_view_others_orders(self):
        """A different user requesting the order id gets a 404."""
        self.client.login(username='user2', password='testpass123')
        response = self.client.get(f'/orders/{self.order1.id}/')
        self.assertEqual(response.status_code, 404)

    def test_user_can_view_own_order(self):
        """The owner of the order can read its detail page."""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(f'/orders/{self.order1.id}/')
        self.assertEqual(response.status_code, 200)

    def test_submit_locks_basket(self):
        """Submitting a basket promotes its status and stamps a timestamp."""
        self.client.login(username='user1', password='testpass123')
        basket = Order.objects.create(
            user=self.user1, status='BASKET', total=0,
        )
        OrderItem.objects.create(
            order=basket, book=self.book,
            quantity=1, unit_price=Decimal('19.99'),
        )

        self.client.post('/orders/submit/')
        basket.refresh_from_db()

        self.assertEqual(basket.status, 'SUBMITTED')
        self.assertIsNotNone(basket.submitted_at)
