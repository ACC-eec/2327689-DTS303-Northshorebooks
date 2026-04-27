from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import action
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Book
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Book instances.
    Public GET access, admin-only write access.
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author']
    ordering_fields = ['title', 'author', 'price', 'created_at']
    ordering = ['title']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally restricts the returned books by filtering against
        query parameters in the URL.
        """
        queryset = Book.objects.all()
        
        # Filter by author (allowlist - safe from SQL injection via ORM)
        author = self.request.query_params.get('author', None)
        if author is not None:
            queryset = queryset.filter(author__icontains=author)
        
        # Filter by price range (numeric validation)
        min_price = self.request.query_params.get('min_price', None)
        if min_price is not None:
            try:
                min_price = float(min_price)
                queryset = queryset.filter(price__gte=min_price)
            except (ValueError, TypeError):
                pass  # Ignore invalid input
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price is not None:
            try:
                max_price = float(max_price)
                queryset = queryset.filter(price__lte=max_price)
            except (ValueError, TypeError):
                pass  # Ignore invalid input
        
        # Search across title and author (using Q objects - safe)
        search = self.request.query_params.get('search', None)
        if search is not None:
            # Limit search length to prevent abuse
            if len(search) > 200:
                search = search[:200]
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(author__icontains=search)
            )
        
        # Ordering with allowlist
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['title', 'author', 'price', 'created_at', '-title', '-author', '-price', '-created_at']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        
        return queryset
