from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, LeetCodeProblem, ProblemTag

class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=6, help_text='密码')
    password_confirm = serializers.CharField(write_only=True, min_length=6, help_text='确认密码')
    
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
    email = serializers.EmailField(required=True, help_text='邮箱')
    password = serializers.CharField(required=True, write_only=True, help_text='密码')

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # 验证用户
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("邮箱或密码错误")
        else:
            raise serializers.ValidationError("请提供邮箱和密码")

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
    tags_detail = ProblemTagSerializer(many=True, read_only=True, source='tags')
    url = serializers.CharField(read_only=True)

    class Meta:
        model = LeetCodeProblem
        fields = (
            'id', 'problem_id', 'title', 'title_slug', 'difficulty', 'difficulty_display',
            'is_premium', 'content', 'acceptance_rate', 'submission_count', 'accepted_count',
            'tags', 'tags_detail', 'url', 'created_at', 'updated_at'
        )


class LeetCodeProblemListSerializer(serializers.ModelSerializer):
    """LeetCode题目列表序列化器（简化版）"""
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    url = serializers.CharField(read_only=True)

    class Meta:
        model = LeetCodeProblem
        fields = (
            'id', 'problem_id', 'title', 'title_slug', 'difficulty', 'difficulty_display',
            'is_premium', 'acceptance_rate', 'tags', 'url'
        )