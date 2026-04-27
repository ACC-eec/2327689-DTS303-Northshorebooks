from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import Order, OrderItem
from catalogue.models import Book
from config.security_logger import log_admin_access_denied


@login_required
def basket_view(request):
    """View current basket (BASKET order) for user."""
    basket, created = Order.objects.get_or_create(
        user=request.user,
        status='BASKET',
        defaults={'total': 0}
    )
    # Ensure total is up to date
    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])
    
    return render(request, 'orders/basket.html', {'basket': basket})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_to_basket(request, book_id):
    """Add book to basket or increment quantity if exists."""
    book = get_object_or_404(Book, pk=book_id)
    
    # Get or create basket
    basket, created = Order.objects.get_or_create(
        user=request.user,
        status='BASKET',
        defaults={'total': 0}
    )
    
    # Get or create order item
    order_item, created = OrderItem.objects.get_or_create(
        order=basket,
        book=book,
        defaults={
            'quantity': 1,
            'unit_price': book.price
        }
    )
    
    if not created:
        # Increment quantity if item already exists
        order_item.quantity += 1
        order_item.save()
    
    # Recalculate total
    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])
    
    messages.success(request, f'Added {book.title} to basket')
    return redirect('book_detail', pk=book_id)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def remove_item(request, item_id):
    """Remove item from basket."""
    item = get_object_or_404(OrderItem, pk=item_id, order__user=request.user, order__status='BASKET')
    book_title = item.book.title
    item.delete()
    
    # Update basket total
    basket = item.order
    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])
    
    messages.success(request, f'Removed {book_title} from basket')
    return redirect('basket')


@login_required
@csrf_protect
@require_http_methods(["POST"])
def update_quantity(request, item_id):
    """Update quantity of item in basket."""
    item = get_object_or_404(OrderItem, pk=item_id, order__user=request.user, order__status='BASKET')
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, 'Quantity must be positive')
            return redirect('basket')
        if quantity > 99:
            messages.error(request, 'Quantity cannot exceed 99')
            return redirect('basket')
        
        item.quantity = quantity
        item.save()
        
        # Update basket total
        basket = item.order
        basket.total = basket.calculate_total()
        basket.save(update_fields=['total'])
        
        messages.success(request, 'Quantity updated')
    except (ValueError, TypeError):
        messages.error(request, 'Invalid quantity')
    
    return redirect('basket')


@login_required
@csrf_protect
@require_http_methods(["POST"])
@transaction.atomic
def submit_order(request):
    """Submit order (change status to SUBMITTED)."""
    try:
        basket = Order.objects.get(user=request.user, status='BASKET')
    except Order.DoesNotExist:
        messages.error(request, 'No basket found')
        return redirect('basket')
    
    if basket.items.count() == 0:
        messages.error(request, 'Basket is empty')
        return redirect('basket')
    
    # Recalculate total from database prices (never trust client)
    for item in basket.items.all():
        # Ensure unit_price matches current book price
        item.unit_price = item.book.price
        item.save()
    
    basket.total = basket.calculate_total()
    basket.status = 'SUBMITTED'
    from django.utils import timezone
    basket.submitted_at = timezone.now()
    basket.save()
    
    messages.success(request, 'Order submitted successfully')
    return redirect('order_history')


@login_required
def order_history(request):
    """List of submitted orders for user."""
    orders = Order.objects.filter(
        user=request.user,
        status='SUBMITTED'
    ).order_by('-submitted_at')
    
    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """Detail view for an order (user or staff only)."""
    order = get_object_or_404(Order, pk=order_id)
    
    # Check authorization: user must own order or be staff
    if order.user != request.user and not request.user.is_staff:
        if request.user.is_staff:
            log_admin_access_denied(request, request.user, f'order_{order_id}')
        raise Http404("Order not found")
    
    return render(request, 'orders/detail.html', {'order': order})
