from django.db import models


class Book(models.Model):
    """Book model for the catalogue."""
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, blank=True, db_index=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    cover_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def cover_url(self):
        # Prefer the locally stored cover; fall back to a remote URL if set.
        if self.cover_image:
            return self.cover_image.url
        return self.cover_image_url or ''
