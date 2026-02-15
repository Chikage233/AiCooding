from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    """自定义用户模型"""
    # 用户角色选择
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    )

    email = models.EmailField(unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='手机号')
    avatar = models.URLField(blank=True, null=True, verbose_name='头像')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name='用户角色')
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name='学号')
    teacher_id = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name='教师工号')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='院系/部门')
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

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_administrator(self):
        return self.role == 'admin'

