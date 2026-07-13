"""
Management command: seed 8 default HabitCategory objects.
Usage: python manage.py seed_habits
"""
from django.core.management.base import BaseCommand
from apps.diagnostic.models import HabitCategory


HABITS = [
    {
        'slug': 'ayurvedic_supplement',
        'title': 'Took Ayurvedic Supplement',
        'icon': '🌿',
        'color_class': 'ayurvedic',
        'points': 10,
        'description': 'Logged your daily ayurvedic herb or supplement intake.',
        'order': 1,
    },
    {
        'slug': 'korean_routine',
        'title': 'Followed Korean Skincare Routine',
        'icon': '🧴',
        'color_class': 'korean',
        'points': 15,
        'description': 'Completed your full K-beauty multi-step skincare routine.',
        'order': 2,
    },
    {
        'slug': 'spf_applied',
        'title': 'Applied SPF Today',
        'icon': '☀️',
        'color_class': 'spf',
        'points': 8,
        'description': 'Protected your skin with sunscreen before going out.',
        'order': 3,
    },
    {
        'slug': 'water_intake',
        'title': 'Drank 8 Glasses of Water',
        'icon': '💧',
        'color_class': 'water',
        'points': 5,
        'description': 'Stayed well-hydrated throughout the day.',
        'order': 4,
    },
    {
        'slug': 'sleep_8hrs',
        'title': 'Got 8 Hours Sleep',
        'icon': '😴',
        'color_class': 'sleep',
        'points': 10,
        'description': 'Got a full night of quality beauty sleep.',
        'order': 5,
    },
    {
        'slug': 'makeup_removed',
        'title': 'Removed Makeup Before Bed',
        'icon': '💄',
        'color_class': 'makeup',
        'points': 12,
        'description': 'Double cleansed and removed all makeup before sleeping.',
        'order': 6,
    },
    {
        'slug': 'pharmacy_med',
        'title': 'Took Prescribed Medicine',
        'icon': '🧪',
        'color_class': 'pharmacy',
        'points': 10,
        'description': 'Followed your prescribed derma or pharmacy treatment.',
        'order': 7,
    },
    {
        'slug': 'no_stress',
        'title': 'Practiced Stress Relief',
        'icon': '🧘',
        'color_class': 'stress',
        'points': 8,
        'description': 'Meditated, journaled, or practised mindful relaxation.',
        'order': 8,
    },
]


class Command(BaseCommand):
    help = 'Seed default HabitCategory objects for Log & Earn dashboard'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for h in HABITS:
            obj, was_created = HabitCategory.objects.update_or_create(
                slug=h['slug'],
                defaults={k: v for k, v in h.items() if k != 'slug'},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ seed_habits complete — {created} created, {updated} updated.'
            )
        )
