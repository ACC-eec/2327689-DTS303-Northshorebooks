"""Catalogue models — single source of truth for the book inventory."""
from django.db import models


class Book(models.Model):
    """A book listed in the Northshore Books catalogue.

    Stock is admin-managed: customers see only an "Available" or "Out of stock"
    state on the public site, while staff see and edit the integer count via
    the Django admin.
    """

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, blank=True, db_index=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    cover_image_url = models.URLField(blank=True)
    stock = models.PositiveIntegerField(
        default=0,
        help_text='Units currently available. Decremented automatically when '
                  'an order is submitted.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def cover_url(self):
        """Return a usable cover image URL or '' if none is set."""
        # Prefer a locally uploaded image; fall back to a remote URL.
        if self.cover_image:
            return self.cover_image.url
        return self.cover_image_url or ''

    @property
    def is_in_stock(self):
        """Customer-facing availability flag — never exposes the count."""
        return self.stock > 0
