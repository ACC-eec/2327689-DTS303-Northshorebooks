"""Django admin configuration for the catalogue app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin-only view of the catalogue.

    Surfaces stock prominently with a coloured badge so staff can spot
    low-stock or sold-out titles at a glance from the change list.
    """

    list_display = ['title', 'author', 'isbn', 'price', 'stock_badge',
                    'created_at']
    list_filter = ['author', 'created_at']
    search_fields = ['title', 'author', 'isbn', 'description']
    ordering = ['title']
    fields = ['title', 'author', 'isbn', 'price', 'stock', 'description',
              'cover_image', 'cover_image_url']

    @admin.display(description='Stock', ordering='stock')
    def stock_badge(self, obj):
        """Coloured stock indicator for the change-list table."""
        if obj.stock == 0:
            colour, label = '#b14a3a', f'Out of stock'
        elif obj.stock < 5:
            colour, label = '#b8860b', f'Low ({obj.stock})'
        else:
            colour, label = '#2e6f4a', f'{obj.stock} in stock'
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            colour, label,
        )
