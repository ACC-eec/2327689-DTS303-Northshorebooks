from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache


class AccountsTestCase(TestCase):
    """Test cases for accounts app."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_registration(self):
        """Test user registration."""
        response = self.client.post('/accounts/register/', {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_login_required_redirect(self):
        """Test that login is required for order views."""
        response = self.client.get('/orders/basket/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_login_rate_limiting(self):
        """Test login rate limiting."""
        cache.clear()
        # Attempt 5 failed logins
        for i in range(5):
            response = self.client.post('/accounts/login/', {
                'username': 'testuser',
                'password': 'wrongpass',
            })
        
        # 6th attempt should be blocked
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertContains(response, 'Too many login attempts', status_code=200)
