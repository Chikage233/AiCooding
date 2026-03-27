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



# ... existing code ...

class LeetCodeProblemListSerializer(serializers.ModelSerializer):
    """LeetCode 题目列表序列化器（简化版）"""
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
        # 使用预加载的完成状态
        if hasattr(obj, '_cached_completion'):
            completion = obj._cached_completion
            if completion:
                return completion.get_status_display()
            return '未开始'

        # 降级处理（不应该是主要路径）
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
        # 使用预加载的完成状态
        if hasattr(obj, '_cached_completion'):
            completion = obj._cached_completion
            if completion:
                return completion.attempts
            return 0

        # 降级处理（不应该是主要路径）
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                completion = ProblemCompletion.objects.get(user=request.user, problem=obj)
                return completion.attempts
            except ProblemCompletion.DoesNotExist:
                return 0
        return 0

# ... existing code ...



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


# 验证码相关序列化器
class SendVerificationCodeSerializer(serializers.Serializer):
    """发送验证码序列化器"""
    email = serializers.EmailField(required=True, help_text='邮箱地址')
    
    def validate_email(self, value):
        # 检查邮箱格式
        if not value or '@' not in value:
            raise serializers.ValidationError("请输入有效的邮箱地址")
        
        # 检查邮箱是否已被注册
        from .models import CustomUser
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        
        return value
    
    def create(self, validated_data):
        email = validated_data['email']
        
        # 生成验证码
        from .models import EmailVerificationCode
        verification_code = EmailVerificationCode.generate_code(email)
        
        # 发送邮件
        from .services import send_verification_code
        success = send_verification_code(email, verification_code.code)
        
        if not success:
            # 如果发送失败，删除验证码记录
            verification_code.delete()
            raise serializers.ValidationError("验证码发送失败，请稍后重试")
        
        return {
            'email': email,
            'message': '验证码已发送，请查收邮箱'
        }


class VerifyCodeSerializer(serializers.Serializer):
    """验证码验证序列化器"""
    email = serializers.EmailField(required=True, help_text='邮箱地址')
    code = serializers.CharField(max_length=6, required=True, help_text='验证码')
    
    def validate(self, attrs):
        email = attrs['email']
        code = attrs['code']
        
        # 查找验证码记录
        from .models import EmailVerificationCode
        try:
            verification_code = EmailVerificationCode.objects.get(
                email=email,
                code=code,
                is_used=False
            )
            
            # 检查验证码是否过期
            if not verification_code.is_valid():
                raise serializers.ValidationError("验证码已过期或无效")
                
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码错误或不存在")
        
        attrs['verification_code'] = verification_code
        return attrs


class UserRegisterWithCodeSerializer(UserRegisterSerializer):
    """带验证码的用户注册序列化器"""
    verification_code = serializers.CharField(max_length=6, write_only=True, help_text='验证码')
    
    def validate(self, attrs):
        # 先执行父类的验证
        super().validate(attrs)
        
        # 验证验证码
        email = attrs['email']
        code = attrs['verification_code']
        
        from .models import EmailVerificationCode
        try:
            verification_code = EmailVerificationCode.objects.get(
                email=email,
                code=code,
                is_used=False
            )
            
            if not verification_code.is_valid():
                raise serializers.ValidationError("验证码已过期或无效")
                
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("验证码错误或不存在")
        
        # 标记验证码为已使用
        verification_code.is_used = True
        verification_code.save()
        
        return attrs


# ==================== Judge0 代码判题相关序列化器 ====================

