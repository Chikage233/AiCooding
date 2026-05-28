from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .personalization import PersonalizedExerciseService
from .serializers import PersonalizedProblemSerializer


class PersonalizedExerciseGenerationView(APIView):
    """Generate personalized practice problems for current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count_raw = request.query_params.get("count", PersonalizedExerciseService.DEFAULT_COUNT)
        strategy = (
            request.query_params.get("strategy", "balanced") or "balanced"
        ).strip().lower()
        difficulty = request.query_params.get("difficulty")
        focus_tag = request.query_params.get("focus_tag")
        include_completed = self._parse_bool(
            request.query_params.get("include_completed"),
            default=False,
        )

        try:
            count = int(count_raw)
        except (TypeError, ValueError):
            return Response(
                {
                    "code": 400,
                    "message": "count must be an integer",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if count < 1 or count > PersonalizedExerciseService.MAX_COUNT:
            return Response(
                {
                    "code": 400,
                    "message": f"count must be between 1 and {PersonalizedExerciseService.MAX_COUNT}",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if strategy not in PersonalizedExerciseService.VALID_STRATEGIES:
            valid_strategy_text = ", ".join(sorted(PersonalizedExerciseService.VALID_STRATEGIES))
            return Response(
                {
                    "code": 400,
                    "message": f"strategy supports only: {valid_strategy_text}",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if difficulty:
            difficulty = difficulty.strip().lower()
            if difficulty not in PersonalizedExerciseService.VALID_DIFFICULTIES:
                valid_difficulty_text = ", ".join(sorted(PersonalizedExerciseService.VALID_DIFFICULTIES))
                return Response(
                    {
                        "code": 400,
                        "message": f"difficulty supports only: {valid_difficulty_text}",
                        "data": {},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        result = PersonalizedExerciseService.generate_for_user(
            user=request.user,
            count=count,
            strategy=strategy,
            difficulty=difficulty,
            focus_tag=focus_tag,
            include_completed=include_completed,
        )

        serializer = PersonalizedProblemSerializer(
            result["problems"],
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "code": 200,
                "message": "Personalized exercises generated successfully",
                "data": {
                    "recommendations": serializer.data,
                    "profile": result["profile"],
                    "strategy": result["strategy"],
                },
            }
        )

    @staticmethod
    def _parse_bool(value, *, default=False):
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
