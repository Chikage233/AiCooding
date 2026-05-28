# 蹇呴』瀹屾暣瀵煎叆 DRF 鐨?APIView 鍜?Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authtoken.models import Token  # 閲嶈锛氭坊鍔犺繖琛?
from django.contrib.auth import login, logout, authenticate
from .serializers import (UserRegisterSerializer, UserLoginSerializer,
                         UserInfoSerializer, UserRoleUpdateSerializer,
                         LeetCodeProblemSerializer, LeetCodeProblemListSerializer,
                         UserStatsSerializer, UserActivitySerializer, ProblemCompletionSerializer,
                         CurrentUserUpdateSerializer, NicknameReviewListItemSerializer,
                         NicknameReviewRejectSerializer)
from .models import CustomUser, LeetCodeProblem, ProblemTag, UserActivity, ProblemCompletion, NicknameReviewLog
from django.db.models import Count, Q
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
import json
import hashlib
import logging
from .nickname_utils import validate_nickname, NICKNAME_DAILY_LIMIT
from .captcha_utils import create_login_captcha, verify_login_captcha
from .avatar_presets import get_avatar_presets
from .email_verification_security import (
    check_send_code_rate_limit,
    record_send_code_request,
    check_verify_code_rate_limit,
    record_verify_code_failure,
    clear_verify_code_failures,
)

logger = logging.getLogger(__name__)
from rest_framework_simplejwt.views import TokenObtainPairView

# JWT鐩稿叧瀵煎叆
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

# 鑷畾涔塉WT搴忓垪鍖栧櫒
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 娣诲姞鑷畾涔夊０鏄?
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        # 娣诲姞绠＄悊鍛樻爣璇嗗瓧娈典互鍖归厤鍓嶇鍒ゆ柇閫昏緫
        token['is_staff'] = user.is_staff
        token['is_admin'] = user.role == 'admin'

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 娣诲姞鐢ㄦ埛淇℃伅鍒板搷搴斾腑
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'role_display': user.get_role_display(),
            'is_active': user.is_active,
            'is_staff': user.is_staff,  # 娣诲姞is_staff瀛楁
            'is_admin': user.role == 'admin'  # 娣诲姞is_admin瀛楁
        }
        return data


class UsernameEmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """鏀寔鐢ㄦ埛鍚?閭娣峰悎鐧诲綍鐨凧WT搴忓垪鍖栧櫒"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 纭繚浣跨敤username瀛楁鑰屼笉鏄痚mail瀛楁
        if 'email' in self.fields:
            del self.fields['email']
        # 纭繚username瀛楁瀛樺湪
        if 'username' not in self.fields:
            self.fields['username'] = serializers.CharField()
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 娣诲姞鑷畾涔夊０鏄?
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_staff'] = user.is_staff
        token['is_admin'] = user.role == 'admin'
        return token
    
    def validate(self, attrs):
        # 鑾峰彇璐﹀彿鍜屽瘑鐮?
        username = attrs.get('username')
        password = attrs.get('password')
            
        if username and password:
            # 鐢变簬 CustomUser 璁剧疆浜?USERNAME_FIELD = 'email'
            # Django 鐨?authenticate 浼氳嚜鍔ㄤ娇鐢?email 瀛楁杩涜璁よ瘉
            # 鎵€浠ユ棤璁轰紶鍏ョ殑鏄偖绠辫繕鏄敤鎴峰悕锛岄兘浼犻€掔粰 username 鍙傛暟
            # authenticate 鍐呴儴浼氭牴鎹?USERNAME_FIELD 鏉ュ鐞?
            user = authenticate(username=username, password=password)
                    
            if not user:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('账号或密码错误')
                
            # 璁剧疆鐢ㄦ埛瀵硅薄
            self.user = user
                
            # 鐢熸垚 token 鏁版嵁
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)
                
            # 娣诲姞鐢ㄦ埛淇℃伅鍒板搷搴斾腑锛屽尮閰嶅墠绔渶瑕佺殑瀛楁
            data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'role_display': user.get_role_display(),
                'is_active': user.is_active,
                'is_staff': user.is_staff,  # 鍓嶇闇€瑕佺殑瀛楁
                'is_admin': user.role == 'admin'  # 鍓嶇闇€瑕佺殑瀛楁
            }
                
            return data
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('璇锋彁渚涜处鍙峰拰瀵嗙爜')


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """鏀寔閭鐧诲綍鐨凧WT搴忓垪鍖栧櫒"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 淇敼瀛楁鍚嶄负email鑰屼笉鏄痷sername
        self.fields['email'] = serializers.EmailField()
        # 鍒犻櫎鍘熸潵鐨剈sername瀛楁
        if 'username' in self.fields:
            del self.fields['username']

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 娣诲姞鑷畾涔夊０鏄?
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        # 鐩存帴浣跨敤email杩涜璁よ瘉锛屼笉杞崲瀛楁鍚?
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # 浣跨敤Django鐨刟uthenticate鍑芥暟杩涜璁よ瘉
            from django.contrib.auth import authenticate
            user = authenticate(email=email, password=password)

            if not user:
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed('邮箱或密码错误')

            # 璁剧疆鐢ㄦ埛瀵硅薄
            self.user = user

            # 鐢熸垚token鏁版嵁
            data = {}
            refresh = self.get_token(user)
            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)

            # 娣诲姞鐢ㄦ埛淇℃伅鍒板搷搴斾腑
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
            raise ValidationError('璇锋彁渚涢偖绠卞拰瀵嗙爜')


