from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser, LeetCodeProblem, ProblemCompletion


class PersonalizedExerciseApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="persona_user",
            email="persona_user@example.com",
            password="Pass12345",
        )

        self.problem_done = self._create_problem(
            problem_id=1001,
            title="Two Sum Lite",
            title_slug="two-sum-lite",
            difficulty="easy",
            tags=["array", "hash table"],
            acceptance_rate=75,
        )
        self.problem_retry = self._create_problem(
            problem_id=1002,
            title="Graph Traverse",
            title_slug="graph-traverse",
            difficulty="medium",
            tags=["graph", "dfs"],
            acceptance_rate=45,
        )
        self.problem_in_progress = self._create_problem(
            problem_id=1003,
            title="Graph Path",
            title_slug="graph-path",
            difficulty="medium",
            tags=["graph", "bfs"],
            acceptance_rate=52,
        )
        self.problem_new_easy = self._create_problem(
            problem_id=1004,
            title="String Window",
            title_slug="string-window",
            difficulty="easy",
            tags=["string", "two pointers"],
            acceptance_rate=68,
        )
        self.problem_new_hard = self._create_problem(
            problem_id=1005,
            title="DP Split",
            title_slug="dp-split",
            difficulty="hard",
            tags=["dp", "prefix sum"],
            acceptance_rate=35,
        )

        ProblemCompletion.objects.create(
            user=self.user,
            problem=self.problem_done,
            status="completed",
            attempts=1,
        )
        ProblemCompletion.objects.create(
            user=self.user,
            problem=self.problem_retry,
            status="failed",
            attempts=5,
        )
        ProblemCompletion.objects.create(
            user=self.user,
            problem=self.problem_in_progress,
            status="in_progress",
            attempts=2,
        )

        self.endpoint = reverse("leetcode-personalized-generation")

    def _create_problem(self, *, problem_id, title, title_slug, difficulty, tags, acceptance_rate):
        return LeetCodeProblem.objects.create(
            problem_id=problem_id,
            title=title,
            title_slug=title_slug,
            difficulty=difficulty,
            tags=tags,
            acceptance_rate=acceptance_rate,
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.endpoint)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_default_generation_excludes_completed_problems(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.endpoint, {"count": 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)

        recommended_ids = {item["problem_id"] for item in response.data["data"]["recommendations"]}
        self.assertNotIn(self.problem_done.problem_id, recommended_ids)

        first_item = response.data["data"]["recommendations"][0]
        self.assertIn("recommendation_reason", first_item)
        self.assertIn("match_score", first_item)
        self.assertIn("strategy", response.data["data"])
        self.assertIn("profile", response.data["data"])

    def test_review_strategy_prioritizes_retry_problem(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.endpoint, {"strategy": "review", "count": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        top_item = response.data["data"]["recommendations"][0]
        self.assertEqual(top_item["problem_id"], self.problem_retry.problem_id)
        self.assertEqual(top_item["recommendation_type"], "retry")

    def test_focus_tag_filters_recommendations(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.endpoint, {"focus_tag": "dp", "count": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recommendations = response.data["data"]["recommendations"]
        self.assertGreater(len(recommendations), 0)
        for item in recommendations:
            normalized_tags = {tag.lower() for tag in item["tags"]}
            self.assertIn("dp", normalized_tags)

    def test_invalid_query_param_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.endpoint, {"difficulty": "unknown"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], 400)
