from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """Serializer for Book model."""

    cover_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'price', 'description',
            'cover_image', 'cover_image_url',
        ]
        read_only_fields = ['id']
