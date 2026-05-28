from django.contrib import admin

from .models import (
    CustomUser,
    HomeworkAssignment,
    HomeworkProblem,
    HomeworkSubmission,
    NicknameReviewLog,
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "username",
        "role",
        "nickname_approved",
        "nickname_candidate",
        "nickname_status",
    )
    search_fields = ("email", "username", "nickname_approved", "nickname_candidate")
    list_filter = ("role", "nickname_status", "is_active")


@admin.register(NicknameReviewLog)
class NicknameReviewLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "operator", "action", "nickname_value", "hit_rule", "created_at")
    search_fields = ("user__username", "user__email", "nickname_value", "hit_rule")
    list_filter = ("action", "created_at")


@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_by", "is_published", "start_at", "due_at", "created_at")
    search_fields = ("title",)
    list_filter = ("is_published", "allow_late_submission", "due_at")


@admin.register(HomeworkProblem)
class HomeworkProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment", "problem", "order", "points")
    search_fields = ("assignment__title", "problem__title")
    list_filter = ("assignment",)


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment", "user", "status", "submitted_at", "updated_at")
    search_fields = ("assignment__title", "user__username", "user__email")
    list_filter = ("status", "assignment")
