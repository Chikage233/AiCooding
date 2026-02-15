# 必须导入 path 和自定义的 View
from django.urls import path
from .views import (TestView, RegisterView, LoginView, LogoutView, UserInfoView,
                   ClearUserCacheView, UserListView, UserRoleUpdateView,
                   RoleStatisticsView, BatchUserUpdateView, SystemHealthView)

# URL 规则列表
urlpatterns = [
    path('test/', TestView.as_view(), name='test'),

    # 用户认证接口
    path('auth/register/', RegisterView.as_view(), name='register'),      # 注册接口
    path('auth/login/', LoginView.as_view(), name='login'),              # 登录接口
    path('auth/logout/', LogoutView.as_view(), name='logout'),            # 登出接口
    path('auth/userinfo/', UserInfoView.as_view(), name='userinfo'),      # 用户信息接口
    path('auth/cache/clear/', ClearUserCacheView.as_view(), name='clear-cache'),  # 清除缓存

    # 管理员专用接口
    path('admin/users/', UserListView.as_view(), name='user-list'),       # 用户列表
    path('admin/users/<int:user_id>/role/', UserRoleUpdateView.as_view(), name='user-role-update'),  # 更新用户角色
    path('admin/users/batch/', BatchUserUpdateView.as_view(), name='batch-user-update'),  # 批量操作
    path('admin/statistics/roles/', RoleStatisticsView.as_view(), name='role-statistics'),  # 角色统计

    # 系统监控接口
    path('system/health/', SystemHealthView.as_view(), name='system-health'),  # 系统健康检查
]

