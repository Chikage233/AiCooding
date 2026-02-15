from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser

class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=6, help_text='密码')
    password_confirm = serializers.CharField(write_only=True, min_length=6, help_text='确认密码')
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password_confirm', 'phone', 'role', 'student_id', 'teacher_id', 'department')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
        }

    def validate(self, attrs):
        # 验证两次密码是否一致
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("两次输入的密码不一致")

        # 根据角色验证必要字段
        role = attrs.get('role', 'student')
        if role == 'student' and not attrs.get('student_id'):
            raise serializers.ValidationError("学生必须提供学号")
        if role == 'teacher' and not attrs.get('teacher_id'):
            raise serializers.ValidationError("教师必须提供工号")

        return attrs

    def create(self, validated_data):
        # 移除确认密码字段
        validated_data.pop('password_confirm')
        # 创建用户
        user = CustomUser.objects.create_user(**validated_data)
        return user

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
                 'student_id', 'teacher_id', 'department', 'date_joined', 'is_active')
        read_only_fields = ('id', 'date_joined', 'is_active')

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """用户角色更新序列化器（仅管理员可用）"""
    class Meta:
        model = CustomUser
        fields = ('role', 'student_id', 'teacher_id', 'department')

    def validate(self, attrs):
        # 根据新角色验证必要字段
        role = attrs.get('role')
        if role == 'student' and not attrs.get('student_id'):
            raise serializers.ValidationError("学生必须提供学号")
        if role == 'teacher' and not attrs.get('teacher_id'):
            raise serializers.ValidationError("教师必须提供工号")
        return attrs