# 鑷畾涔?JWT 鐧诲綍瑙嗗浘
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = UsernameEmailTokenObtainPairSerializer  # 浣跨敤鏀寔鐢ㄦ埛鍚?閭娣峰悎鐧诲綍鐨勫簭鍒楀寲鍣?

    def post(self, request, *args, **kwargs):
        if getattr(settings, 'LOGIN_CAPTCHA_ENABLED', True):
            ok, error_code, error_message, error_status = verify_login_captcha(
                request.data.get('captcha_id'),
                request.data.get('captcha_code')
            )
            if not ok:
                return Response({
                    'code': error_status,
                    'business_code': error_code,
                    'message': error_message,
                    'data': {}
                }, status=error_status)

        # 鍏堣皟鐢ㄧ埗绫绘柟娉曡幏鍙栧搷搴?
        response = super().post(request, *args, **kwargs)
        
        # 鐧诲綍鎴愬姛鏃惰褰曟椿鍔?
        if response.status_code == 200:
            user_payload = None
            if isinstance(response.data, dict):
                if isinstance(response.data.get('user'), dict):
                    user_payload = response.data.get('user')
                elif isinstance(response.data.get('data'), dict) and isinstance(response.data['data'].get('user'), dict):
                    user_payload = response.data['data'].get('user')

            user_id = user_payload.get('id') if user_payload else None
            if user_id:
                try:
                    from .models import CustomUser, UserActivity
                    user = CustomUser.objects.get(id=user_id)
                    UserActivity.objects.create(
                        user=user,
                        activity_type='login',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'璁板綍鐧诲綍娲诲姩鏃跺嚭閿欙細{e}')
        
        # 鏍规嵁鐘舵€佺爜鍖呰鍝嶅簲鏁版嵁
        if response.status_code == 200:
            return Response({
                'code': 200,
                'message': '鐧诲綍鎴愬姛',
                'data': response.data
            })
        else:
            return Response({
                'code': 401,
                'message': '账号或密码错误',
                'data': response.data
            }, status=status.HTTP_401_UNAUTHORIZED)


# JWT鍒锋柊浠ょ墝瑙嗗浘
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {
                'code': 200,
                'message': '浠ょ墝鍒锋柊鎴愬姛',
                'data': response.data
            }
        else:
            response.data = {
                'code': 401,
                'message': '浠ょ墝鍒锋柊澶辫触',
                'data': response.data
            }
        return response


class LoginCaptchaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        captcha_payload = create_login_captcha()
        return Response({
            'code': 200,
            'message': '获取验证码成功',
            'data': captcha_payload
        })


class AvatarPresetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'code': 200,
            'message': '获取预置头像成功',
            'data': {
                'avatars': get_avatar_presets()
            }
        })


