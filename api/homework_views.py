from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HomeworkAssignment, HomeworkProblem, HomeworkSubmission, LeetCodeProblem
from .serializers import (
    HomeworkAssignmentDetailSerializer,
    HomeworkAssignmentListSerializer,
    HomeworkCreateUpdateSerializer,
    HomeworkSubmissionSerializer,
)


class AdminHomeworkListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        queryset = HomeworkAssignment.objects.all().annotate(
            problem_count=Count("homework_problems", distinct=True),
            submission_count=Count("submissions", distinct=True),
        )
        serializer = HomeworkAssignmentListSerializer(queryset, many=True)
        return Response({
            "code": 200,
            "message": "获取作业列表成功",
            "data": serializer.data,
        })

    def post(self, request):
        serializer = HomeworkCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "code": 400,
                "message": "参数错误",
                "data": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        try:
            with transaction.atomic():
                assignment = HomeworkAssignment.objects.create(
                    title=payload["title"],
                    description=payload.get("description", ""),
                    created_by=request.user,
                    start_at=payload["start_at"],
                    due_at=payload["due_at"],
                    is_published=payload.get("is_published", False),
                    allow_late_submission=payload.get("allow_late_submission", False),
                )
                create_homework_problem_links(assignment, payload["problem_items"])
        except ValueError as exc:
            return Response({
                "code": 400,
                "message": str(exc),
                "data": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        detail = HomeworkAssignmentDetailSerializer(assignment)
        return Response({
            "code": 200,
            "message": "创建作业成功",
            "data": detail.data,
        })


class AdminHomeworkDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, assignment_id):
        assignment = HomeworkAssignment.objects.filter(id=assignment_id).first()
        if not assignment:
            return Response({"code": 404, "message": "作业不存在", "data": {}}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "code": 200,
            "message": "获取作业详情成功",
            "data": HomeworkAssignmentDetailSerializer(assignment).data,
        })

    def put(self, request, assignment_id):
        assignment = HomeworkAssignment.objects.filter(id=assignment_id).first()
        if not assignment:
            return Response({"code": 404, "message": "作业不存在", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        serializer = HomeworkCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "code": 400,
                "message": "参数错误",
                "data": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        try:
            with transaction.atomic():
                assignment.title = payload["title"]
                assignment.description = payload.get("description", "")
                assignment.start_at = payload["start_at"]
                assignment.due_at = payload["due_at"]
                assignment.is_published = payload.get("is_published", False)
                assignment.allow_late_submission = payload.get("allow_late_submission", False)
                assignment.save()
                assignment.homework_problems.all().delete()
                create_homework_problem_links(assignment, payload["problem_items"])
        except ValueError as exc:
            return Response({
                "code": 400,
                "message": str(exc),
                "data": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "code": 200,
            "message": "更新作业成功",
            "data": HomeworkAssignmentDetailSerializer(assignment).data,
        })

    def delete(self, request, assignment_id):
        assignment = HomeworkAssignment.objects.filter(id=assignment_id).first()
        if not assignment:
            return Response({"code": 404, "message": "作业不存在", "data": {}}, status=status.HTTP_404_NOT_FOUND)
        assignment.delete()
        return Response({
            "code": 200,
            "message": "删除作业成功",
            "data": {},
        })


class UserHomeworkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        queryset = HomeworkAssignment.objects.filter(is_published=True).order_by("-created_at")

        items = []
        for assignment in queryset:
            submission = HomeworkSubmission.objects.filter(assignment=assignment, user=request.user).first()
            if submission:
                submit_status = submission.status
                submitted_at = submission.submitted_at.isoformat() if submission.submitted_at else None
                notes = submission.notes
            else:
                submit_status = infer_submission_status(assignment, now)
                submitted_at = None
                notes = ""

            items.append({
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "start_at": assignment.start_at.isoformat(),
                "due_at": assignment.due_at.isoformat(),
                "is_published": assignment.is_published,
                "allow_late_submission": assignment.allow_late_submission,
                "problem_count": assignment.homework_problems.count(),
                "submission_status": submit_status,
                "submitted_at": submitted_at,
                "notes": notes,
            })

        return Response({
            "code": 200,
            "message": "获取作业列表成功",
            "data": items,
        })


class UserHomeworkDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        assignment = HomeworkAssignment.objects.filter(id=assignment_id, is_published=True).first()
        if not assignment:
            return Response({"code": 404, "message": "作业不存在", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        detail = HomeworkAssignmentDetailSerializer(assignment).data
        submission = HomeworkSubmission.objects.filter(assignment=assignment, user=request.user).first()
        if submission:
            detail["submission"] = HomeworkSubmissionSerializer(submission).data
        else:
            detail["submission"] = {
                "status": infer_submission_status(assignment, timezone.now()),
                "submitted_at": None,
                "notes": "",
            }

        return Response({
            "code": 200,
            "message": "获取作业详情成功",
            "data": detail,
        })


class UserHomeworkSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        assignment = HomeworkAssignment.objects.filter(id=assignment_id, is_published=True).first()
        if not assignment:
            return Response({"code": 404, "message": "作业不存在", "data": {}}, status=status.HTTP_404_NOT_FOUND)

        notes = str(request.data.get("notes", "")).strip()
        now = timezone.now()
        is_late = now > assignment.due_at

        if is_late and not assignment.allow_late_submission:
            return Response({
                "code": 400,
                "message": "作业已截止，不能提交",
                "data": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        status_value = "late_submitted" if is_late else "submitted"
        submission, _ = HomeworkSubmission.objects.get_or_create(
            assignment=assignment,
            user=request.user,
            defaults={"status": status_value, "notes": notes, "submitted_at": now},
        )
        if submission.status not in {"submitted", "late_submitted"}:
            submission.status = status_value
        submission.notes = notes
        submission.submitted_at = now
        submission.save()

        return Response({
            "code": 200,
            "message": "作业提交成功",
            "data": HomeworkSubmissionSerializer(submission).data,
        })


def infer_submission_status(assignment, now):
    if now < assignment.start_at:
        return "not_started"
    if now <= assignment.due_at:
        return "in_progress"
    return "not_started" if assignment.allow_late_submission else "expired"


def create_homework_problem_links(assignment, problem_items):
    problem_ids = [item["problem_id"] for item in problem_items]
    problems = LeetCodeProblem.objects.filter(problem_id__in=problem_ids)
    problem_map = {p.problem_id: p for p in problems}

    missing = [pid for pid in problem_ids if pid not in problem_map]
    if missing:
        raise ValueError(f"problem ids not found: {missing}")

    links = []
    for item in problem_items:
        links.append(
            HomeworkProblem(
                assignment=assignment,
                problem=problem_map[item["problem_id"]],
                order=item.get("order", 0),
                points=item.get("points", 100),
            )
        )
    HomeworkProblem.objects.bulk_create(links)
