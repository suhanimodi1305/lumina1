"""
Management command: python manage.py create_superuser

Creates a Django superuser non-interactively, reading credentials from
environment variables or falling back to safe defaults for local dev.

Usage
-----
  # Use .env / environment variables (recommended):
  python manage.py create_superuser

  # Override any value directly on the CLI:
  python manage.py create_superuser \
      --username admin \
      --email admin@example.com \
      --password secret123 \
      --first-name Admin \
      --last-name User

Environment variables (all optional, each has a CLI equivalent):
  DJANGO_SUPERUSER_USERNAME   default: admin
  DJANGO_SUPERUSER_EMAIL      default: admin@lumina.com
  DJANGO_SUPERUSER_PASSWORD   default: Admin@1234
  DJANGO_SUPERUSER_FIRSTNAME  default: (empty)
  DJANGO_SUPERUSER_LASTNAME   default: (empty)
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a superuser non-interactively (env vars or CLI args)."

    # ── Argument declaration ─────────────────────────────────────────────────

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=None,
            help="Superuser username (env: DJANGO_SUPERUSER_USERNAME, default: admin)",
        )
        parser.add_argument(
            "--email",
            default=None,
            help="Superuser email (env: DJANGO_SUPERUSER_EMAIL, default: admin@lumina.com)",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Superuser password (env: DJANGO_SUPERUSER_PASSWORD, default: Admin@1234)",
        )
        parser.add_argument(
            "--first-name",
            dest="first_name",
            default=None,
            help="First name (env: DJANGO_SUPERUSER_FIRSTNAME)",
        )
        parser.add_argument(
            "--last-name",
            dest="last_name",
            default=None,
            help="Last name (env: DJANGO_SUPERUSER_LASTNAME)",
        )

    # ── Main handler ─────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        username   = options["username"]   or os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email      = options["email"]      or os.environ.get("DJANGO_SUPERUSER_EMAIL",    "admin@lumina.com")
        password   = options["password"]   or os.environ.get("DJANGO_SUPERUSER_PASSWORD", "Admin@1234")
        first_name = options["first_name"] or os.environ.get("DJANGO_SUPERUSER_FIRSTNAME", "")
        last_name  = options["last_name"]  or os.environ.get("DJANGO_SUPERUSER_LASTNAME",  "")

        if not password:
            raise CommandError("Password must not be empty.")

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Superuser '{username}' already exists — skipping creation."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Superuser '{username}' created successfully."
            )
        )
