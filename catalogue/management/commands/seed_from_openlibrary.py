"""Populate the catalogue with real books fetched from Open Library.

For each ISBN in the run, the command fetches the title, authors and
description, downloads the cover image into ``MEDIA_ROOT/covers/`` via
``Book.cover_image``, and either creates a new ``Book`` or updates the
existing one. Designed to leave the prototype with a recognisable
shelf — Gatsby, Mockingbird, 1984 — rather than the placeholder strings
a generic seed command would produce.

Usage::

    python manage.py seed_from_openlibrary
    python manage.py seed_from_openlibrary --clear
    python manage.py seed_from_openlibrary --isbns 9780743273565,9780061120084
    python manage.py seed_from_openlibrary --price 14.99
"""
import unicodedata
from decimal import Decimal

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from catalogue.models import Book


def _nfc(text):
    """Normalise Unicode to NFC so a Windows cp1252 console can print Brontë."""
    return unicodedata.normalize('NFC', text or '')


DEFAULT_ISBNS = [
    '9780743273565',  # The Great Gatsby
    '9780061120084',  # To Kill a Mockingbird
    '9780452284234',  # 1984
    '9780141439518',  # Pride and Prejudice
    '9780316769174',  # The Catcher in the Rye
    '9780399501487',  # Lord of the Flies
    '9780547928227',  # The Hobbit
    '9781451673319',  # Fahrenheit 451
    '9780141441146',  # Jane Eyre
    '9780451526342',  # Animal Farm
    '9780141439570',  # The Picture of Dorian Gray
    '9780141439556',  # Wuthering Heights
    '9780544003415',  # The Lord of the Rings
    '9780142437179',  # Moby-Dick
    '9780486280615',  # The Adventures of Huckleberry Finn
]

OPEN_LIBRARY_API = 'https://openlibrary.org/api/books'
OPEN_LIBRARY_BASE = 'https://openlibrary.org'


class Command(BaseCommand):
    help = 'Seed books from Open Library by ISBN (downloads covers to MEDIA_ROOT).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--isbns',
            help='Comma-separated ISBN list. Defaults to a curated set of 15 classics.',
        )
        parser.add_argument(
            '--price',
            type=Decimal,
            default=Decimal('12.99'),
            help='Default price applied to every seeded book (default: 12.99).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing books (and their covers) before seeding.',
        )

    def handle(self, *args, **options):
        isbns = (
            [i.strip() for i in options['isbns'].split(',') if i.strip()]
            if options['isbns']
            else DEFAULT_ISBNS
        )
        price = options['price']

        if options['clear']:
            deleted_covers = 0
            for book in Book.objects.exclude(cover_image=''):
                if book.cover_image:
                    book.cover_image.delete(save=False)
                    deleted_covers += 1
            deleted_books, _ = Book.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Cleared existing catalogue: {deleted_books} rows, {deleted_covers} cover files removed.'
            ))

        created, updated, skipped = 0, 0, 0
        for isbn in isbns:
            data = self._fetch_metadata(isbn)
            if not data:
                self.stdout.write(self.style.WARNING(f'No Open Library record for {isbn} — skipping'))
                skipped += 1
                continue

            title = _nfc(data.get('title', '')).strip()
            authors = _nfc(', '.join(a.get('name', '') for a in data.get('authors', []))) or 'Unknown'
            description = _nfc(self._fetch_description(data))
            cover_url = (data.get('cover') or {}).get('large') or (data.get('cover') or {}).get('medium', '')

            book, was_created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    'title': title or f'Untitled ({isbn})',
                    'author': authors,
                    'price': price,
                    'description': description,
                    'cover_image_url': cover_url,
                },
            )

            if not was_created:
                book.title = title or book.title
                book.author = authors
                book.description = description or book.description
                book.cover_image_url = cover_url or book.cover_image_url
                book.save()

            if cover_url and not book.cover_image:
                self._download_cover(book, cover_url, isbn)

            action = 'Created' if was_created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action}: {book.title} - {book.author}'))
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. created={created} updated={updated} skipped={skipped} total={len(isbns)}'
        ))

    def _fetch_metadata(self, isbn):
        try:
            resp = requests.get(
                OPEN_LIBRARY_API,
                params={'bibkeys': f'ISBN:{isbn}', 'format': 'json', 'jscmd': 'data'},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.stderr.write(f'Open Library request failed for {isbn}: {exc}')
            return None
        return resp.json().get(f'ISBN:{isbn}')

    def _fetch_description(self, data):
        works = data.get('works') or []
        if not works:
            return ''
        key = works[0].get('key', '')
        if not key:
            return ''
        try:
            resp = requests.get(f'{OPEN_LIBRARY_BASE}{key}.json', timeout=10)
            resp.raise_for_status()
        except requests.RequestException:
            return ''
        desc = resp.json().get('description', '')
        if isinstance(desc, dict):
            return desc.get('value', '')
        return desc or ''

    def _download_cover(self, book, cover_url, isbn):
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.stderr.write(f'Cover download failed for {isbn}: {exc}')
            return
        book.cover_image.save(f'{isbn}.jpg', ContentFile(resp.content), save=True)
