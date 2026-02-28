# 必须完整导入 DRF 的 APIView 和 Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token  # 重要：添加这行
from django.contrib.auth import login, logout
from .serializers import (UserRegisterSerializer, UserLoginSerializer,
                         UserInfoSerializer, UserRoleUpdateSerializer,
                         LeetCodeProblemSerializer, LeetCodeProblemListSerializer)
from .models import CustomUser, LeetCodeProblem, ProblemTag
from django.db.models import Count, Q
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import json
import hashlib
from rest_framework_simplejwt.views import TokenObtainPairView

# JWT相关导入
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

# 自定义JWT序列化器
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 添加自定义声明
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 添加用户信息到响应中
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'role_display': user.get_role_display(),
            'is_active': user.is_active
        }
        return data


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """支持邮箱登录的JWT序列化器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 修改字段名为email而不是username
        self.fields['email'] = serializers.EmailField()
        # 删除原来的username字段
        if 'username' in self.fields:
            del self.fields['username']

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 添加自定义声明
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        # 直接使用email进行认证，不转换字段名
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # 使用Django的authenticate函数进行认证
            from django.contrib.auth import authenticate
            user = authenticate(email=email, password=password)

            if not user:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('邮箱或密码错误')

            # 设置用户对象
            self.user = user

            # 生成token数据
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)

            # 添加用户信息到响应中
            data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'role_display': user.get_role_display(),
                'is_active': user.is_active
            }

            return data
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('请提供邮箱和密码')


# 自定义JWT登录视图
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer  # 使用支持邮箱的序列化器

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {
                'code': 200,
                'message': '登录成功',
                'data': response.data
            }
        else:
            response.data = {
                'code': 401,
                'message': '登录失败',
                'data': response.data
            }
        return response


# JWT刷新令牌视图
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {
                'code': 200,
                'message': '令牌刷新成功',
                'data': response.data
            }
        else:
            response.data = {
                'code': 401,
                'message': '令牌刷新失败',
                'data': response.data
            }
        return response

# 获取当前用户信息视图
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'code': 200,
            'message': '获取用户信息成功',
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'avatar': user.avatar,
                    'role': user.role,
                    'role_display': user.get_role_display(),
                    'department': user.department,
                    'date_joined': user.date_joined,
                    'is_active': user.is_active,
                    'last_login': user.last_login
                }
            },
            'timestamp': timezone.now().isoformat()
        })

# 用户登出视图（JWT版本）
class JWTLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 将refresh token加入黑名单
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        return Response({
            'code': 200,
            'message': '登出成功',
            'data': {}
        })

# 保留原有的测试接口
class TestView(APIView):
    # 处理 GET 请求，方法名必须是 get（小写）
    def get(self, request):
        # 返回 JSON 响应
        return Response({
            "code": 200,
            "msg": "hello world!",
            "data": {
                "method": "GET",
                "timestamp": timezone.now().isoformat()
            }
        })

# 用户注册视图
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "code": 201,
                "msg": "注册成功",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "code": 400,
            "msg": "注册失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登录视图（保持原有逻辑）
class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)

            # 生成或获取token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "token": token.key,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "role_display": user.get_role_display()
                    }
                }
            })
        return Response({
            "code": 400,
            "msg": "登录失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 用户登出视图
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            "code": 200,
            "msg": "登出成功",
            "data": {}
        })

# 用户列表视图（仅管理员可访问）
class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserInfoSerializer(users, many=True)
        return Response({
            "code": 200,
            "msg": "获取用户列表成功",
            "data": serializer.data
        })

# 用户详情视图
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            # 普通用户只能查看自己的信息，管理员可以查看所有用户
            if request.user != user and not request.user.is_administrator():
                return Response({
                    "code": 403,
                    "msg": "权限不足",
                    "data": {}
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = UserInfoSerializer(user)
            return Response({
                "code": 200,
                "msg": "获取用户信息成功",
                "data": serializer.data
            })
        except CustomUser.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "用户不存在",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

# 更新用户角色视图（仅管理员）
class UserRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "code": 200,
                    "msg": "用户角色更新成功",
                    "data": serializer.data
                })
            return Response({
                "code": 400,
                "msg": "更新失败",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "用户不存在",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

# 统计用户角色分布视图
class UserStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 统计各角色用户数量
        stats = {
            'total_users': CustomUser.objects.count(),
            'users': CustomUser.objects.filter(role='user').count(),
            'administrators': CustomUser.objects.filter(role='admin').count(),
        }

        return Response({
            "code": 200,
            "msg": "获取角色统计成功",
            "data": stats
        })


# ==================== LeetCode 相关视图 ====================

class LeetCodeProblemListView(APIView):
    """LeetCode题目列表视图"""

    def get(self, request):
        # 获取查询参数
        difficulty = request.query_params.get('difficulty')
        is_premium = request.query_params.get('is_premium')
        search = request.query_params.get('search')

        # 构建查询集
        queryset = LeetCodeProblem.objects.all()

        # 过滤条件
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        if is_premium is not None:
            is_premium_bool = is_premium.lower() == 'true'
            queryset = queryset.filter(is_premium=is_premium_bool)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )

        # 分页
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        try:
            page = int(page)
            page_size = int(page_size)
            page_size = min(page_size, 500)  # 限制最大页面大小
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        problems = queryset

        serializer = LeetCodeProblemListSerializer(problems, many=True)

        return Response({
            'code': 200,
            'message': '获取题目列表成功',
            'data': {
                'problems': serializer.data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        })


class LeetCodeProblemDetailView(APIView):
    """LeetCode题目详情视图"""

    def get(self, request, problem_id):
        try:
            problem = LeetCodeProblem.objects.get(problem_id=problem_id)
            serializer = LeetCodeProblemSerializer(problem)

            return Response({
                'code': 200,
                'message': '获取题目详情成功',
                'data': serializer.data
            })
        except LeetCodeProblem.DoesNotExist:
            return Response({
                'code': 404,
                'message': '题目不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)


class LeetCodeProblemStatsView(APIView):
    """LeetCode题目统计视图"""

    def get(self, request):
        total_problems = LeetCodeProblem.objects.count()
        easy_count = LeetCodeProblem.objects.filter(difficulty='easy').count()
        medium_count = LeetCodeProblem.objects.filter(difficulty='medium').count()
        hard_count = LeetCodeProblem.objects.filter(difficulty='hard').count()
        premium_count = LeetCodeProblem.objects.filter(is_premium=True).count()

        # 获取热门标签
        popular_tags = ProblemTag.objects.annotate(
            problem_count=Count('leetcodeproblem')
        ).filter(problem_count__gt=0).order_by('-problem_count')[:10]

        tag_stats = [
            {
                'name': tag.name,
                'slug': tag.slug,
                'count': tag.problem_count
            }
            for tag in popular_tags
        ]

        stats = {
            'total_problems': total_problems,
            'difficulty_distribution': {
                'easy': easy_count,
                'medium': medium_count,
                'hard': hard_count
            },
            'premium_problems': premium_count,
            'popular_tags': tag_stats
        }

        return Response({
            'code': 200,
            'message': '获取统计信息成功',
            'data': stats
        })

