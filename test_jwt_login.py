"""
测试 JWT 登录接口
"""
import requests
import json

# 测试数据
test_cases = [
    {
        'name': '使用邮箱登录',
        'data': {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
    },
    {
        'name': '使用用户名登录',
        'data': {
            'username': 'testuser',
            'password': 'testpass123'
        }
    }
]

url = 'http://127.0.0.1:8000/auth/jwt/login/'

print("=" * 60)
print("测试 JWT 登录接口")
print("=" * 60)

for test in test_cases:
    print(f"\n{test['name']}:")
    print(f"请求 URL: {url}")
    print(f"请求数据：{json.dumps(test['data'], ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=test['data'])
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            print("✅ 登录成功!")
            result = response.json()
            print(f"响应：{json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 登录失败")
            print(f"响应：{response.text}")
    except Exception as e:
        print(f"❌ 请求异常：{e}")

print("\n" + "=" * 60)
