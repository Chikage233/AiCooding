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
            # 支持邮箱或用户名登录
            user = None
            if '@' in username:  # 如果包含@，认为是邮箱
                user = authenticate(email=username, password=password)
            else:  # 否则是用户名
                user = authenticate(username=username, password=password)
                
            if not user:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('账号或密码错误')
            
            # 设置用户对象
            self.user = user
            
            # 生成token数据
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


# 自定义JWT登录视图
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = UsernameEmailTokenObtainPairSerializer  # 使用支持用户名/邮箱混合登录的序列化器

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
                    'last_login': user.last_login,
                    'is_staff': user.is_staff,  # 前端需要的字段
                    'is_admin': user.role == 'admin'  # 前端需要的字段
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
            status = request.data.get('status')
            solution_code = request.data.get('solution_code', '')
            notes = request.data.get('notes', '')
            
            if not problem_id or not status:
                return Response({
                    'code': 400,
                    'message': '请提供题目ID和状态',
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                problem = LeetCodeProblem.objects.get(id=problem_id)
            except LeetCodeProblem.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '题目不存在',
                    'data': {}
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 获取或创建完成记录
            completion, created = ProblemCompletion.objects.get_or_create(
                user=request.user,
                problem=problem,
                defaults={
                    'status': status,
                    'attempts': 1,
                    'last_attempted': timezone.now(),
                    'solution_code': solution_code,
                    'notes': notes
                }
            )
            
            if not created:
                # 更新现有记录
                completion.status = status
                completion.attempts += 1
                completion.last_attempted = timezone.now()
                if solution_code:
                    completion.solution_code = solution_code
                if notes:
                    completion.notes = notes
                completion.save()
            
            serializer = ProblemCompletionSerializer(completion)
            
            return Response({
                'code': 200,
                'message': '更新题目完成状态成功',
                'data': serializer.data
            })

