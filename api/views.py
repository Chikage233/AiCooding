# 必须完整导入 DRF 的 APIView 和 Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import login, logout
from .serializers import (UserRegisterSerializer, UserLoginSerializer,
                         UserInfoSerializer, UserRoleUpdateSerializer)
from .models import CustomUser
from django.core.cache import cache
from django.conf import settings
import json
import hashlib
# 必须完整导入 DRF 的 APIView 和 Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.conf import settings
import json
import hashlib
from .serializers import (UserRegisterSerializer, UserLoginSerializer,
                         UserInfoSerializer, UserRoleUpdateSerializer)
from .models import CustomUser

# 保留原有的测试接口
class TestView(APIView):
    # 处理 GET 请求，方法名必须是 get（小写）
    def get(self, request):
        # 返回和前端匹配的格式，无语法错误
        return Response({
            "code": 200,
            "msg": "接口调用成功！",
            "data": {"name": "AI编程辅导系统", "version": "1.0.0"}
        })

# 用户注册接口
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 创建token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "code": 200,
                "msg": "注册成功",
                "data": {
                    "token": token.key,
                    "user": UserInfoSerializer(user).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "code": 400,
            "msg": "注册失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登录接口
class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            # 获取或创建token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "token": token.key,
                    "user": UserInfoSerializer(user).data
                }
            })
        return Response({
            "code": 400,
            "msg": "登录失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登出接口
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 删除用户的token
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({
            "code": 200,
            "msg": "登出成功",
            "data": {}
        })

# 获取用户信息接口（带缓存优化）
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 生成缓存键
        cache_key = f"user_info_{request.user.id}"

        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                "code": 200,
                "msg": "获取用户信息成功（缓存）",
                "data": json.loads(cached_data)
            })

        # 缓存未命中，从数据库获取
        serializer = UserInfoSerializer(request.user)
        response_data = serializer.data

        # 存入缓存（设置过期时间）
        cache.set(cache_key, json.dumps(response_data), timeout=300)  # 5分钟缓存

        return Response({
            "code": 200,
            "msg": "获取用户信息成功",
            "data": response_data
        })

# 清除用户缓存接口
class ClearUserCacheView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cache_key = f"user_info_{request.user.id}"
        cache.delete(cache_key)
        return Response({
            "code": 200,
            "msg": "用户缓存清除成功",
            "data": {}
        })

