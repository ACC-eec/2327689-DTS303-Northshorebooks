"""Django admin configuration for the orders app."""
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline editor showing each line item on the parent order page."""

    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin view of customer orders.

    Items show inline so staff can see the full order at a glance.
    Totals and timestamps are read-only because they are derived fields.
    """

    list_display = ['id', 'user', 'status', 'total', 'created_at',
                    'submitted_at']
    list_filter = ['status', 'created_at', 'submitted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'submitted_at', 'total']
    inlines = [OrderItemInline]
    ordering = ['-created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Standalone admin view of order items, mostly for support queries."""

    list_display = ['id', 'order', 'book', 'quantity', 'unit_price',
                    'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title', 'order__user__username']
    readonly_fields = ['unit_price', 'created_at']
    ordering = ['-created_at']