# 鑾峰彇褰撳墠鐢ㄦ埛淇℃伅瑙嗗浘
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_user_stats(self, user):
        total_completed = ProblemCompletion.objects.filter(user=user, status='completed').count()
        completed_easy = ProblemCompletion.objects.filter(user=user, status='completed', problem__difficulty='easy').count()
        completed_medium = ProblemCompletion.objects.filter(user=user, status='completed', problem__difficulty='medium').count()
        completed_hard = ProblemCompletion.objects.filter(user=user, status='completed', problem__difficulty='hard').count()
        return {
            'problems_completed': total_completed,
            'problems_completed_easy': completed_easy,
            'problems_completed_medium': completed_medium,
            'problems_completed_hard': completed_hard
        }

    def _serialize_user(self, user):
        user_data = UserInfoSerializer(user).data
        user_data.update({
            'last_login': user.last_login,
            'is_staff': user.is_staff,
            'is_admin': user.role == 'admin',
            'display_name': user.display_name,
            'nickname_status': user.nickname_status
        })
        return user_data

    def _nickname_error_response(self, code, hit_rule, message, http_status):
        return Response({
            'code': code,
            'hit_rule': hit_rule,
            'message': message,
            'status': http_status
        }, status=http_status)

    def _log_nickname_event(self, user, action, nickname_value="", hit_rule="", message="", operator=None):
        try:
            NicknameReviewLog.objects.create(
                user=user,
                operator=operator,
                action=action,
                nickname_value=nickname_value or "",
                hit_rule=hit_rule or "",
                message=message or ""
            )
        except Exception as e:
            logger.warning(f'记录昵称审核日志失败: {e}')

    def _daily_nickname_submit_count(self, user):
        today = timezone.localdate()
        return NicknameReviewLog.objects.filter(
            user=user,
            action='submit',
            created_at__date=today
        ).count()

    def get(self, request):
        user = request.user
        stats = self._get_user_stats(user)
        return Response({
            'code': 200,
            'message': '获取用户信息成功',
            'data': {
                'user': self._serialize_user(user),
                'stats': stats,
                'avatar_presets': get_avatar_presets()
            },
            'timestamp': timezone.now().isoformat()
        })

    def patch(self, request):
        payload = request.data.copy()
        raw_nickname = request.data.get('nickname') if 'nickname' in request.data else None
        payload.pop('nickname', None)

        serializer = CurrentUserUpdateSerializer(request.user, data=payload, partial=True)
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '个人信息更新失败',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        normalized_nickname = None
        same_as_current = False
        user = request.user
        nickname_submitted = False

        if raw_nickname is not None:
            is_valid, normalized, hit_rule, error_message = validate_nickname(raw_nickname)
            if not is_valid:
                self._log_nickname_event(
                    user=user,
                    action='validation_fail',
                    nickname_value=normalized,
                    hit_rule=hit_rule,
                    message=error_message
                )
                return self._nickname_error_response(
                    code='NICKNAME_INVALID',
                    hit_rule=hit_rule,
                    message=error_message,
                    http_status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            approved_name = (user.nickname_approved or "").strip()
            pending_name = (user.nickname_candidate or "").strip()
            same_as_current = (
                (user.nickname_status == 'approved' and normalized == approved_name) or
                (user.nickname_status == 'pending' and normalized == pending_name)
            )
            normalized_nickname = normalized

            if not same_as_current:
                submit_count = self._daily_nickname_submit_count(user)
                if submit_count >= NICKNAME_DAILY_LIMIT:
                    message = f'昵称每日最多修改{NICKNAME_DAILY_LIMIT}次，请明天再试'
                    self._log_nickname_event(
                        user=user,
                        action='rate_limited',
                        nickname_value=normalized,
                        hit_rule='daily_limit',
                        message=message
                    )
                    return self._nickname_error_response(
                        code='NICKNAME_RATE_LIMIT',
                        hit_rule='daily_limit',
                        message=message,
                        http_status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

        user = serializer.save()

        if raw_nickname is not None and not same_as_current and normalized_nickname is not None:
            user.nickname_candidate = normalized_nickname
            user.nickname_status = 'pending'
            user.nickname_reject_reason = ''
            user.nickname_reviewed_by = None
            user.nickname_reviewed_at = None
            user.save(update_fields=[
                'nickname_candidate',
                'nickname_status',
                'nickname_reject_reason',
                'nickname_reviewed_by',
                'nickname_reviewed_at',
                'updated_at'
            ])
            nickname_submitted = True
            self._log_nickname_event(
                user=user,
                action='submit',
                nickname_value=normalized_nickname,
                message='昵称已提交审核'
            )

        try:
            UserActivity.objects.create(
                user=user,
                activity_type='profile_update',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as e:
            logger.warning(f'记录个人资料更新活动失败: {e}')

        return Response({
            'code': 200,
            'message': '个人信息更新成功，昵称已提交审核' if nickname_submitted else '个人信息更新成功',
            'data': {
                'user': self._serialize_user(user)
            }
        })

class JWTLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 灏唕efresh token鍔犲叆榛戝悕鍗?
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        return Response({
            'code': 200,
            'message': '鐧诲嚭鎴愬姛',
            'data': {}
        })

# 淇濈暀鍘熸湁鐨勬祴璇曟帴鍙?
class TestView(APIView):
    # 澶勭悊 GET 璇锋眰锛屾柟娉曞悕蹇呴』鏄?get锛堝皬鍐欙級
    def get(self, request):
        # 杩斿洖 JSON 鍝嶅簲
        return Response({
            "code": 200,
            "msg": "hello world!",
            "data": {
                "method": "GET",
                "timestamp": timezone.now().isoformat()
            }
        })

# 鐢ㄦ埛娉ㄥ唽瑙嗗浘
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "code": 201,
                "msg": "娉ㄥ唽鎴愬姛",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "code": 400,
            "msg": "娉ㄥ唽澶辫触",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 鐢ㄦ埛鐧诲綍瑙嗗浘锛圝WT 鐗堟湰 - 鍖归厤鍓嶇鏍煎紡锛?
class LoginView(APIView):
    """
    鐢ㄦ埛鐧诲綍鎺ュ彛
    璺緞锛?api/user/login/
    鏂规硶锛歅OST
    鍙傛暟锛歶sername (閭), password
    杩斿洖锛{code, message, data: {token, user_id, username}}
    """
    def post(self, request):
        if getattr(settings, 'LOGIN_CAPTCHA_ENABLED', True):
            ok, error_code, error_message, error_status = verify_login_captcha(
                request.data.get('captcha_id'),
                request.data.get('captcha_code')
            )
            if not ok:
                return Response({
                    "code": error_status,
                    "business_code": error_code,
                    "message": error_message,
                    "data": {}
                }, status=error_status)

        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)

            # 璁板綍鐢ㄦ埛鐧诲綍娲诲姩
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )

            # 鐢熸垚 JWT token (浣跨敤 access token 浣滀负涓昏 token)
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "code": 200,
                "msg": "鐧诲綍鎴愬姛",
                "data": {
                    "token": access_token,  # 鍓嶇鏈熸湜鐨勫瓧娈靛悕
                    "user_id": user.id,     # 鍓嶇鏈熸湜鐨勫瓧娈?
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "role_display": user.get_role_display(),
                    # 棰濆淇℃伅
                    "refresh_token": str(refresh)  # 涔熸彁渚?refresh token
                }
            })
        return Response({
            "code": 400,
            "msg": "鐧诲綍澶辫触",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 鐢ㄦ埛鐧诲嚭瑙嗗浘
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            "code": 200,
            "msg": "鐧诲嚭鎴愬姛",
            "data": {}
        })

