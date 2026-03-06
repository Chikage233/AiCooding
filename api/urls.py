# 必须导入 path 和自定义的 View
from django.urls import path
from .views import (TestView, RegisterView, LoginView, LogoutView,
                    UserListView, UserRoleUpdateView,UserDetailView,
                    UserStatsView, CustomTokenObtainPairView, CustomTokenRefreshView,
                    CurrentUserView, JWTLogoutView,
                    LeetCodeProblemListView, LeetCodeProblemDetailView, LeetCodeProblemStatsView,
                    UserActivitiesView, ProblemCompletionsView,
                    # 添加验证码相关视图
                    SendVerificationCodeView, VerifyCodeView, RegisterWithCodeView)
# 导入 Judge0 相关视图
from .judge0_views import (
    Judge0LanguagesView,
    Judge0SubmitView,
    Judge0BatchSubmitView,
    Judge0SubmissionDetailView,
    Judge0SystemInfoView,
    Judge0HealthCheckView,
    Judge0QuickRunView
)

# URL 规则列表
urlpatterns = [
    path('test/', TestView.as_view(), name='test'),
    # 传统认证接口（保持兼容性）
    path('auth/register/', RegisterView.as_view(), name='register'),  # 添加$表示精确匹配
    path('auth/login/', LoginView.as_view(), name='login'),              # 登录接口
    path('auth/logout/', LogoutView.as_view(), name='logout'),            # 登出接口
    
    # 前端期望的登录接口路径 (兼容旧版)
    path('api/user/login/', LoginView.as_view(), name='api-user-login'),  # 前端使用的登录接口

    # JWT认证接口（推荐使用）
    path('auth/jwt/login/', CustomTokenObtainPairView.as_view(), name='jwt-login'),# JWT登录
    path('auth/jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt-refresh'),          # JWT刷新
    path('auth/jwt/logout/', JWTLogoutView.as_view(), name='jwt-logout'),                     # JWT登出
    path('auth/jwt/me/', CurrentUserView.as_view(), name='jwt-current-user'),                 # 获取当前用户

    # 验证码相关接口
    path('auth/send-verification-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('auth/register-with-code/', RegisterWithCodeView.as_view(), name='register-with-code'),

    # 管理员专用接口
    path('admin/users/', UserListView.as_view(), name='user-list'),       # 用户列表
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),  # 用户详情
    path('admin/users/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),  # 更新用户角色
    path('admin/statistics/users/', UserStatsView.as_view(), name='user-stats'),  # 用户统计
    path('admin/activities/', UserActivitiesView.as_view(), name='user-activities'),  # 用户活动记录

    # LeetCode题目接口
    path('leetcode/problems/', LeetCodeProblemListView.as_view(), name='leetcode-problem-list'),  # 题目列表
    path('leetcode/problems/<int:problem_id>/', LeetCodeProblemDetailView.as_view(), name='leetcode-problem-detail'),  # 题目详情
    path('leetcode/stats/', LeetCodeProblemStatsView.as_view(), name='leetcode-stats'),  # 题目统计
    
    # 用户题目完成状态接口
    path('user/completions/', ProblemCompletionsView.as_view(), name='problem-completions'),  # 题目完成状态
    
    # ==================== Judge0 代码判题接口 ====================
    # 获取支持的编程语言列表
    path('judge0/languages/', Judge0LanguagesView.as_view(), name='judge0-languages'),
    # 提交代码执行 (完整参数版本)
    path('judge0/submit/', Judge0SubmitView.as_view(), name='judge0-submit'),
    # 批量提交代码
    path('judge0/batch-submit/', Judge0BatchSubmitView.as_view(), name='judge0-batch-submit'),
    # 获取提交详情
    path('judge0/submission/<str:token>/', Judge0SubmissionDetailView.as_view(), name='judge0-submission-detail'),
    # 获取系统信息
    path('judge0/system-info/', Judge0SystemInfoView.as_view(), name='judge0-system-info'),
    # 健康检查
    path('judge0/health/', Judge0HealthCheckView.as_view(), name='judge0-health'),
    # 快速运行代码 (简化版)
    path('judge0/run/', Judge0QuickRunView.as_view(), name='judge0-quick-run'),
]