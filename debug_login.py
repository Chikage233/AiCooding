"""
调试 JWT 登录 - 查看实际接收的数据
"""
import requests
import json

# 测试不同的字段组合
test_cases = [
    {
        'name': '使用 username 字段 (邮箱)',
        'data': {'username': 'test@example.com', 'password': 'testpass123'},
        'content_type': 'application/json'
    },
    {
        'name': '使用 email 字段',
        'data': {'email': 'test@example.com', 'password': 'testpass123'},
        'content_type': 'application/json'
    },
    {
        'name': '使用 form-data 格式',
        'data': {'username': 'test@example.com', 'password': 'testpass123'},
        'content_type': 'application/x-www-form-urlencoded'
    }
]

url = 'http://127.0.0.1:8000/auth/jwt/login/'

print("=" * 60)
print("调试 JWT 登录 - 测试不同字段组合")
print("=" * 60)

for test in test_cases:
    print(f"\n{test['name']}:")
    print(f"  请求数据：{json.dumps(test['data'], ensure_ascii=False)}")
    print(f"  Content-Type: {test['content_type']}")
    
    try:
        if test['content_type'] == 'application/json':
            response = requests.post(url, json=test['data'])
        else:
            response = requests.post(url, data=test['data'])
            
        print(f"  状态码：{response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ 成功!")
            result = response.json()
            print(f"  响应：{json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
        else:
            print(f"  ❌ 失败")
            print(f"  响应：{response.text}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

print("\n" + "=" * 60)
print("\n建议:")
print("1. 检查前端发送的字段名是 'username' 还是 'email'")
print("2. 检查 Content-Type 是否为 'application/json'")
print("3. 确保请求体格式正确")
