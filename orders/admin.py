from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at', 'submitted_at']
    list_filter = ['status', 'created_at', 'submitted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'submitted_at', 'total']
    inlines = [OrderItemInline]
    ordering = ['-created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'book', 'quantity', 'unit_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title', 'order__user__username']
    readonly_fields = ['unit_price', 'created_at']
    ordering = ['-created_at']
