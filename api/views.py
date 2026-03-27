# 必须完整导入 DRF 的 APIView 和 Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token  # 重要：添加这行
from django.contrib.auth import login, logout, authenticate
from .serializers import (UserRegisterSerializer, UserLoginSerializer,
                         UserInfoSerializer, UserRoleUpdateSerializer,
                         LeetCodeProblemSerializer, LeetCodeProblemListSerializer,
                         UserStatsSerializer, UserActivitySerializer, ProblemCompletionSerializer)
from .models import CustomUser, LeetCodeProblem, ProblemTag, UserActivity, ProblemCompletion
from django.db.models import Count, Q
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)
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
        # 添加管理员标识字段以匹配前端判断逻辑
        token['is_staff'] = user.is_staff
        token['is_admin'] = user.role == 'admin'

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
            'is_active': user.is_active,
            'is_staff': user.is_staff,  # 添加is_staff字段
            'is_admin': user.role == 'admin'  # 添加is_admin字段
        }
        return data


class UsernameEmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """支持用户名/邮箱混合登录的JWT序列化器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保使用username字段而不是email字段
        if 'email' in self.fields:
            del self.fields['email']
        # 确保username字段存在
        if 'username' not in self.fields:
            self.fields['username'] = serializers.CharField()
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 添加自定义声明
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_staff'] = user.is_staff
        token['is_admin'] = user.role == 'admin'
        return token
    
    def validate(self, attrs):
        # 获取账号和密码
        username = attrs.get('username')
        password = attrs.get('password')
            
        if username and password:
            # 由于 CustomUser 设置了 USERNAME_FIELD = 'email'
            # Django 的 authenticate 会自动使用 email 字段进行认证
            # 所以无论传入的是邮箱还是用户名，都传递给 username 参数
            # authenticate 内部会根据 USERNAME_FIELD 来处理
            user = authenticate(username=username, password=password)
                    
            if not user:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('账号或密码错误')
                
            # 设置用户对象
            self.user = user
                
            # 生成 token 数据
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)
                
            # 添加用户信息到响应中，匹配前端需要的字段
            data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'role_display': user.get_role_display(),
                'is_active': user.is_active,
                'is_staff': user.is_staff,  # 前端需要的字段
                'is_admin': user.role == 'admin'  # 前端需要的字段
            }
                
            return data
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('请提供账号和密码')


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


# 自定义 JWT 登录视图
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = UsernameEmailTokenObtainPairSerializer  # 使用支持用户名/邮箱混合登录的序列化器

    def post(self, request, *args, **kwargs):
        # 先调用父类方法获取响应
        response = super().post(request, *args, **kwargs)
        
        # 根据状态码包装响应数据
        if response.status_code == 200:
            return Response({
                'code': 200,
                'message': '登录成功',
                'data': response.data
            })
        else:
            return Response({
                'code': 401,
                'message': '账号或密码错误',
                'data': response.data
            }, status=status.HTTP_401_UNAUTHORIZED)


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
        
        # 获取用户做题统计
        total_completed = ProblemCompletion.objects.filter(
            user=user,
            status='completed'
        ).count()
        
        completed_easy = ProblemCompletion.objects.filter(
            user=user,
            status='completed',
            problem__difficulty='easy'
        ).count()
        
        completed_medium = ProblemCompletion.objects.filter(
            user=user,
            status='completed',
            problem__difficulty='medium'
        ).count()
        
        completed_hard = ProblemCompletion.objects.filter(
            user=user,
            status='completed',
            problem__difficulty='hard'
        ).count()
        
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
                    'last_login': user.last_login,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_admin': user.role == 'admin'
                },
                'stats': {
                    'problems_completed': total_completed,
                    'problems_completed_easy': completed_easy,
                    'problems_completed_medium': completed_medium,
                    'problems_completed_hard': completed_hard
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

# 用户登录视图（JWT 版本 - 匹配前端格式）
class LoginView(APIView):
    """
    用户登录接口
    路径：/api/user/login/
    方法：POST
    参数：username (邮箱), password
    返回：{code, message, data: {token, user_id, username}}
    """
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)

            # 生成 JWT token (使用 access token 作为主要 token)
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "code": 200,
                "msg": "登录成功",
                "data": {
                    "token": access_token,  # 前端期望的字段名
                    "user_id": user.id,     # 前端期望的字段
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "role_display": user.get_role_display(),
                    # 额外信息
                    "refresh_token": str(refresh)  # 也提供 refresh token
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
    """LeetCode 题目列表视图"""

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
            page_size = min(page_size, 100)  # 限制最大页面大小为 100，避免数据量过大
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()

        # 只获取需要的字段，减少数据传输
        problems = queryset.only(
            'id', 'problem_id', 'title', 'title_slug', 'difficulty',
            'is_premium', 'acceptance_rate', 'tags'
        )[start:end]

        # 如果是认证用户，预加载完成状态以避免 N+1 查询
        if request.user.is_authenticated:
            # 获取当前用户的 ID
            user_id = request.user.id
            # 预先获取这批题目的完成状态
            completions = ProblemCompletion.objects.filter(
                user_id=user_id,
                problem_id__in=[p.id for p in problems]
            )
            # 创建映射字典
            completion_map = {c.problem_id: c for c in completions}

            # 为每个问题附加完成状态（临时属性）
            for problem in problems:
                completion = completion_map.get(problem.id)
                problem._cached_completion = completion
        else:
            for problem in problems:
                problem._cached_completion = None

        serializer = LeetCodeProblemListSerializer(problems, many=True, context={'request': request})

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


class UserStatsView(APIView):
    """用户统计API视图"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 基础用户统计
        total_users = CustomUser.objects.count()
        
        # 时间范围计算
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # 活跃用户统计
        active_users_today = UserActivity.objects.filter(
            created_at__gte=today_start,
            activity_type='login'
        ).values('user').distinct().count()
        
        active_users_week = UserActivity.objects.filter(
            created_at__gte=week_start,
            activity_type='login'
        ).values('user').distinct().count()
        
        active_users_month = UserActivity.objects.filter(
            created_at__gte=month_start,
            activity_type='login'
        ).values('user').distinct().count()
        
        # 注册统计
        registrations_today = CustomUser.objects.filter(date_joined__gte=today_start).count()
        registrations_week = CustomUser.objects.filter(date_joined__gte=week_start).count()
        registrations_month = CustomUser.objects.filter(date_joined__gte=month_start).count()
        
        # 登录统计
        logins_today = UserActivity.objects.filter(
            created_at__gte=today_start,
            activity_type='login'
        ).count()
        
        logins_week = UserActivity.objects.filter(
            created_at__gte=week_start,
            activity_type='login'
        ).count()
        
        logins_month = UserActivity.objects.filter(
            created_at__gte=month_start,
            activity_type='login'
        ).count()
        
        # 用户分布
        user_roles = dict(CustomUser.objects.values_list('role').annotate(count=Count('role')))
        user_departments = dict(CustomUser.objects.values_list('department').annotate(count=Count('department')).filter(department__isnull=False))
        
        # 活跃度指标
        total_activities = UserActivity.objects.count()
        avg_activities_per_user = total_activities / total_users if total_users > 0 else 0
        
        # 最活跃用户
        most_active_users = UserActivity.objects.values('user__username').annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')[:10]
        
        # 题目完成统计
        total_problems = LeetCodeProblem.objects.count()
        problems_completed_today = ProblemCompletion.objects.filter(
            completed_at__gte=today_start,
            status='completed'
        ).count()
        
        total_completions = ProblemCompletion.objects.filter(status='completed').count()
        avg_completion_rate = (total_completions / (total_users * total_problems) * 100) if total_users > 0 and total_problems > 0 else 0
        
        stats_data = {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'active_users_week': active_users_week,
            'active_users_month': active_users_month,
            'registrations_today': registrations_today,
            'registrations_week': registrations_week,
            'registrations_month': registrations_month,
            'logins_today': logins_today,
            'logins_week': logins_week,
            'logins_month': logins_month,
            'user_roles': user_roles,
            'user_departments': user_departments,
            'avg_activities_per_user': round(avg_activities_per_user, 2),
            'most_active_users': list(most_active_users),
            'total_problems': total_problems,
            'problems_completed_today': problems_completed_today,
            'avg_completion_rate': round(avg_completion_rate, 2)
        }
        
        serializer = UserStatsSerializer(stats_data)
        
        return Response({
            'code': 200,
            'message': '获取用户统计数据成功',
            'data': serializer.data
        })