class CodeSubmissionSerializer(serializers.Serializer):
    """代码提交序列化器"""
    source_code = serializers.CharField(required=True, help_text='源代码')
    language_id = serializers.IntegerField(required=True, help_text='编程语言 ID')
    stdin = serializers.CharField(required=False, allow_blank=True, help_text='标准输入')
    expected_output = serializers.CharField(required=False, allow_blank=True, help_text='期望输出')
    cpu_time_limit = serializers.FloatField(required=False, default=5.0, help_text='CPU 时间限制 (秒)')
    memory_limit = serializers.IntegerField(required=False, default=128000, help_text='内存限制 (KB)')
    stack_limit = serializers.IntegerField(required=False, default=64000, help_text='栈限制 (KB)')
    max_processes_and_or_threads = serializers.IntegerField(required=False, default=60, help_text='最大进程/线程数')
    enable_per_process_and_thread_time_limit = serializers.BooleanField(required=False, default=False, help_text='是否启用每个进程/线程的时间限制')
    enable_per_process_and_thread_memory_limit = serializers.BooleanField(required=False, default=False, help_text='是否启用每个进程/线程的内存限制')
    max_file_size = serializers.IntegerField(required=False, help_text='最大文件大小 (字节)')
    redirect_stderr_to_stdout = serializers.BooleanField(required=False, default=False, help_text='是否将标准错误重定向到标准输出')
    compiler_options = serializers.CharField(required=False, allow_blank=True, help_text='编译器选项')
    command_line_arguments = serializers.CharField(required=False, allow_blank=True, help_text='命令行参数')
    number_of_runs = serializers.IntegerField(required=False, default=1, help_text='运行次数')
    
    def validate_source_code(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("源代码不能为空")
        return value
    
    def validate_language_id(self, value):
        # 只检查 language_id 是否为正整数，不限制具体值
        # 因为 Judge0 服务器支持的语言 ID 可能会变化
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("语言 ID 必须是正整数")
        return value
    
    def validate_cpu_time_limit(self, value):
        if value and (value <= 0 or value > 30):
            raise serializers.ValidationError("CPU 时间限制必须在 0-30 秒之间")
        return value
    
    def validate_memory_limit(self, value):
        if value and (value <= 0 or value > 512000):
            raise serializers.ValidationError("内存限制必须在 0-512000 KB 之间")
        return value


class CodeSubmissionResponseSerializer(serializers.Serializer):
    """代码提交响应序列化器"""
    token = serializers.CharField(help_text='提交令牌')
    status = serializers.DictField(help_text='状态信息')
    stdout = serializers.CharField(allow_null=True, help_text='标准输出')
    stderr = serializers.CharField(allow_null=True, help_text='标准错误输出')
    compile_output = serializers.CharField(allow_null=True, help_text='编译输出')
    message = serializers.CharField(allow_null=True, help_text='系统信息')
    exit_code = serializers.IntegerField(allow_null=True, help_text='退出码')
    exit_signal = serializers.IntegerField(allow_null=True, help_text='退出信号')
    time = serializers.FloatField(allow_null=True, help_text='执行时间 (秒)')
    wall_time = serializers.FloatField(allow_null=True, help_text='实际耗时 (秒)')
    memory = serializers.IntegerField(allow_null=True, help_text='内存使用 (KB)')
    created_at = serializers.DateTimeField(allow_null=True, help_text='创建时间')
    finished_at = serializers.DateTimeField(allow_null=True, help_text='完成时间')


class LanguageInfoSerializer(serializers.Serializer):
    """编程语言信息序列化器"""
    id = serializers.IntegerField(help_text='语言 ID')
    name = serializers.CharField(help_text='语言名称')
    is_archived = serializers.BooleanField(required=False, help_text='是否已归档')
    source_file = serializers.CharField(required=False, allow_null=True, help_text='源文件名')
    compile_cmd = serializers.CharField(required=False, allow_null=True, help_text='编译命令')
    run_cmd = serializers.CharField(required=False, allow_null=True, help_text='运行命令')


class BatchSubmissionSerializer(serializers.Serializer):
    """批量代码提交序列化器"""
    submissions = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text='提交列表',
        min_length=1,
        max_length=20
    )
    wait = serializers.BooleanField(required=False, default=True, help_text='是否等待结果')
    
    def validate_submissions(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("批量提交最多支持 20 个代码")
        
        for i, submission in enumerate(value):
            if 'source_code' not in submission or 'language_id' not in submission:
                raise serializers.ValidationError(f"第 {i+1} 个提交缺少必需字段 (source_code, language_id)")
        
        return value


class SystemInfoSerializer(serializers.Serializer):
    """系统信息序列化器"""
    cpu_info = serializers.CharField(allow_null=True, help_text='CPU 信息')
    cpu_count = serializers.IntegerField(allow_null=True, help_text='CPU 核心数')
    memory_info = serializers.CharField(allow_null=True, help_text='内存信息')
    disk_info = serializers.CharField(allow_null=True, help_text='磁盘信息')
    judge0_version = serializers.CharField(allow_null=True, help_text='Judge0 版本')
