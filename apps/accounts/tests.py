from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ManualLoginTests(TestCase):
    def test_users_can_login_with_typed_username_and_password(self):
        for flags in (
            {},
            {'is_staff': True},
            {'is_staff': True, 'is_superuser': True},
        ):
            user = User.objects.create_user(
                username=f'user_{len(User.objects.all())}',
                email=f'user_{len(User.objects.all())}@example.com',
                password='TypedPassword123!',
                **flags,
            )

            response = self.client.post(
                reverse('accounts:login'),
                {'username': user.username, 'password': 'TypedPassword123!'},
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, '/me/')
            self.client.get(reverse('accounts:logout'))

    def test_users_can_login_with_typed_email_and_password(self):
        User.objects.create_user(
            username='email_user',
            email='EmailUser@example.com',
            password='TypedPassword123!',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'username': ' emailuser@EXAMPLE.COM ', 'password': 'TypedPassword123!'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/me/')
