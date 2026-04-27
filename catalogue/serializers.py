"""DRF serializers for the catalogue app."""
from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """JSON representation of a :class:`catalogue.models.Book`.

    The uploaded ``cover_image`` is exposed as a read-only URL — clients
    set covers either by URL (``cover_image_url``) or via the admin upload
    flow, never through the API.
    """

    cover_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'price', 'description',
            'cover_image', 'cover_image_url',
        ]
        read_only_fields = ['id']
