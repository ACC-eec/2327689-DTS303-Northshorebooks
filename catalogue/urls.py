from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api

# API Router
router = DefaultRouter()
router.register(r'books', api.BookViewSet, basename='book')

# Separate API and template URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    # Template routes
    path('', views.HomeView.as_view(), name='home'),  # Home page at root
    path('books/', views.BookListView.as_view(), name='book_list'),  # Book list
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),  # Book detail
]
