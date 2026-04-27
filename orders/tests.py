from django.test import TestCase
from django.contrib.auth.models import User
from .models import Order, OrderItem
from catalogue.models import Book


class OrderTestCase(TestCase):
    """Test cases for Order model and views."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            price=19.99
        )
        self.order1 = Order.objects.create(
            user=self.user1,
            status='SUBMITTED',
            total=19.99
        )
        OrderItem.objects.create(
            order=self.order1,
            book=self.book,
            quantity=1,
            unit_price=19.99
        )
    
    def test_user_cannot_view_others_orders(self):
        """User cannot view another user's order."""
        self.client.login(username='user2', password='testpass123')
        response = self.client.get(f'/orders/{self.order1.id}/')
        self.assertEqual(response.status_code, 404)
    
    def test_user_can_view_own_order(self):
        """User can view their own order."""
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(f'/orders/{self.order1.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_submit_locks_basket(self):
        """Submitting order changes status and prevents edits."""
        self.client.login(username='user1', password='testpass123')
        basket = Order.objects.create(user=self.user1, status='BASKET', total=0)
        OrderItem.objects.create(
            order=basket,
            book=self.book,
            quantity=1,
            unit_price=19.99
        )
        
        response = self.client.post('/orders/submit/')
        basket.refresh_from_db()
        
        self.assertEqual(basket.status, 'SUBMITTED')
        self.assertIsNotNone(basket.submitted_at)