# 管理员：获取所有用户列表
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 检查是否为管理员
        if not request.user.is_administrator():
            return Response({
                "code": 403,
                "msg": "权限不足，只有管理员可以访问",
                "data": {}
            }, status=status.HTTP_403_FORBIDDEN)

        # 获取查询参数
        role = request.GET.get('role', None)
        department = request.GET.get('department', None)
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        # 过滤用户
        users = CustomUser.objects.all()
        if role:
            users = users.filter(role=role)
        if department:
            users = users.filter(department=department)

        # 分页处理
        total = users.count()
        start = (page - 1) * page_size
        end = start + page_size
        users_page = users[start:end]

        serializer = UserInfoSerializer(users_page, many=True)
        return Response({
            "code": 200,
            "msg": "获取用户列表成功",
            "data": {
                "users": serializer.data,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        })

# 管理员：批量更新用户状态
class BatchUserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # 检查是否为管理员
        if not request.user.is_administrator():
            return Response({
                "code": 403,
                "msg": "权限不足，只有管理员可以批量操作",
                "data": {}
            }, status=status.HTTP_403_FORBIDDEN)

        user_ids = request.data.get('user_ids', [])
        action = request.data.get('action', '')  # 'activate', 'deactivate', 'delete'

        if not user_ids or not action:
            return Response({
                "code": 400,
                "msg": "请提供用户ID列表和操作类型",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        users = CustomUser.objects.filter(id__in=user_ids)
        affected_count = 0

        if action == 'activate':
            affected_count = users.update(is_active=True)
        elif action == 'deactivate':
            affected_count = users.update(is_active=False)
        elif action == 'delete':
            affected_count = users.delete()[0]

        # 清除相关缓存
        for user_id in user_ids:
            cache_key = f"user_info_{user_id}"
            cache.delete(cache_key)

        return Response({
            "code": 200,
            "msg": f"批量操作成功，影响 {affected_count} 个用户",
            "data": {"affected_count": affected_count}
        })

# 获取系统健康状态（监控接口）
class SystemHealthView(APIView):
    def get(self, request):
        # 检查数据库连接
        try:
            db_status = "healthy" if CustomUser.objects.first() is not None else "unhealthy"
        except Exception:
            db_status = "unhealthy"

        # 检查Redis连接
        try:
            cache.set("health_check", "ok", timeout=1)
            redis_status = "healthy" if cache.get("health_check") == "ok" else "unhealthy"
        except Exception:
            redis_status = "unhealthy"

        return Response({
            "code": 200,
            "msg": "系统健康检查",
            "data": {
                "database": db_status,
                "redis_cache": redis_status,
                "timestamp": timezone.now().isoformat()
            }
        })


# 保留原有的测试接口
class TestView(APIView):
    # 处理 GET 请求，方法名必须是 get（小写）
    def get(self, request):
        # 返回和前端匹配的格式，无语法错误
        return Response({
            "code": 200,
            "msg": "接口调用成功！",
            "data": {"name": "AI编程辅导系统", "version": "1.0.0"}
        })

# 用户注册接口
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 创建token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "code": 200,
                "msg": "注册成功",
                "data": {
                    "token": token.key,
                    "user": UserInfoSerializer(user).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "code": 400,
            "msg": "注册失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登录接口
class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            # 获取或创建token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "token": token.key,
                    "user": UserInfoSerializer(user).data
                }
            })
        return Response({
            "code": 400,
            "msg": "登录失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登出接口
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 删除用户的token
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({
            "code": 200,
            "msg": "登出成功",
            "data": {}
        })


# ... existing code ...

# 获取用户信息接口（带缓存优化）
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 生成缓存键
        cache_key = f"user_info_{request.user.id}"

        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                "code": 200,
                "msg": "获取用户信息成功（缓存）",
                "data": json.loads(cached_data)
            })

        # 缓存未命中，从数据库获取
        serializer = UserInfoSerializer(request.user)
        response_data = serializer.data

        # 存入缓存（设置过期时间）
        cache.set(cache_key, json.dumps(response_data), timeout=300)  # 5分钟缓存

        return Response({
            "code": 200,
            "msg": "获取用户信息成功",
            "data": response_data
        })


# 清除用户缓存接口
class ClearUserCacheView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cache_key = f"user_info_{request.user.id}"
        cache.delete(cache_key)
        return Response({
            "code": 200,
            "msg": "用户缓存清除成功",
            "data": {}
        })

# 管理员：获取所有用户列表
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 检查是否为管理员
        if not request.user.is_administrator():
            return Response({
                "code": 403,
                "msg": "权限不足，只有管理员可以访问",
                "data": {}
            }, status=status.HTTP_403_FORBIDDEN)

        # 获取查询参数
        role = request.GET.get('role', None)
        department = request.GET.get('department', None)

        # 过滤用户
        users = CustomUser.objects.all()
        if role:
            users = users.filter(role=role)
        if department:
            users = users.filter(department=department)

        serializer = UserInfoSerializer(users, many=True)
        return Response({
            "code": 200,
            "msg": "获取用户列表成功",
            "data": serializer.data
        })

# 管理员：更新用户角色
class UserRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id):
        # 检查是否为管理员
        if not request.user.is_administrator():
            return Response({
                "code": 403,
                "msg": "权限不足，只有管理员可以修改用户角色",
                "data": {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "用户不存在",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "code": 200,
                "msg": "用户角色更新成功",
                "data": UserInfoSerializer(user).data
            })
        return Response({
            "code": 400,
            "msg": "更新失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 获取角色统计信息（管理员专用）
class RoleStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 检查是否为管理员
        if not request.user.is_administrator():
            return Response({
                "code": 403,
                "msg": "权限不足，只有管理员可以访问",
                "data": {}
            }, status=status.HTTP_403_FORBIDDEN)

        # 统计各角色用户数量
        stats = {
            'total_users': CustomUser.objects.count(),
            'students': CustomUser.objects.filter(role='student').count(),
            'teachers': CustomUser.objects.filter(role='teacher').count(),
            'administrators': CustomUser.objects.filter(role='admin').count(),
        }

        return Response({
            "code": 200,
            "msg": "获取角色统计成功",
            "data": stats
        })

