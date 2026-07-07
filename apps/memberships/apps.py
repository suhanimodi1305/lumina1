from django.apps import AppConfig


class MembershipsConfig(AppConfig):
    name = 'apps.memberships'

    def ready(self):
        import apps.memberships.signals  # noqa
