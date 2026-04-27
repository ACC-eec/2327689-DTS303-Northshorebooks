"""Order views for the basket-and-history flow.

Every state-changing endpoint is gated on:

* ``login_required`` — anonymous users cannot interact with a basket.
* ``csrf_protect`` — CSRF token must be present on every POST.
* ``require_http_methods(["POST"])`` — read endpoints stay GET-only.

The submission step (:func:`submit_order`) decrements ``Book.stock`` inside
``select_for_update`` so two concurrent shoppers cannot oversell a title.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from catalogue.models import Book
from config.security_logger import log_admin_access_denied

from .models import Order, OrderItem


@login_required
def basket_view(request):
    """Render the current user's BASKET order, creating one if absent."""
    basket, _ = Order.objects.get_or_create(
        user=request.user,
        status='BASKET',
        defaults={'total': 0},
    )
    # Recalculate to keep the displayed total in sync with the items.
    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])

    return render(request, 'orders/basket.html', {'basket': basket})


@login_required
@csrf_protect
@require_http_methods(['POST'])
def add_to_basket(request, book_id):
    """Add ``book_id`` to the basket or increment quantity if already present.

    Refuses to add a book whose ``stock`` is zero so the customer never
    holds a sold-out title in their basket.
    """
    book = get_object_or_404(Book, pk=book_id)

    if not book.is_in_stock:
        messages.error(request, f'{book.title} is currently out of stock.')
        return redirect('book_detail', pk=book_id)

    basket, _ = Order.objects.get_or_create(
        user=request.user,
        status='BASKET',
        defaults={'total': 0},
    )

    order_item, created = OrderItem.objects.get_or_create(
        order=basket,
        book=book,
        defaults={'quantity': 1, 'unit_price': book.price},
    )

    if not created:
        # Don't let basket quantity exceed available stock.
        if order_item.quantity + 1 > book.stock:
            messages.error(
                request,
                f'Only {book.stock} of {book.title} left in stock.',
            )
            return redirect('book_detail', pk=book_id)
        order_item.quantity += 1
        order_item.save()

    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])

    messages.success(request, f'Added {book.title} to basket')
    return redirect('book_detail', pk=book_id)


@login_required
@csrf_protect
@require_http_methods(['POST'])
def remove_item(request, item_id):
    """Remove a single item from the current user's basket."""
    item = get_object_or_404(
        OrderItem,
        pk=item_id,
        order__user=request.user,
        order__status='BASKET',
    )
    book_title = item.book.title
    basket = item.order
    item.delete()

    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])

    messages.success(request, f'Removed {book_title} from basket')
    return redirect('basket')


@login_required
@csrf_protect
@require_http_methods(['POST'])
def update_quantity(request, item_id):
    """Set the quantity for one basket item, capped at stock and 99."""
    item = get_object_or_404(
        OrderItem,
        pk=item_id,
        order__user=request.user,
        order__status='BASKET',
    )

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        messages.error(request, 'Invalid quantity')
        return redirect('basket')

    if quantity <= 0:
        messages.error(request, 'Quantity must be positive')
        return redirect('basket')
    if quantity > 99:
        messages.error(request, 'Quantity cannot exceed 99')
        return redirect('basket')
    if quantity > item.book.stock:
        messages.error(
            request,
            f'Only {item.book.stock} of {item.book.title} left in stock.',
        )
        return redirect('basket')

    item.quantity = quantity
    item.save()

    basket = item.order
    basket.total = basket.calculate_total()
    basket.save(update_fields=['total'])

    messages.success(request, 'Quantity updated')
    return redirect('basket')


@login_required
@csrf_protect
@require_http_methods(['POST'])
@transaction.atomic
def submit_order(request):
    """Promote the current basket to a SUBMITTED order.

    Re-reads each book row with ``select_for_update`` so concurrent submits
    cannot oversell stock, then re-stamps each line item's unit price from
    the database (defence against client-side price tampering) before
    decrementing stock and locking the order.
    """
    try:
        basket = Order.objects.get(user=request.user, status='BASKET')
    except Order.DoesNotExist:
        messages.error(request, 'No basket found')
        return redirect('basket')

    if basket.items.count() == 0:
        messages.error(request, 'Basket is empty')
        return redirect('basket')

    # Lock book rows for the duration of the transaction.
    for item in basket.items.select_related('book'):
        book = Book.objects.select_for_update().get(pk=item.book_id)
        if item.quantity > book.stock:
            messages.error(
                request,
                f'Only {book.stock} of {book.title} left in stock — '
                'please update your basket.',
            )
            return redirect('basket')

        # Recompute prices from the database — never trust the form.
        item.unit_price = book.price
        item.save()

        book.stock -= item.quantity
        book.save(update_fields=['stock'])

    basket.total = basket.calculate_total()
    basket.status = 'SUBMITTED'
    basket.submitted_at = timezone.now()
    basket.save()

    messages.success(request, 'Order submitted successfully')
    return redirect('order_history')


@login_required
def order_history(request):
    """List the authenticated user's submitted orders, newest first."""
    orders = Order.objects.filter(
        user=request.user,
        status='SUBMITTED',
    ).order_by('-submitted_at')

    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """Read-only detail view for an order owned by the user (or any staff)."""
    order = get_object_or_404(Order, pk=order_id)

    # An order is visible to its owner or to staff. Anyone else triggers a
    # 404 (not 403) to avoid leaking the existence of order ids.
    if order.user != request.user and not request.user.is_staff:
        log_admin_access_denied(request, request.user, f'order_{order_id}')
        raise Http404('Order not found')

    return render(request, 'orders/detail.html', {'order': order})
