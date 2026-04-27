"""Add admin-managed stock count to Book."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0002_book_isbn_book_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='stock',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Units currently available. Decremented automatically '
                          'when an order is submitted.',
            ),
        ),
    ]
