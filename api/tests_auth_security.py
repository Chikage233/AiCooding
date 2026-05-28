from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser, EmailVerificationCode


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    EMAIL_VERIFICATION_SEND_COOLDOWN_SECONDS=60,
    EMAIL_VERIFICATION_MAX_SENDS_PER_HOUR_PER_EMAIL=5,
    EMAIL_VERIFICATION_MAX_SENDS_PER_HOUR_PER_IP=20,
    EMAIL_VERIFICATION_VERIFY_WINDOW_SECONDS=300,
    EMAIL_VERIFICATION_MAX_VERIFY_ATTEMPTS_PER_EMAIL=2,
    EMAIL_VERIFICATION_MAX_VERIFY_ATTEMPTS_PER_IP=5,
)
class AuthSecurityApiTests(APITestCase):
    def test_public_register_cannot_create_admin(self):
        payload = {
            "username": "new_user_1",
            "email": "new_user_1@example.com",
            "password": "Pass12345!",
            "password_confirm": "Pass12345!",
            "role": "admin",
        }

        response = self.client.post(reverse("register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CustomUser.objects.filter(email="new_user_1@example.com").exists())

    def test_public_register_forces_normal_user(self):
        payload = {
            "username": "new_user_2",
            "email": "new_user_2@example.com",
            "password": "Pass12345!",
            "password_confirm": "Pass12345!",
            "role": "user",
        }

        response = self.client.post(reverse("register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = CustomUser.objects.get(email="new_user_2@example.com")
        self.assertEqual(created.role, "user")
        self.assertFalse(created.is_superuser)

    def test_register_with_code_cannot_create_admin(self):
        email = "new_user_3@example.com"
        EmailVerificationCode.objects.create(
            email=email,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=5),
            is_used=False,
        )
        payload = {
            "username": "new_user_3",
            "email": email,
            "password": "Pass12345!",
            "password_confirm": "Pass12345!",
            "verification_code": "123456",
            "role": "admin",
        }

        response = self.client.post(reverse("register-with-code"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CustomUser.objects.filter(email=email).exists())

    @patch("api.services.send_verification_code", return_value=True)
    def test_send_verification_code_is_rate_limited(self, _mock_send):
        payload = {"email": "fresh_mail@example.com"}

        first = self.client.post(reverse("send-verification-code"), payload, format="json")
        second = self.client.post(reverse("send-verification-code"), payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_verify_code_is_locked_after_failed_attempts(self):
        payload = {"email": "victim@example.com", "code": "000000"}

        first = self.client.post(reverse("verify-code"), payload, format="json")
        second = self.client.post(reverse("verify-code"), payload, format="json")
        third = self.client.post(reverse("verify-code"), payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(third.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class PromoteUserCommandTests(TestCase):
    def test_promote_user_command_upgrades_role(self):
        user = CustomUser.objects.create_user(
            username="promote_me",
            email="promote_me@example.com",
            password="Pass12345!",
            role="user",
        )

        stdout = StringIO()
        call_command("promote_user", email=user.email, stdout=stdout)
        user.refresh_from_db()

        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertIn("Promoted user", stdout.getvalue())

    def test_promote_user_command_can_enable_superuser(self):
        user = CustomUser.objects.create_user(
            username="promote_super",
            email="promote_super@example.com",
            password="Pass12345!",
            role="user",
        )

        call_command("promote_user", username=user.username, superuser=True)
        user.refresh_from_db()

        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

