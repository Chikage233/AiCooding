from django.db import models
from django.contrib.auth.models import AbstractUser

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

    USERNAME_FIELD = 'email'  # 使用邮箱作为登录字段
    REQUIRED_FIELDS = ['username']  # 创建超级用户时必需的字段

    class Meta:
        db_table = 'custom_user'
        verbose_name = '用户'
        verbose_name_plural = '用户列表'

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

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