"""
测试 Django authenticate 函数在 CustomUser 下的行为
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
django.setup()

from django.contrib.auth import authenticate
from api.models import CustomUser

print("=" * 60)
print("测试 Django authenticate 函数行为")
print("=" * 60)

# 1. 检查 CustomUser 的配置
print(f"\n1. CustomUser 的 USERNAME_FIELD: {CustomUser.USERNAME_FIELD}")
print(f"2. CustomUser 的 REQUIRED_FIELDS: {CustomUser.REQUIRED_FIELDS}")

# 3. 尝试获取或创建测试用户
print("\n3. 查找测试用户...")
try:
    test_user = CustomUser.objects.get(email='test@example.com')
    print(f"   找到用户：{test_user.email}, username: {test_user.username}")
except CustomUser.DoesNotExist:
    print("   测试用户不存在，尝试创建...")
    try:
        test_user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        print(f"   ✅ 创建成功：{test_user.email}, username: {test_user.username}")
    except Exception as e:
        print(f"   ❌ 创建失败：{e}")
        test_user = None

if test_user:
    # 4. 测试不同的 authenticate 调用方式
    print("\n4. 测试 authenticate 函数:")
    
    # 方式 1: 传递 username 参数 (值包含@)
    print("\n   方式 1: authenticate(username='test@example.com', password='testpass123')")
    user1 = authenticate(username='test@example.com', password='testpass123')
    if user1:
        print(f"   ✅ 认证成功：{user1.email}")
    else:
        print(f"   ❌ 认证失败")
    
    # 方式 2: 传递 email 参数
    print("\n   方式 2: authenticate(email='test@example.com', password='testpass123')")
    user2 = authenticate(email='test@example.com', password='testpass123')
    if user2:
        print(f"   ✅ 认证成功：{user2.email}")
    else:
        print(f"   ❌ 认证失败")
    
    # 方式 3: 传递 username 参数 (用户名不含@)
    print("\n   方式 3: authenticate(username='testuser', password='testpass123')")
    user3 = authenticate(username='testuser', password='testpass123')
    if user3:
        print(f"   ✅ 认证成功：{user3.email}")
    else:
        print(f"   ❌ 认证失败")

print("\n" + "=" * 60)
