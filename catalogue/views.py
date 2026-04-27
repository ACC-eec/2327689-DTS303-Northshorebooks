from django.views.generic import ListView, DetailView, TemplateView
from .models import Book


class HomeView(TemplateView):
    """Home page view with featured books carousel."""
    template_name = 'catalogue/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all books for the carousel
        context['books'] = Book.objects.all()[:12]  # Limit to 12 for carousel
        return context


class BookListView(ListView):
    """List view for books."""
    model = Book
    template_name = 'catalogue/book_list.html'
    context_object_name = 'books'
    paginate_by = 12


class BookDetailView(DetailView):
    """Detail view for a single book."""
    model = Book
    template_name = 'catalogue/book_detail.html'
    context_object_name = 'book'
