"""
Management command: load_mars_products
Usage:
    python manage.py load_mars_products           # adds MARS products (keeps existing)
    python manage.py load_mars_products --clear   # removes ALL makeup products first, then loads MARS
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Load MARS makeup products into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove all existing makeup products before loading MARS data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Product.objects.filter(product_range='makeup').delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing makeup products.'))

        self.stdout.write('Loading MARS makeup products...')
        call_command('loaddata', 'mars_makeup_products', verbosity=1)
        count = Product.objects.filter(brand='MARS').count()
        self.stdout.write(self.style.SUCCESS(f'Done. {count} MARS products now in database.'))
