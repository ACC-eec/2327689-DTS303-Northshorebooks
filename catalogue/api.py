"""DRF API for the Book resource.

Public read access (``GET /api/books/`` and ``GET /api/books/<id>/``) and
admin-only write access (POST/PUT/PATCH/DELETE) — coursework requirement 2.

Filtering is built deliberately on Django ORM lookups to satisfy the
SQL-injection requirement: every query parameter is validated and
parameterised, never string-formatted into raw SQL.
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Book
from .serializers import BookSerializer


# Allow-listed values for ``?ordering=`` — anything else is silently
# discarded so a malicious caller cannot probe arbitrary columns.
ALLOWED_ORDERING_FIELDS = frozenset([
    'title', 'author', 'price', 'created_at',
    '-title', '-author', '-price', '-created_at',
])


class BookViewSet(viewsets.ModelViewSet):
    """CRUD viewset for :class:`catalogue.models.Book`.

    Read endpoints are public; write endpoints require ``is_staff`` via
    :class:`rest_framework.permissions.IsAdminUser`.
    """

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author']
    ordering_fields = ['title', 'author', 'price', 'created_at']
    ordering = ['title']

    def get_permissions(self):
        """Permit anyone to list/retrieve; require staff for everything else."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Apply optional ``author``, ``min_price``, ``max_price``, ``search``
        and ``ordering`` query parameters, ignoring anything malformed."""
        queryset = Book.objects.all()
        params = self.request.query_params

        author = params.get('author')
        if author is not None:
            queryset = queryset.filter(author__icontains=author)

        # Use Decimal to match Book.price's DecimalField — float would
        # introduce binary-rounding error on edge prices like 19.99.
        min_price = params.get('min_price')
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            except (InvalidOperation, TypeError):
                pass

        max_price = params.get('max_price')
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=Decimal(max_price))
            except (InvalidOperation, TypeError):
                pass

        search = params.get('search')
        if search is not None:
            # Cap length to avoid pathological regex/LIKE patterns.
            search = search[:200]
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(author__icontains=search)
            )

        ordering = params.get('ordering')
        if ordering and ordering in ALLOWED_ORDERING_FIELDS:
            queryset = queryset.order_by(ordering)

        return queryset
