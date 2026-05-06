from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='12345678')

    def test_login_success(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'tester', 'password': '12345678'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
