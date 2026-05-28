from django.urls import path

from .ai_judge_views import AIJudgeSubmitView, submit_and_complete_problem
from .judge0_views import (
    Judge0BatchSubmitView,
    Judge0HealthCheckView,
    Judge0LanguagesView,
    Judge0QuickRunView,
    Judge0SubmissionDetailView,
    Judge0SubmitView,
    Judge0SystemInfoView,
)
from .homework_views import (
    AdminHomeworkDetailView,
    AdminHomeworkListCreateView,
    UserHomeworkDetailView,
    UserHomeworkListView,
    UserHomeworkSubmitView,
)
from .personalized_views import PersonalizedExerciseGenerationView
from .qwen_views import QwenChatView, QwenCodeHelpView, QwenTranslateView
from .views import (
    AvatarPresetListView,
    CurrentUserView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    DebugProblemCompletionsView,
    JWTLogoutView,
    LeetCodeProblemDetailView,
    LeetCodeProblemListView,
    LeetCodeProblemStatsView,
    LoginCaptchaView,
    LoginView,
    LogoutView,
    NicknameReviewApproveView,
    NicknameReviewListView,
    NicknameReviewRejectView,
    ProblemCompletionsView,
    RegisterView,
    RegisterWithCodeView,
    SendVerificationCodeView,
    TestView,
    UserActivitiesView,
    UserDetailView,
    UserListView,
    UserRoleUpdateView,
    UserStatsView,
    VerifyCodeView,
)

urlpatterns = [
    path('test/', TestView.as_view(), name='test'),

    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/user/login/', LoginView.as_view(), name='api-user-login'),

    # JWT
    path('auth/jwt/login/', CustomTokenObtainPairView.as_view(), name='jwt-login'),
    path('auth/jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt-refresh'),
    path('auth/jwt/logout/', JWTLogoutView.as_view(), name='jwt-logout'),
    path('auth/jwt/me/', CurrentUserView.as_view(), name='jwt-current-user'),
    path('auth/jwt/avatar-presets/', AvatarPresetListView.as_view(), name='avatar-preset-list'),
    path('auth/captcha/', LoginCaptchaView.as_view(), name='login-captcha'),

    # Email verification
    path('auth/send-verification-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('auth/register-with-code/', RegisterWithCodeView.as_view(), name='register-with-code'),

    # Admin
    path('admin/users/', UserListView.as_view(), name='user-list'),
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('admin/users/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),
    path('admin/nickname-reviews', NicknameReviewListView.as_view(), name='nickname-review-list'),
    path('admin/nickname-reviews/', NicknameReviewListView.as_view(), name='nickname-review-list-slash'),
    path('admin/nickname-reviews/<int:user_id>/approve', NicknameReviewApproveView.as_view(), name='nickname-review-approve'),
    path('admin/nickname-reviews/<int:user_id>/approve/', NicknameReviewApproveView.as_view(), name='nickname-review-approve-slash'),
    path('admin/nickname-reviews/<int:user_id>/reject', NicknameReviewRejectView.as_view(), name='nickname-review-reject'),
    path('admin/nickname-reviews/<int:user_id>/reject/', NicknameReviewRejectView.as_view(), name='nickname-review-reject-slash'),
    path('admin/statistics/users/', UserStatsView.as_view(), name='user-stats'),
    path('admin/activities/', UserActivitiesView.as_view(), name='user-activities'),

    # LeetCode
    path('leetcode/problems/', LeetCodeProblemListView.as_view(), name='leetcode-problem-list'),
    path('leetcode/problems/<int:problem_id>/', LeetCodeProblemDetailView.as_view(), name='leetcode-problem-detail'),
    path('leetcode/stats/', LeetCodeProblemStatsView.as_view(), name='leetcode-stats'),
    path('leetcode/personalized/', PersonalizedExerciseGenerationView.as_view(), name='leetcode-personalized-generation'),

    # User problem status
    path('user/completions/', ProblemCompletionsView.as_view(), name='problem-completions'),
    path('user/personalized-exercises/', PersonalizedExerciseGenerationView.as_view(), name='user-personalized-exercises'),
    path('user/homeworks/', UserHomeworkListView.as_view(), name='user-homework-list'),
    path('user/homeworks/<int:assignment_id>/', UserHomeworkDetailView.as_view(), name='user-homework-detail'),
    path('user/homeworks/<int:assignment_id>/submit/', UserHomeworkSubmitView.as_view(), name='user-homework-submit'),
    path('debug/user/completions/', DebugProblemCompletionsView.as_view(), name='debug-problem-completions'),

    # Admin homework
    path('admin/homeworks/', AdminHomeworkListCreateView.as_view(), name='admin-homework-list-create'),
    path('admin/homeworks/<int:assignment_id>/', AdminHomeworkDetailView.as_view(), name='admin-homework-detail'),

    # Judge0
    path('judge0/languages/', Judge0LanguagesView.as_view(), name='judge0-languages'),
    path('judge0/submit/', Judge0SubmitView.as_view(), name='judge0-submit'),
    path('judge0/batch-submit/', Judge0BatchSubmitView.as_view(), name='judge0-batch-submit'),
    path('judge0/submission/<str:token>/', Judge0SubmissionDetailView.as_view(), name='judge0-submission-detail'),
    path('judge0/system-info/', Judge0SystemInfoView.as_view(), name='judge0-system-info'),
    path('judge0/health/', Judge0HealthCheckView.as_view(), name='judge0-health'),
    path('judge0/run/', Judge0QuickRunView.as_view(), name='judge0-quick-run'),

    # Qwen
    path('ai/chat/', QwenChatView.as_view(), name='qwen-chat'),
    path('ai/code-help/', QwenCodeHelpView.as_view(), name='qwen-code-help'),
    path('ai/translate/', QwenTranslateView.as_view(), name='qwen-translate'),

    # AI judge
    path('ai/judge/submit/', AIJudgeSubmitView.as_view(), name='ai-judge-submit'),
    path('ai/judge/submit-and-complete/', submit_and_complete_problem, name='ai-judge-submit-complete'),
]
