"""
测试 Qwen API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
django.setup()

from api.qwen_client import qwen_client

print("=" * 60)
print("测试 Qwen API - Qwen3.5-Plus")
print("=" * 60)

# 测试 1: 简单对话
print("\n【测试 1】简单对话")
result = qwen_client.simple_chat("你好，请介绍一下自己")
if result['success']:
    print(f"✅ AI 回复：{result['content'][:100]}...")
else:
    print(f"❌ 失败：{result.get('error')}")

# 测试 2: 代码解释
print("\n【测试 2】代码解释")
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
result = qwen_client.generate_code_explanation(code)
if result['success']:
    print(f"✅ 代码解释：{result['content'][:150]}...")
else:
    print(f"❌ 失败：{result.get('error')}")

# 测试 3: 代码生成
print("\n【测试 3】代码生成")
problem = "写一个函数，判断一个字符串是否是回文串"
result = qwen_client.generate_code_solution(problem)
if result['success']:
    print(f"✅ 生成的代码：\n{result['content'][:200]}...")
else:
    print(f"❌ 失败：{result.get('error')}")

# 测试 4: 代码调试
print("\n【测试 4】代码调试")
buggy_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)
"""
result = qwen_client.debug_code(buggy_code)
if result['success']:
    print(f"✅ 调试分析：{result['content'][:150]}...")
else:
    print(f"❌ 失败：{result.get('error')}")

# 测试 5: 翻译
print("\n【测试 5】翻译")
text = "Hello, welcome to use AiCooding platform!"
result = qwen_client.translate_text(text, target_language="中文")
if result['success']:
    print(f"✅ 翻译结果：{result['content']}")
else:
    print(f"❌ 失败：{result.get('error')}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
