# 必须导入 path 和自定义的 View
from django.urls import path
from .views import (TestView, RegisterView, LoginView, LogoutView,
                    UserListView, UserRoleUpdateView,UserDetailView,
                    UserStatsView, CustomTokenObtainPairView, CustomTokenRefreshView,
                    CurrentUserView, JWTLogoutView,
                    LeetCodeProblemListView, LeetCodeProblemDetailView, LeetCodeProblemStatsView)

# URL 规则列表
urlpatterns = [
    path('test/', TestView.as_view(), name='test'),
    # 传统认证接口（保持兼容性）
    path('auth/register/', RegisterView.as_view(), name='register'),  # 添加$表示精确匹配
    path('auth/login/', LoginView.as_view(), name='login'),              # 登录接口
    path('auth/logout/', LogoutView.as_view(), name='logout'),            # 登出接口


    # JWT认证接口（推荐使用）
    path('auth/jwt/login/', CustomTokenObtainPairView.as_view(), name='jwt-login'),# JWT登录
    path('auth/jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt-refresh'),          # JWT刷新
    path('auth/jwt/logout/', JWTLogoutView.as_view(), name='jwt-logout'),                     # JWT登出
    path('auth/jwt/me/', CurrentUserView.as_view(), name='jwt-current-user'),                 # 获取当前用户


    # 管理员专用接口
    path('admin/users/', UserListView.as_view(), name='user-list'),       # 用户列表
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),  # 用户详情
    path('admin/users/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),  # 更新用户角色
    path('admin/statistics/users/', UserStatsView.as_view(), name='user-stats'),  # 用户统计


    # LeetCode题目接口
    path('leetcode/problems/', LeetCodeProblemListView.as_view(), name='leetcode-problem-list'),  # 题目列表
    path('leetcode/problems/<int:problem_id>/', LeetCodeProblemDetailView.as_view(), name='leetcode-problem-detail'),  # 题目详情
    path('leetcode/stats/', LeetCodeProblemStatsView.as_view(), name='leetcode-stats'),  # 题目统计
]

