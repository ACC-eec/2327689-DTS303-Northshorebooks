"""Happy-path API tests for the catalogue.

Negative-path / security cases live in :mod:`catalogue.tests_security`.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Book


class BookAPITestCase(TestCase):
    """Verify the public/admin permission split on ``/api/books/``."""

    def setUp(self):
        """Seed one book and two users (admin + regular)."""
        self.client = APIClient()
        self.book = Book.objects.create(
            title='Test Book', author='Test Author',
            price=19.99, description='Test description', stock=5,
        )
        self.admin_user = User.objects.create_user(
            username='admin', password='testpass123', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='user', password='testpass123',
        )

    def test_anonymous_can_get_books(self):
        """Anonymous GET on the list endpoint returns 200."""
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_post_books(self):
        """Anonymous POST is forbidden."""
        response = self.client.post('/api/books/', {
            'title': 'New Book', 'author': 'New Author', 'price': '29.99',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_post_books(self):
        """A logged-in non-staff user is also forbidden."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/books/', {
            'title': 'New Book', 'author': 'New Author', 'price': '29.99',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_post_books(self):
        """An admin can create a book — happy path."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/books/', {
            'title': 'New Book', 'author': 'New Author', 'price': '29.99',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
