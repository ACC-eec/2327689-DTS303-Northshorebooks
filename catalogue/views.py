"""Customer-facing HTML views for the book catalogue.

These are pure read views — anyone can browse them, no login required
(coursework requirement 1). Write access to the catalogue happens
exclusively through the admin and the DRF viewset in :mod:`catalogue.api`.
"""
from django.views.generic import DetailView, ListView, TemplateView

from .models import Book


class HomeView(TemplateView):
    """Landing page with the seaside hero and a featured-books carousel."""

    template_name = 'catalogue/home.html'

    def get_context_data(self, **kwargs):
        """Add a small slice of books for the carousel band."""
        context = super().get_context_data(**kwargs)
        context['books'] = Book.objects.all()[:12]
        return context


class BookListView(ListView):
    """Paginated grid of every book in the catalogue."""

    model = Book
    template_name = 'catalogue/book_list.html'
    context_object_name = 'books'
    paginate_by = 12


class BookDetailView(DetailView):
    """Single-book page used by the public site and the basket links."""

    model = Book
    template_name = 'catalogue/book_detail.html'
    context_object_name = 'book'
