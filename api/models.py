from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Application user model."""

    ROLE_CHOICES = (
        ("user", "user"),
        ("admin", "admin"),
    )
    GENDER_CHOICES = (
        ("male", "male"),
        ("female", "female"),
        ("other", "other"),
    )
    NICKNAME_STATUS_CHOICES = (
        ("approved", "approved"),
        ("pending", "pending"),
        ("rejected", "rejected"),
    )

    email = models.EmailField(unique=True, verbose_name="email")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="phone")
    avatar = models.URLField(blank=True, null=True, verbose_name="avatar")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user", verbose_name="role")
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="department")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="nickname")
    nickname_approved = models.CharField(max_length=20, blank=True, null=True, verbose_name="nickname_approved")
    nickname_candidate = models.CharField(max_length=20, blank=True, null=True, verbose_name="nickname_candidate")
    nickname_status = models.CharField(
        max_length=10,
        choices=NICKNAME_STATUS_CHOICES,
        default="approved",
        verbose_name="nickname_status",
    )
    nickname_reject_reason = models.CharField(max_length=255, blank=True, default="", verbose_name="nickname_reject_reason")
    nickname_reviewed_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_nicknames",
        verbose_name="nickname_reviewed_by",
    )
    nickname_reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="nickname_reviewed_at")
    bio = models.TextField(blank=True, default="", verbose_name="bio")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="gender")
    birthday = models.DateField(blank=True, null=True, verbose_name="birthday")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated_at")

    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into this admin site.",
        verbose_name="staff status",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "custom_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Keep staff flag aligned with app-level role.
        self.is_staff = self.role == "admin"
        # Keep legacy nickname field in sync with approved nickname for backward compatibility.
        if self.nickname_approved:
            self.nickname = self.nickname_approved
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.add("is_staff")
            if self.nickname_approved:
                update_fields.add("nickname")
            kwargs["update_fields"] = list(update_fields)
        super().save(*args, **kwargs)

    def is_user(self):
        return self.role == "user"

    def is_administrator(self):
        return self.role == "admin"

    @property
    def display_name(self):
        if self.nickname_approved:
            return self.nickname_approved
        return self.username


class LeetCodeProblem(models.Model):
    """LeetCode problem model."""

    DIFFICULTY_CHOICES = (
        ("easy", "easy"),
        ("medium", "medium"),
        ("hard", "hard"),
    )

    problem_id = models.IntegerField(unique=True, verbose_name="problem_id")
    title = models.CharField(max_length=200, verbose_name="title")
    title_slug = models.SlugField(max_length=200, unique=True, verbose_name="title_slug")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name="difficulty")
    is_premium = models.BooleanField(default=False, verbose_name="is_premium")
    content = models.TextField(blank=True, verbose_name="content")
    acceptance_rate = models.FloatField(default=0.0, verbose_name="acceptance_rate")
    submission_count = models.IntegerField(default=0, verbose_name="submission_count")
    accepted_count = models.IntegerField(default=0, verbose_name="accepted_count")
    tags = models.JSONField(default=list, blank=True, verbose_name="tags")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated_at")

    class Meta:
        db_table = "leetcode_problem"
        verbose_name = "leetcode_problem"
        verbose_name_plural = "leetcode_problems"
        ordering = ["problem_id"]

    def __str__(self):
        return f"{self.problem_id}. {self.title}"

    @property
    def url(self):
        return f"https://leetcode.cn/problems/{self.title_slug}/"


class ProblemTag(models.Model):
    """Problem tag model."""

    name = models.CharField(max_length=50, unique=True, verbose_name="name")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")

    class Meta:
        db_table = "problem_tag"
        verbose_name = "problem_tag"
        verbose_name_plural = "problem_tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserActivity(models.Model):
    """User activity tracking."""

    ACTIVITY_TYPES = (
        ("login", "login"),
        ("view_problem", "view_problem"),
        ("submit_solution", "submit_solution"),
        ("complete_problem", "complete_problem"),
        ("profile_update", "profile_update"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="user")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name="activity_type")
    problem = models.ForeignKey(
        LeetCodeProblem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="problem",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="ip_address")
    user_agent = models.TextField(blank=True, verbose_name="user_agent")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")

    class Meta:
        db_table = "user_activity"
        verbose_name = "user_activity"
        verbose_name_plural = "user_activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["activity_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.created_at}"


class ProblemCompletion(models.Model):
    """Problem completion status per user."""

    COMPLETION_STATUS = (
        ("not_started", "not_started"),
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("failed", "failed"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="user")
    problem = models.ForeignKey(LeetCodeProblem, on_delete=models.CASCADE, verbose_name="problem")
    status = models.CharField(
        max_length=15,
        choices=COMPLETION_STATUS,
        default="not_started",
        verbose_name="status",
    )
    attempts = models.IntegerField(default=0, verbose_name="attempts")
    last_attempted = models.DateTimeField(null=True, blank=True, verbose_name="last_attempted")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="completed_at")
    solution_code = models.TextField(blank=True, verbose_name="solution_code")
    notes = models.TextField(blank=True, verbose_name="notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated_at")

    class Meta:
        db_table = "problem_completion"
        verbose_name = "problem_completion"
        verbose_name_plural = "problem_completions"
        unique_together = ["user", "problem"]
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["problem", "status"]),
            models.Index(fields=["user", "-completed_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class EmailVerificationCode(models.Model):
    """Email verification code."""

    email = models.EmailField(max_length=254, verbose_name="email")
    code = models.CharField(max_length=6, verbose_name="code")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")
    expires_at = models.DateTimeField(verbose_name="expires_at")
    is_used = models.BooleanField(default=False, verbose_name="is_used")

    class Meta:
        verbose_name = "email_verification_code"
        verbose_name_plural = "email_verification_codes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.code}"

    @classmethod
    def generate_code(cls, email):
        import random
        import string

        code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=5)
        return cls.objects.create(
            email=email,
            code=code,
            expires_at=expires_at,
        )

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class NicknameReviewLog(models.Model):
    """Nickname validation/review audit log."""

    ACTION_CHOICES = (
        ("submit", "submit"),
        ("approve", "approve"),
        ("reject", "reject"),
        ("validation_fail", "validation_fail"),
        ("rate_limited", "rate_limited"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="nickname_review_logs", verbose_name="user")
    operator = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operated_nickname_review_logs",
        verbose_name="operator",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="action")
    nickname_value = models.CharField(max_length=20, blank=True, default="", verbose_name="nickname_value")
    hit_rule = models.CharField(max_length=64, blank=True, default="", verbose_name="hit_rule")
    message = models.CharField(max_length=255, blank=True, default="", verbose_name="message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created_at")

    class Meta:
        db_table = "nickname_review_log"
        verbose_name = "nickname_review_log"
        verbose_name_plural = "nickname_review_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.action}:{self.nickname_value}"
