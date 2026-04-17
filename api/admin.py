from django.contrib import admin

from .models import CustomUser, NicknameReviewLog


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
