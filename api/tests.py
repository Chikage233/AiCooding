from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .avatar_presets import get_avatar_presets
from .models import CustomUser


class AvatarPresetApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="avatar_user",
            email="avatar_user@example.com",
            password="Pass12345",
        )
        self.client.force_authenticate(user=self.user)

    def test_avatar_presets_endpoint_returns_fixed_options(self):
        response = self.client.get(reverse("avatar-preset-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertIn("avatars", response.data["data"])
        self.assertGreater(len(response.data["data"]["avatars"]), 0)

    def test_patch_current_user_accepts_only_preset_avatar(self):
        preset_url = get_avatar_presets()[0]["url"]

        ok_response = self.client.patch(
            reverse("jwt-current-user"),
            {"avatar": preset_url},
            format="json",
        )
        self.assertEqual(ok_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar, preset_url)

        bad_response = self.client.patch(
            reverse("jwt-current-user"),
            {"avatar": "https://example.com/custom-avatar.png"},
            format="json",
        )
        self.assertEqual(bad_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("avatar", bad_response.data["data"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar, preset_url)
