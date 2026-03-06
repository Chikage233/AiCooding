"""
测试 /api/user/login/ 接口 - 匹配前端格式
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
    }
]

url = 'http://127.0.0.1:8000/api/user/login/'

print("=" * 60)
print("测试 /api/user/login/ 接口 (前端期望的格式)")
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
            print(f"\n响应结构:")
            print(f"  code: {result.get('code')}")
            print(f"  msg: {result.get('msg')}")
            print(f"\n  data.token: {result.get('data', {}).get('token', '')[:50]}...")
            print(f"  data.user_id: {result.get('data', {}).get('user_id')}")
            print(f"  data.username: {result.get('data', {}).get('username')}")
            print(f"  data.email: {result.get('data', {}).get('email')}")
            print(f"  data.role: {result.get('data', {}).get('role')}")
            print(f"  data.refresh_token: {result.get('data', {}).get('refresh_token', '')[:50]}...")
            
            # 验证响应格式是否匹配前端期望
            print("\n✅ 响应格式检查:")
            has_token = 'token' in result.get('data', {})
            has_user_id = 'user_id' in result.get('data', {})
            has_username = 'username' in result.get('data', {})
            
            print(f"  ✓ 包含 token 字段：{has_token}")
            print(f"  ✓ 包含 user_id 字段：{has_user_id}")
            print(f"  ✓ 包含 username 字段：{has_username}")
            
            if has_token and has_user_id and has_username:
                print("\n🎉 响应格式完全匹配前端期望!")
            else:
                print("\n⚠️  响应格式与前端期望不完全匹配")
                
        else:
            print(f"❌ 登录失败")
            print(f"响应：{response.text}")
    except Exception as e:
        print(f"❌ 请求异常：{e}")

print("\n" + "=" * 60)