# 鐢ㄦ埛鍒楄〃瑙嗗浘锛堜粎绠＄悊鍛樺彲璁块棶锛?
class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserInfoSerializer(users, many=True)
        return Response({
            "code": 200,
            "msg": "鑾峰彇鐢ㄦ埛鍒楄〃鎴愬姛",
            "data": serializer.data
        })

# 鐢ㄦ埛璇︽儏瑙嗗浘
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            # 鏅€氱敤鎴峰彧鑳芥煡鐪嬭嚜宸辩殑淇℃伅锛岀鐞嗗憳鍙互鏌ョ湅鎵€鏈夌敤鎴?
            if request.user != user and not request.user.is_administrator():
                return Response({
                    "code": 403,
                    "msg": "鏉冮檺涓嶈冻",
                    "data": {}
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = UserInfoSerializer(user)
            return Response({
                "code": 200,
                "msg": "鑾峰彇鐢ㄦ埛淇℃伅鎴愬姛",
                "data": serializer.data
            })
        except CustomUser.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "用户不存在",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)

# 鏇存柊鐢ㄦ埛瑙掕壊瑙嗗浘锛堜粎绠＄悊鍛橈級
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
                    "msg": "鐢ㄦ埛瑙掕壊鏇存柊鎴愬姛",
                    "data": serializer.data
                })
            return Response({
                "code": 400,
                "msg": "鏇存柊澶辫触",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({
                "code": 404,
                "msg": "用户不存在",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)


class NicknameReviewListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_value = request.query_params.get('status', 'pending')
        valid_statuses = {'pending', 'approved', 'rejected'}
        if status_value not in valid_statuses:
            return Response({
                'code': 400,
                'message': '无效的审核状态',
                'data': {
                    'status': status_value
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = CustomUser.objects.filter(nickname_status=status_value).order_by('-updated_at')
        if status_value == 'pending':
            queryset = queryset.exclude(nickname_candidate__isnull=True).exclude(nickname_candidate='')

        serializer = NicknameReviewListItemSerializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取昵称审核列表成功',
            'data': serializer.data
        })


class NicknameReviewApproveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id):
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'code': 404,
                'message': '用户不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        candidate = (target_user.nickname_candidate or '').strip()
        if target_user.nickname_status != 'pending' or not candidate:
            return Response({
                'code': 400,
                'message': '当前用户没有待审核昵称',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        is_valid, normalized, hit_rule, error_message = validate_nickname(candidate)
        if not is_valid:
            NicknameReviewLog.objects.create(
                user=target_user,
                operator=request.user,
                action='validation_fail',
                nickname_value=normalized,
                hit_rule=hit_rule,
                message=error_message
            )
            return Response({
                'code': 'NICKNAME_INVALID',
                'hit_rule': hit_rule,
                'message': error_message,
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        target_user.nickname_approved = normalized
        target_user.nickname_candidate = ''
        target_user.nickname_status = 'approved'
        target_user.nickname_reject_reason = ''
        target_user.nickname_reviewed_by = request.user
        target_user.nickname_reviewed_at = timezone.now()
        target_user.save(update_fields=[
            'nickname_approved',
            'nickname_candidate',
            'nickname_status',
            'nickname_reject_reason',
            'nickname_reviewed_by',
            'nickname_reviewed_at',
            'updated_at'
        ])

        NicknameReviewLog.objects.create(
            user=target_user,
            operator=request.user,
            action='approve',
            nickname_value=normalized,
            message='管理员通过昵称审核'
        )

        return Response({
            'code': 200,
            'message': '昵称审核通过',
            'data': {
                'user': UserInfoSerializer(target_user).data
            }
        })


class NicknameReviewRejectView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id):
        serializer = NicknameReviewRejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '驳回原因不能为空',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'code': 404,
                'message': '用户不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        candidate = (target_user.nickname_candidate or '').strip()
        if target_user.nickname_status != 'pending' or not candidate:
            return Response({
                'code': 400,
                'message': '当前用户没有待审核昵称',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        reason = serializer.validated_data['reason'].strip()
        target_user.nickname_status = 'rejected'
        target_user.nickname_reject_reason = reason
        target_user.nickname_reviewed_by = request.user
        target_user.nickname_reviewed_at = timezone.now()
        target_user.save(update_fields=[
            'nickname_status',
            'nickname_reject_reason',
            'nickname_reviewed_by',
            'nickname_reviewed_at',
            'updated_at'
        ])

        NicknameReviewLog.objects.create(
            user=target_user,
            operator=request.user,
            action='reject',
            nickname_value=candidate,
            message=reason
        )

        return Response({
            'code': 200,
            'message': '已驳回昵称申请',
            'data': {
                'user': UserInfoSerializer(target_user).data
            }
        })

# 缁熻鐢ㄦ埛瑙掕壊鍒嗗竷瑙嗗浘锛堝凡搴熷純锛屼娇鐢ㄤ笅闈㈢殑 UserStatsView 鏇夸唬锛?
# class UserStatsView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminUser]
#
#     def get(self, request):
#         # 缁熻鍚勮鑹茬敤鎴锋暟閲?
#         stats = {
#             'total_users': CustomUser.objects.count(),
#             'users': CustomUser.objects.filter(role='user').count(),
#             'administrators': CustomUser.objects.filter(role='admin').count(),
#         }
#
#         return Response({
#             "code": 200,
#             "msg": "鑾峰彇瑙掕壊缁熻鎴愬姛",
#             "data": stats
#         })


# ==================== LeetCode 鐩稿叧瑙嗗浘 ====================

class LeetCodeProblemListView(APIView):
    """LeetCode 棰樼洰鍒楄〃瑙嗗浘"""

    def get(self, request):
        # 鑾峰彇鏌ヨ鍙傛暟
        difficulty = request.query_params.get('difficulty')
        is_premium = request.query_params.get('is_premium')
        search = request.query_params.get('search')

        # 鏋勫缓鏌ヨ闆?
        queryset = LeetCodeProblem.objects.all()

        # 杩囨护鏉′欢
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

        # 鍒嗛〉
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)

        try:
            page = int(page)
            page_size = int(page_size)
            page_size = min(page_size, 100)  # 闄愬埗鏈€澶ч〉闈㈠ぇ灏忎负 100锛岄伩鍏嶆暟鎹噺杩囧ぇ
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()

        # 鍙幏鍙栭渶瑕佺殑瀛楁锛屽噺灏戞暟鎹紶杈?
        problems = queryset.only(
            'id', 'problem_id', 'title', 'title_slug', 'difficulty',
            'is_premium', 'acceptance_rate', 'tags'
        )[start:end]

        # 濡傛灉鏄璇佺敤鎴凤紝棰勫姞杞藉畬鎴愮姸鎬佷互閬垮厤 N+1 鏌ヨ
        if request.user.is_authenticated:
            # 鑾峰彇褰撳墠鐢ㄦ埛鐨?ID
            user_id = request.user.id
            # 棰勫厛鑾峰彇杩欐壒棰樼洰鐨勫畬鎴愮姸鎬?
            completions = ProblemCompletion.objects.filter(
                user_id=user_id,
                problem_id__in=[p.id for p in problems]
            )
            # 鍒涘缓鏄犲皠瀛楀吀
            completion_map = {c.problem_id: c for c in completions}

            # 涓烘瘡涓棶棰橀檮鍔犲畬鎴愮姸鎬侊紙涓存椂灞炴€э級
            for problem in problems:
                completion = completion_map.get(problem.id)
                problem._cached_completion = completion
        else:
            for problem in problems:
                problem._cached_completion = None

        serializer = LeetCodeProblemListSerializer(problems, many=True, context={'request': request})

        return Response({
            'code': 200,
            'message': '鑾峰彇棰樼洰鍒楄〃鎴愬姛',
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
    """LeetCode棰樼洰璇︽儏瑙嗗浘"""

    def get(self, request, problem_id):
        try:
            problem = LeetCodeProblem.objects.get(problem_id=problem_id)
            serializer = LeetCodeProblemSerializer(problem)

            return Response({
                'code': 200,
                'message': '鑾峰彇棰樼洰璇︽儏鎴愬姛',
                'data': serializer.data
            })
        except LeetCodeProblem.DoesNotExist:
            return Response({
                'code': 404,
                'message': '题目不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)


class LeetCodeProblemStatsView(APIView):
    """LeetCode 棰樼洰缁熻瑙嗗浘"""

    def get(self, request):
        try:
            # 鍩虹缁熻
            total_problems = LeetCodeProblem.objects.count()
            easy_count = LeetCodeProblem.objects.filter(difficulty='easy').count()
            medium_count = LeetCodeProblem.objects.filter(difficulty='medium').count()
            hard_count = LeetCodeProblem.objects.filter(difficulty='hard').count()
            premium_count = LeetCodeProblem.objects.filter(is_premium=True).count()

            # 鑾峰彇鐑棬鏍囩锛堜粠 JSON 瀛楁涓粺璁★級
            tag_stats = []
            try:
                from collections import Counter
                
                # 鑾峰彇鎵€鏈夐鐩殑鏍囩
                all_tags = []
                for problem in LeetCodeProblem.objects.only('tags'):
                    if problem.tags and isinstance(problem.tags, list):
                        all_tags.extend(problem.tags)
                
                # 缁熻鏍囩棰戠巼
                tag_counter = Counter(all_tags)
                
                # 鍙栧墠 10 涓儹闂ㄦ爣绛?
                popular_tags = tag_counter.most_common(10)
                
                tag_stats = [
                    {
                        'name': tag_name,
                        'slug': tag_name.lower().replace(' ', '-').replace('_', '-'),
                        'count': tag_count
                    }
                    for tag_name, tag_count in popular_tags
                ]
                
            except Exception as tag_error:
                # 濡傛灉鏍囩缁熻澶辫触锛岃褰曟棩蹇椾絾涓嶅奖鍝嶆暣浣撹繑鍥?
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'鑾峰彇鐑棬鏍囩澶辫触锛{tag_error}')
                tag_stats = []

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
                'message': '鑾峰彇缁熻淇℃伅鎴愬姛',
                'data': stats
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'鑾峰彇棰樼洰缁熻淇℃伅澶辫触锛{e}', exc_info=True)
            
            return Response({
                'code': 500,
                'message': f'鑾峰彇缁熻淇℃伅澶辫触锛{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserStatsView(APIView):
    """鐢ㄦ埛缁熻API瑙嗗浘"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 鍩虹鐢ㄦ埛缁熻
        total_users = CustomUser.objects.count()
        
        # 鏃堕棿鑼冨洿璁＄畻
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # 娲昏穬鐢ㄦ埛缁熻
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
        
        # 娉ㄥ唽缁熻
        registrations_today = CustomUser.objects.filter(date_joined__gte=today_start).count()
        registrations_week = CustomUser.objects.filter(date_joined__gte=week_start).count()
        registrations_month = CustomUser.objects.filter(date_joined__gte=month_start).count()
        
        # 鐧诲綍缁熻
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
        
        # 鐢ㄦ埛鍒嗗竷
        user_roles = dict(CustomUser.objects.values_list('role').annotate(count=Count('role')))
        user_departments = dict(CustomUser.objects.values_list('department').annotate(count=Count('department')).filter(department__isnull=False))
        
        # 娲昏穬搴︽寚鏍?
        total_activities = UserActivity.objects.count()
        avg_activities_per_user = total_activities / total_users if total_users > 0 else 0
        
        # 鏈€娲昏穬鐢ㄦ埛
        most_active_users = UserActivity.objects.values('user__username').annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')[:10]
        
        # 棰樼洰瀹屾垚缁熻
        total_problems = LeetCodeProblem.objects.count()
        problems_completed_today = ProblemCompletion.objects.filter(
            completed_at__gte=today_start,
            status='completed'
        ).count()
        
        completed_qs = ProblemCompletion.objects.filter(status='completed')
        total_completions = completed_qs.count()
        completed_problem_total = completed_qs.values('problem_id').distinct().count()
        completed_problem_easy = completed_qs.filter(problem__difficulty='easy').values('problem_id').distinct().count()
        completed_problem_medium = completed_qs.filter(problem__difficulty='medium').values('problem_id').distinct().count()
        completed_problem_hard = completed_qs.filter(problem__difficulty='hard').values('problem_id').distinct().count()

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
            'avg_completion_rate': round(avg_completion_rate, 2),
            # 全站口径（按题目去重）：至少有 1 个用户完成过的题目数量
            'problems_completed_total': completed_problem_total,
            'total_completed_problems': completed_problem_total,
            'problems_completed_easy': completed_problem_easy,
            'problems_completed_medium': completed_problem_medium,
            'problems_completed_hard': completed_problem_hard
        }
        
        serializer = UserStatsSerializer(stats_data)
        
        return Response({
            'code': 200,
            'message': '鑾峰彇鐢ㄦ埛缁熻鏁版嵁鎴愬姛',
            'data': serializer.data
        })


class UserActivitiesView(APIView):
    """鐢ㄦ埛娲诲姩璁板綍瑙嗗浘"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 鑾峰彇鏌ヨ鍙傛暟
        days = int(request.query_params.get('days', 7))
        activity_type = request.query_params.get('type', None)
        user_id = request.query_params.get('user_id', None)
        
        # 璁＄畻鏃堕棿鑼冨洿
        start_date = timezone.now() - timedelta(days=days)
        
        # 鏋勫缓鏌ヨ
        queryset = UserActivity.objects.filter(created_at__gte=start_date)
        
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 鍒嗛〉
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
            'message': '鑾峰彇鐢ㄦ埛娲诲姩璁板綍鎴愬姛',
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
    """Problem completions view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 鑾峰彇鏌ヨ鍙傛暟
        status_filter = request.query_params.get('status', None)
        problem_id = request.query_params.get('problem_id', None)
        
        # 鏋勫缓鏌ヨ
        queryset = ProblemCompletion.objects.filter(user=request.user)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)
        
        # 鍒嗛〉
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
        """Update problem completion status."""
        problem_id = request.data.get('problem_id')
        completion_status = request.data.get('status', 'completed')  # 榛樿涓?completed
        solution_code = request.data.get('solution_code', '')
        notes = request.data.get('notes', '')
        
        logger.info(f"鏀跺埌鏇存柊棰樼洰瀹屾垚鐘舵€佽姹傦細problem_id={problem_id}, status={completion_status}, user={request.user}")
        
        if not problem_id:
            logger.warning(f"鍙傛暟缂哄け锛歱roblem_id={problem_id}")
            return Response({
                'code': 400,
                'message': '璇锋彁渚涢鐩?ID',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 楠岃瘉 status 鐨勬湁鏁堟€?
        valid_statuses = ['not_started', 'in_progress', 'completed', 'failed']
        if completion_status not in valid_statuses:
            logger.warning(f"鏃犳晥鐨勭姸鎬佸€硷細{completion_status}锛屼娇鐢ㄩ粯璁ゅ€?'completed'")
            completion_status = 'completed'
        
        try:
            # 浣跨敤 problem_id 瀛楁锛圠eetCode 棰樼洰 ID锛夎€屼笉鏄富閿?id
            problem = LeetCodeProblem.objects.get(problem_id=problem_id)
            logger.info(f"鎵惧埌棰樼洰锛{problem.title}")
        except LeetCodeProblem.DoesNotExist:
            logger.error(f"棰樼洰涓嶅瓨鍦細problem_id={problem_id}")
            return Response({
                'code': 404,
                'message': '题目不存在',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"鏌ヨ棰樼洰鏃跺彂鐢熷紓甯革細{e}")
            return Response({
                'code': 500,
                'message': f'鏌ヨ棰樼洰鏃跺嚭閿欙細{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # 鑾峰彇鎴栧垱寤哄畬鎴愯褰?
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
                logger.info(f"鍒涘缓鏂扮殑瀹屾垚璁板綍锛歝ompletion_id={completion.id}")
            else:
                logger.info(f"鏇存柊鐜版湁瀹屾垚璁板綍锛歝ompletion_id={completion.id}")
                # 鏇存柊鐜版湁璁板綍
                completion.status = completion_status
                completion.attempts += 1
                completion.last_attempted = timezone.now()
                if solution_code:
                    completion.solution_code = solution_code
                if notes:
                    completion.notes = notes
                completion.save()
            
            serializer = ProblemCompletionSerializer(completion)
            logger.info("序列化完成数据成功")
            
            return Response({
                'code': 200,
                'message': '更新题目完成状态成功',
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"鏇存柊棰樼洰瀹屾垚鐘舵€佹椂鍙戠敓寮傚父锛{e}", exc_info=True)
            return Response({
                'code': 500,
                'message': f'鏇存柊棰樼洰瀹屾垚鐘舵€佹椂鍑洪敊锛{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 楠岃瘉鐮佺浉鍏宠鍥?
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SendVerificationCodeSerializer, VerifyCodeSerializer, UserRegisterWithCodeSerializer
from .models import EmailVerificationCode
from django.contrib.auth import get_user_model

User = get_user_model()


class SendVerificationCodeView(APIView):
    """鍙戦€侀偖绠遍獙璇佺爜瑙嗗浘"""
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        client_ip = request.META.get("REMOTE_ADDR")

        ok, error_code, error_message, error_status = check_send_code_rate_limit(email, client_ip)
        if not ok:
            return Response({
                "code": error_status,
                "business_code": error_code,
                "msg": error_message,
                "data": {}
            }, status=error_status)

        serializer = SendVerificationCodeSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            record_send_code_request(email, client_ip)
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
    """Verify email code view."""
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        client_ip = request.META.get("REMOTE_ADDR")

        ok, error_code, error_message, error_status = check_verify_code_rate_limit(email, client_ip)
        if not ok:
            return Response({
                "code": error_status,
                "business_code": error_code,
                "msg": error_message,
                "data": {}
            }, status=error_status)

        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            clear_verify_code_failures(email, client_ip)
            return Response({
                "code": 200,
                "msg": "验证码校验成功",
                "data": {"email": serializer.validated_data['email']}
            })
        record_verify_code_failure(email, client_ip)
        return Response({
            "code": 400,
            "msg": "验证码校验失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterWithCodeView(APIView):
    """Register with verification code view."""
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        client_ip = request.META.get("REMOTE_ADDR")

        ok, error_code, error_message, error_status = check_verify_code_rate_limit(email, client_ip)
        if not ok:
            return Response({
                "code": error_status,
                "business_code": error_code,
                "msg": error_message,
                "data": {}
            }, status=error_status)

        serializer = UserRegisterWithCodeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            clear_verify_code_failures(email, client_ip)
            return Response({
                "code": 201,
                "msg": "娉ㄥ唽鎴愬姛",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)
        record_verify_code_failure(email, client_ip)
        return Response({
            "code": 400,
            "msg": "娉ㄥ唽澶辫触",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DebugProblemCompletionsView(APIView):
    """璋冭瘯鐢ㄧ殑棰樼洰瀹屾垚鐘舵€佽鍥?- 鐢ㄤ簬鏌ョ湅璇︾粏璇锋眰鏁版嵁"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Record request debug details."""
        logger.error("=" * 80)
        logger.error("馃攳 鏀跺埌 POST 璇锋眰 - 璇︾粏璋冭瘯淇℃伅")
        logger.error("=" * 80)
        
        # 1. 璁板綍璇锋眰澶?
        logger.error(f"馃搵 璇锋眰澶?")
        for key, value in request.headers.items():
            logger.error(f"   {key}: {value}")
        
        # 2. 璁板綍璇锋眰浣撶被鍨嬪拰鍐呭
        logger.error(f"\n馃摝 璇锋眰浣撶被鍨嬶細{type(request.data)}")
        logger.error(f"馃摝 鍘熷璇锋眰浣撳唴瀹癸細{request.data}")
        
        # 3. 灏濊瘯鑾峰彇瀛楁
        logger.error(f"\n馃攳 灏濊瘯鑾峰彇瀛楁:")
        problem_id = request.data.get('problem_id')
        status_field = request.data.get('status')
        solution_code = request.data.get('solution_code')
        notes = request.data.get('notes')
        
        logger.error(f"   problem_id: {problem_id} (绫诲瀷锛{type(problem_id)})")
        logger.error(f"   status: {status_field} (绫诲瀷锛{type(status_field)})")
        logger.error(f"   solution_code: {solution_code} (绫诲瀷锛{type(solution_code)})")
        logger.error(f"   notes: {notes} (绫诲瀷锛{type(notes)})")
        
        # 4. 濡傛灉鏄?dict锛岃褰曟墍鏈夐敭
        if isinstance(request.data, dict):
            logger.error(f"\n馃攽 璇锋眰浣撶殑鎵€鏈夐敭锛{list(request.data.keys())}")
        
        # 5. 鐢ㄦ埛淇℃伅
        logger.error(f"\n馃懁 鐢ㄦ埛淇℃伅:")
        logger.error(f"   user: {request.user}")
        logger.error(f"   user.id: {request.user.id}")
        logger.error(f"   user.username: {request.user.username}")
        
        logger.error("=" * 80)
        
        # 杩斿洖璋冭瘯淇℃伅缁欏墠绔?
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




