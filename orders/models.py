"""Order and OrderItem models — the basket-and-history domain."""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from catalogue.models import Book


class Order(models.Model):
    """A single order belonging to one user.

    An order moves through two statuses: ``BASKET`` while the user is
    still editing it, then ``SUBMITTED`` once they check out. Submitted
    orders are read-only as far as the application is concerned.
    """

    STATUS_CHOICES = [
        ('BASKET', 'Basket'),
        ('SUBMITTED', 'Submitted'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='BASKET',
    )
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
        return f'Order {self.id} - {self.user.username} - {self.status}'

    def calculate_total(self):
        """Return the sum of (quantity * unit_price) across all items."""
        total = self.items.aggregate(
            total=Sum(models.F('quantity') * models.F('unit_price')),
        )['total'] or 0
        return total

    def save(self, *args, **kwargs):
        """Refresh ``total`` from items on every persisted update."""
        if self.pk:
            self.total = self.calculate_total()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """A single line on an order — one book, a quantity, a captured price.

    ``unit_price`` is captured at add-to-basket time and re-stamped from
    the database at submit time, so changes to the book's catalogue price
    after submission never alter historical orders.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items',
    )
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'book'],
                name='unique_order_book',
            ),
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['book']),
        ]

    def __str__(self):
        return f'{self.quantity}x {self.book.title} @ ${self.unit_price}'

    def get_total(self):
        """Return ``quantity * unit_price`` for this line."""
        return self.quantity * self.unit_price

    def clean(self):
        """Validate quantity bounds (1..99 inclusive)."""
        if self.quantity <= 0:
            raise ValidationError('Quantity must be positive')
        if self.quantity > 99:
            raise ValidationError('Quantity cannot exceed 99')

    def save(self, *args, **kwargs):
        """Run model validation, then keep the parent order's total fresh."""
        self.full_clean()
        super().save(*args, **kwargs)
        if self.order:
            self.order.save()
