from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from catalogue.models import Book


class Order(models.Model):
    """Order model for customer orders."""
    STATUS_CHOICES = [
        ('BASKET', 'Basket'),
        ('SUBMITTED', 'Submitted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BASKET')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.status}"
    
    def calculate_total(self):
        """Recalculate total from order items."""
        total = self.items.aggregate(
            total=Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or 0
        return total
    
    def save(self, *args, **kwargs):
        """Override save to recalculate total if needed."""
        if self.pk:
            # Recalculate total from items
            self.total = self.calculate_total()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Order item model linking orders to books."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'book'],
                name='unique_order_book'
            )
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['book']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.book.title} @ ${self.unit_price}"
    
    def get_total(self):
        """Calculate total for this order item."""
        return self.quantity * self.unit_price
    
    def clean(self):
        """Validate order item."""
        if self.quantity <= 0:
            raise ValidationError('Quantity must be positive')
        if self.quantity > 99:
            raise ValidationError('Quantity cannot exceed 99')
    
    def save(self, *args, **kwargs):
        """Override save to update order total."""
        self.full_clean()
        super().save(*args, **kwargs)
        # Update order total
        if self.order:
            self.order.save()
