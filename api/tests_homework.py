from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser, HomeworkSubmission, LeetCodeProblem


class HomeworkApiTests(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username="admin_homework",
            email="admin_homework@example.com",
            password="Pass12345",
            role="admin",
        )
        self.student_user = CustomUser.objects.create_user(
            username="student_homework",
            email="student_homework@example.com",
            password="Pass12345",
            role="user",
        )

        self.problem1 = LeetCodeProblem.objects.create(
            problem_id=3001,
            title="Homework Two Sum",
            title_slug="homework-two-sum",
            difficulty="easy",
            tags=["array"],
            acceptance_rate=70.0,
        )
        self.problem2 = LeetCodeProblem.objects.create(
            problem_id=3002,
            title="Homework DFS",
            title_slug="homework-dfs",
            difficulty="medium",
            tags=["graph"],
            acceptance_rate=45.0,
        )

    def _create_homework(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "title": "Week 1 Homework",
            "description": "basic training",
            "start_at": (timezone.now() - timedelta(hours=1)).isoformat(),
            "due_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "is_published": True,
            "allow_late_submission": False,
            "problem_items": [
                {"problem_id": self.problem1.problem_id, "order": 1, "points": 50},
                {"problem_id": self.problem2.problem_id, "order": 2, "points": 50},
            ],
        }
        response = self.client.post(reverse("admin-homework-list-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["data"]["id"]

    def test_admin_can_create_and_update_homework(self):
        homework_id = self._create_homework()

        detail = self.client.get(reverse("admin-homework-detail", args=[homework_id]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail.data["data"]["problem_items"]), 2)

        update_payload = {
            "title": "Week 1 Homework Updated",
            "description": "updated desc",
            "start_at": (timezone.now() - timedelta(hours=2)).isoformat(),
            "due_at": (timezone.now() + timedelta(days=2)).isoformat(),
            "is_published": True,
            "allow_late_submission": True,
            "problem_items": [
                {"problem_id": self.problem1.problem_id, "order": 1, "points": 100},
            ],
        }
        update = self.client.put(reverse("admin-homework-detail", args=[homework_id]), update_payload, format="json")
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["data"]["title"], "Week 1 Homework Updated")
        self.assertEqual(len(update.data["data"]["problem_items"]), 1)

    def test_student_can_view_and_submit_homework(self):
        homework_id = self._create_homework()

        self.client.force_authenticate(user=self.student_user)
        list_response = self.client.get(reverse("user-homework-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_response.data["data"]), 1)

        detail_response = self.client.get(reverse("user-homework-detail", args=[homework_id]))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn("problem_items", detail_response.data["data"])

        submit_response = self.client.post(
            reverse("user-homework-submit", args=[homework_id]),
            {"notes": "finished"},
            format="json",
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertIn(submit_response.data["data"]["status"], ["submitted", "late_submitted"])

        exists = HomeworkSubmission.objects.filter(assignment_id=homework_id, user=self.student_user).exists()
        self.assertTrue(exists)
