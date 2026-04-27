from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Book


class BookAPITestCase(TestCase):
    """Test cases for Book API."""
    
    def setUp(self):
        self.client = APIClient()
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            price=19.99,
            description='Test description'
        )
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
    
    def test_anonymous_can_get_books(self):
        """Anonymous users can GET books."""
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_anonymous_cannot_post_books(self):
        """Anonymous users cannot POST books."""
        response = self.client.post('/api/books/', {
            'title': 'New Book',
            'author': 'New Author',
            'price': '29.99'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_regular_user_cannot_post_books(self):
        """Regular users cannot POST books."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post('/api/books/', {
            'title': 'New Book',
            'author': 'New Author',
            'price': '29.99'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_post_books(self):
        """Admin users can POST books."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/books/', {
            'title': 'New Book',
            'author': 'New Author',
            'price': '29.99'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
