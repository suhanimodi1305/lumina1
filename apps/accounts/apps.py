from django.apps import AppConfig


def _auto_ensure_superuser(sender, **kwargs):
    """Ensure default superuser 'suhani' exists with password 'Lumina@2025'."""
    import os
    from django.contrib.auth.models import User
    try:
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME") or "suhani"
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL") or "suhani@example.com"
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD") or "Lumina@2025"

        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
        else:
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
    except Exception:
        pass


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Accounts'

    def ready(self):
        import apps.accounts.signals  # noqa: F401 — connects user_logged_in signal
        from django.db.models.signals import post_migrate
        post_migrate.connect(_auto_ensure_superuser, sender=self)
        try:
            _auto_ensure_superuser(sender=self)
        except Exception:
            pass
