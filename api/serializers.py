from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, LeetCodeProblem, ProblemTag, UserActivity, ProblemCompletion

class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8, help_text='密码')
    password_confirm = serializers.CharField(write_only=True, min_length=8, help_text='确认密码')
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password_confirm', 'phone', 'role', 'department')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
        }

    def validate(self, attrs):
        # 验证两次密码是否一致
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")

        # 密码强度验证
        password = attrs['password']
        if len(password) < 8:
            raise serializers.ValidationError("密码至少8位")
        if not any(c.isalpha() for c in password):
            raise serializers.ValidationError("密码必须包含字母")
        if not any(c.isdigit() for c in password):
            raise serializers.ValidationError("密码必须包含数字")

        return attrs

    def create(self, validated_data):
        # 移除确认密码字段
        validated_data.pop('password_confirm')
        # 创建用户
        user = CustomUser.objects.create_user(**validated_data)
        return user

    def validate(self, attrs):
        # 验证两次密码是否一致
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")

        # 检查用户名是否已存在
        if CustomUser.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("用户名已存在")

        # 检查邮箱是否已存在
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("邮箱已被注册")

        return attrs


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=True, help_text='账号（邮箱/用户名）')
    password = serializers.CharField(required=True, write_only=True, help_text='密码')
    
    def validate_password(self, value):
        # 密码强度验证：至少8位，包含字母和数字
        if len(value) < 8:
            raise serializers.ValidationError("密码至少8位")
        if not any(c.isalpha() for c in value):
            raise serializers.ValidationError("密码必须包含字母")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("密码必须包含数字")
        return value

    def validate(self, attrs):
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
                raise serializers.ValidationError("账号或密码错误")
        else:
            raise serializers.ValidationError("请提供账号和密码")

        attrs['user'] = user
        return attrs

class UserInfoSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'phone', 'avatar', 'role', 'role_display',
                 'department', 'date_joined', 'is_active')
        read_only_fields = ('id', 'date_joined', 'is_active')

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """用户角色更新序列化器（仅管理员可用）"""
    class Meta:
        model = CustomUser
        fields = ('role', 'department')

    def validate(self, attrs):
        return attrs


class ProblemTagSerializer(serializers.ModelSerializer):
    """题目标签序列化器"""

    class Meta:
        model = ProblemTag
        fields = ('id', 'name', 'slug', 'created_at')



class LeetCodeProblemSerializer(serializers.ModelSerializer):
    """LeetCode题目序列化器"""
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    # 删除有问题的tags_detail字段
    url = serializers.CharField(read_only=True)

    class Meta:
        model = LeetCodeProblem
        fields = (
            'id', 'problem_id', 'title', 'title_slug', 'difficulty', 'difficulty_display',
            'is_premium', 'content', 'acceptance_rate', 'submission_count', 'accepted_count',
            'tags', 'url', 'created_at', 'updated_at'
        )



class LeetCodeProblemListSerializer(serializers.ModelSerializer):
    """LeetCode题目列表序列化器（简化版）"""
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    url = serializers.CharField(read_only=True)
    # 添加用户完成状态字段
    completion_status = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()
    
    class Meta:
        model = LeetCodeProblem
        fields = (
            'id', 'problem_id', 'title', 'title_slug', 'difficulty', 'difficulty_display',
            'is_premium', 'acceptance_rate', 'tags', 'url', 'completion_status', 'user_attempts'
        )
    
    def get_completion_status(self, obj):
        """获取当前用户的题目完成状态"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                completion = ProblemCompletion.objects.get(user=request.user, problem=obj)
                return completion.get_status_display()
            except ProblemCompletion.DoesNotExist:
                return '未开始'
        return '未登录'
    
    def get_user_attempts(self, obj):
        """获取当前用户的尝试次数"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                completion = ProblemCompletion.objects.get(user=request.user, problem=obj)
                return completion.attempts
            except ProblemCompletion.DoesNotExist:
                return 0
        return 0


class UserStatsSerializer(serializers.Serializer):
    """用户统计序列化器"""
    # 基础统计
    total_users = serializers.IntegerField(read_only=True)
    active_users_today = serializers.IntegerField(read_only=True)
    active_users_week = serializers.IntegerField(read_only=True)
    active_users_month = serializers.IntegerField(read_only=True)
    
    # 注册统计
    registrations_today = serializers.IntegerField(read_only=True)
    registrations_week = serializers.IntegerField(read_only=True)
    registrations_month = serializers.IntegerField(read_only=True)
    
    # 登录统计
    logins_today = serializers.IntegerField(read_only=True)
    logins_week = serializers.IntegerField(read_only=True)
    logins_month = serializers.IntegerField(read_only=True)
    
    # 用户分布
    user_roles = serializers.DictField(read_only=True)
    user_departments = serializers.DictField(read_only=True)
    
    # 活跃度指标
    avg_activities_per_user = serializers.FloatField(read_only=True)
    most_active_users = serializers.ListField(read_only=True)
    
    # 题目完成统计
    total_problems = serializers.IntegerField(read_only=True)
    problems_completed_today = serializers.IntegerField(read_only=True)
    avg_completion_rate = serializers.FloatField(read_only=True)


class UserActivitySerializer(serializers.ModelSerializer):
    """用户活动序列化器"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True, allow_null=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = (
            'id', 'user_username', 'activity_type', 'activity_type_display',
            'problem_title', 'ip_address', 'created_at'
        )


class ProblemCompletionSerializer(serializers.ModelSerializer):
    """题目完成状态序列化器"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    
    class Meta:
        model = ProblemCompletion
        fields = (
            'id', 'user_username', 'problem_title', 'status', 'status_display',
            'attempts', 'last_attempted', 'completed_at', 'difficulty',
            'created_at', 'updated_at'
        )