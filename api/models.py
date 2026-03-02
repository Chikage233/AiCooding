from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.
class CustomUser(AbstractUser):
    """自定义用户模型"""
    # 用户角色选择
    ROLE_CHOICES = (
        ('user', '用户'),
        ('admin', '管理员'),
    )

    email = models.EmailField(unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='手机号')
    avatar = models.URLField(blank=True, null=True, verbose_name='头像')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='用户角色')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='部门')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 添加is_staff字段以匹配前端判断逻辑
    is_staff = models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')
    
    USERNAME_FIELD = 'email'  # 使用邮箱作为登录字段
    REQUIRED_FIELDS = ['username']  # 创建超级用户时必需的字段

    class Meta:
        db_table = 'custom_user'
        verbose_name = '用户'
        verbose_name_plural = '用户列表'

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # 当角色为admin时，自动设置is_staff为True
        if self.role == 'admin':
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

    def is_user(self):
        return self.role == 'user'

    def is_administrator(self):
        return self.role == 'admin'


class LeetCodeProblem(models.Model):
    """LeetCode题目模型"""
    DIFFICULTY_CHOICES = (
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    )

    # 基本信息
    problem_id = models.IntegerField(unique=True, verbose_name='题目ID')
    title = models.CharField(max_length=200, verbose_name='题目标题')
    title_slug = models.SlugField(max_length=200, unique=True, verbose_name='题目slug')

    # 难度和状态
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name='难度')
    is_premium = models.BooleanField(default=False, verbose_name='是否为会员题')

    # 描述和统计
    content = models.TextField(blank=True, verbose_name='题目描述')
    acceptance_rate = models.FloatField(default=0.0, verbose_name='通过率')
    submission_count = models.IntegerField(default=0, verbose_name='提交次数')
    accepted_count = models.IntegerField(default=0, verbose_name='通过次数')

    # 标签
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'leetcode_problem'
        verbose_name = 'LeetCode题目'
        verbose_name_plural = 'LeetCode题目列表'
        ordering = ['problem_id']

    def __str__(self):
        return f"{self.problem_id}. {self.title}"

    @property
    def url(self):
        """返回LeetCode题目链接"""
        return f"https://leetcode.cn/problems/{self.title_slug}/"


class ProblemTag(models.Model):
    """题目标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='标签slug')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'problem_tag'
        verbose_name = '题目标签'
        verbose_name_plural = '题目标签列表'
        ordering = ['name']

    def __str__(self):
        return self.name


class UserActivity(models.Model):
    """用户活跃度追踪模型"""
    ACTIVITY_TYPES = (
        ('login', '登录'),
        ('view_problem', '查看题目'),
        ('submit_solution', '提交解答'),
        ('complete_problem', '完成题目'),
        ('profile_update', '更新资料'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='用户')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name='活动类型')
    problem = models.ForeignKey(LeetCodeProblem, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='相关题目')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='活动时间')
    
    class Meta:
        db_table = 'user_activity'
        verbose_name = '用户活动'
        verbose_name_plural = '用户活动记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"


class ProblemCompletion(models.Model):
    """题目完成状态模型"""
    COMPLETION_STATUS = (
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='用户')
    problem = models.ForeignKey(LeetCodeProblem, on_delete=models.CASCADE, verbose_name='题目')
    status = models.CharField(max_length=15, choices=COMPLETION_STATUS, default='not_started', verbose_name='完成状态')
    attempts = models.IntegerField(default=0, verbose_name='尝试次数')
    last_attempted = models.DateTimeField(null=True, blank=True, verbose_name='最后尝试时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    solution_code = models.TextField(blank=True, verbose_name='解决方案代码')
    notes = models.TextField(blank=True, verbose_name='笔记')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'problem_completion'
        verbose_name = '题目完成状态'
        verbose_name_plural = '题目完成状态记录'
        unique_together = ['user', 'problem']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['problem', 'status']),
            models.Index(fields=['user', '-completed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.title} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # 自动更新完成时间
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)