class UserActivitiesView(APIView):
    """用户活动记录视图"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 获取查询参数
        days = int(request.query_params.get('days', 7))
        activity_type = request.query_params.get('type', None)
        user_id = request.query_params.get('user_id', None)
        
        # 计算时间范围
        start_date = timezone.now() - timedelta(days=days)
        
        # 构建查询
        queryset = UserActivity.objects.filter(created_at__gte=start_date)
        
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 分页
        page_size = int(request.query_params.get('page_size', 50))
        paginator = Paginator(queryset.order_by('-created_at'), page_size)
        page_number = request.query_params.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        serializer = UserActivitySerializer(page_obj, many=True)
        
        return Response({
            'code': 200,
            'message': '获取用户活动记录成功',
            'data': {
                'activities': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })


class ProblemCompletionsView(APIView):
    """题目完成状态视图"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取查询参数
        status_filter = request.query_params.get('status', None)
        problem_id = request.query_params.get('problem_id', None)
        
        # 构建查询
        queryset = ProblemCompletion.objects.filter(user=request.user)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        
        # 分页
        page_size = int(request.query_params.get('page_size', 20))
        paginator = Paginator(queryset.order_by('-updated_at'), page_size)
        page_number = request.query_params.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        serializer = ProblemCompletionSerializer(page_obj, many=True)
        
        return Response({
            'code': 200,
            'message': '获取题目完成状态成功',
            'data': {
                'completions': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })
    
    def post(self, request):
        """更新题目完成状态"""
        problem_id = request.data.get('problem_id')
        completion_status = request.data.get('status', 'completed')  # 默认为 completed
        solution_code = request.data.get('solution_code', '')
        notes = request.data.get('notes', '')
        
        logger.info(f"收到更新题目完成状态请求：problem_id={problem_id}, status={completion_status}, user={request.user}")
        
        if not problem_id:
            logger.warning(f"参数缺失：problem_id={problem_id}")
            return Response({
                'code': 400,
                'message': '请提供题目 ID',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证 status 的有效性
        valid_statuses = ['not_started', 'in_progress', 'completed', 'failed']
        if completion_status not in valid_statuses:
            logger.warning(f"无效的状态值：{completion_status}，使用默认值 'completed'")
            completion_status = 'completed'
        
        try:
            # 使用 problem_id 字段（LeetCode 题目 ID）而不是主键 id
            problem = LeetCodeProblem.objects.get(problem_id=problem_id)
            logger.info(f"找到题目：{problem.title}")
        except LeetCodeProblem.DoesNotExist:
            logger.error(f"题目不存在：problem_id={problem_id}")
            return Response({
                'code': 404,
                'message': '题目不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"查询题目时发生异常：{e}")
            return Response({
                'code': 500,
                'message': f'查询题目时出错：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # 获取或创建完成记录
            completion, created = ProblemCompletion.objects.get_or_create(
                user=request.user,
                problem=problem,
                defaults={
                    'status': completion_status,
                    'attempts': 1,
                    'last_attempted': timezone.now(),
                    'solution_code': solution_code,
                    'notes': notes
                }
            )
            
            if created:
                logger.info(f"创建新的完成记录：completion_id={completion.id}")
            else:
                logger.info(f"更新现有完成记录：completion_id={completion.id}")
                # 更新现有记录
                completion.status = completion_status
                completion.attempts += 1
                completion.last_attempted = timezone.now()
                if solution_code:
                    completion.solution_code = solution_code
                if notes:
                    completion.notes = notes
                completion.save()
            
            serializer = ProblemCompletionSerializer(completion)
            logger.info(f"序列化完成数据成功")
            
            return Response({
                'code': 200,
                'message': '更新题目完成状态成功',
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"更新题目完成状态时发生异常：{e}", exc_info=True)
            return Response({
                'code': 500,
                'message': f'更新题目完成状态时出错：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 验证码相关视图
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SendVerificationCodeSerializer, VerifyCodeSerializer, UserRegisterWithCodeSerializer
from .models import EmailVerificationCode
from django.contrib.auth import get_user_model

User = get_user_model()


class SendVerificationCodeView(APIView):
    """发送邮箱验证码视图"""
    def post(self, request):
        serializer = SendVerificationCodeSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "code": 200,
                "msg": "验证码发送成功",
                "data": result
            })
        return Response({
            "code": 400,
            "msg": "验证码发送失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    """验证邮箱验证码视图"""
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "code": 200,
                "msg": "验证码验证成功",
                "data": {"email": serializer.validated_data['email']}
            })
        return Response({
            "code": 400,
            "msg": "验证码验证失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterWithCodeView(APIView):
    """带验证码的用户注册视图"""
    def post(self, request):
        serializer = UserRegisterWithCodeSerializer(data=request.data)
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


class DebugProblemCompletionsView(APIView):
    """调试用的题目完成状态视图 - 用于查看详细请求数据"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """记录所有请求详情"""
        logger.error("=" * 80)
        logger.error("🔍 收到 POST 请求 - 详细调试信息")
        logger.error("=" * 80)
        
        # 1. 记录请求头
        logger.error(f"📋 请求头:")
        for key, value in request.headers.items():
            logger.error(f"   {key}: {value}")
        
        # 2. 记录请求体类型和内容
        logger.error(f"\n📦 请求体类型：{type(request.data)}")
        logger.error(f"📦 原始请求体内容：{request.data}")
        
        # 3. 尝试获取字段
        logger.error(f"\n🔍 尝试获取字段:")
        problem_id = request.data.get('problem_id')
        status_field = request.data.get('status')
        solution_code = request.data.get('solution_code')
        notes = request.data.get('notes')
        
        logger.error(f"   problem_id: {problem_id} (类型：{type(problem_id)})")
        logger.error(f"   status: {status_field} (类型：{type(status_field)})")
        logger.error(f"   solution_code: {solution_code} (类型：{type(solution_code)})")
        logger.error(f"   notes: {notes} (类型：{type(notes)})")
        
        # 4. 如果是 dict，记录所有键
        if isinstance(request.data, dict):
            logger.error(f"\n🔑 请求体的所有键：{list(request.data.keys())}")
        
        # 5. 用户信息
        logger.error(f"\n👤 用户信息:")
        logger.error(f"   user: {request.user}")
        logger.error(f"   user.id: {request.user.id}")
        logger.error(f"   user.username: {request.user.username}")
        
        logger.error("=" * 80)
        
        # 返回调试信息给前端
        return Response({
            'code': 200,
            'message': '调试信息已记录到服务器日志',
            'data': {
                'request_headers': dict(request.headers),
                'request_data_type': str(type(request.data)),
                'request_data': str(request.data),
                'extracted_fields': {
                    'problem_id': problem_id,
                    'problem_id_type': str(type(problem_id)) if problem_id is not None else None,
                    'status': status_field,
                    'status_type': str(type(status_field)) if status_field is not None else None,
                    'solution_code': solution_code,
                    'notes': notes,
                },
                'user_info': {
                    'id': request.user.id,
                    'username': request.user.username,
                }
            }
        })
