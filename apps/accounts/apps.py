from django.apps import AppConfig


def _auto_ensure_superuser(sender, **kwargs):
    """Ensure default superuser 'suhani' and sample data exist."""
    from django.contrib.auth.models import User
    from django.core.management import call_command
    try:
        suhani_user = User.objects.filter(username__iexact="suhani").first()
        if not suhani_user:
            call_command('add_sample_data')
        else:
            suhani_user.email = 'suhanimodi7090@gmail.com'
            suhani_user.is_active = True
            suhani_user.is_staff = True
            suhani_user.is_superuser = True
            suhani_user.set_password('Lumina@2025')
            suhani_user.save()
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
