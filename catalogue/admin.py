from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'price', 'created_at']
    list_filter = ['author', 'created_at']
    search_fields = ['title', 'author', 'isbn', 'description']
    ordering = ['title']
    fields = ['title', 'author', 'isbn', 'price', 'description', 'cover_image', 'cover_image_url']
