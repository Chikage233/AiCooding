"""
测试题目完成状态更新接口
"""
import requests
import json

# 配置
BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'
COMPLETION_URL = f'{BASE_URL}/user/completions/'

# 测试账号
EMAIL = 'test@example.com'
PASSWORD = 'testpassword123'

def test_completion_api():
    print("=" * 60)
    print("测试题目完成状态更新接口")
    print("=" * 60)
    
    # 1. 登录获取 token
    print("\n[步骤 1] 登录获取 JWT token...")
    login_data = {
        'email': EMAIL,
        'password': PASSWORD
    }
    
    try:
        login_response = requests.post(LOGIN_URL, json=login_data)
        print(f"登录响应状态码：{login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败：{login_response.text}")
            return
        
        login_result = login_response.json()
        print(f"✅ 登录成功")
        
        # 提取 access token
        access_token = login_result.get('data', {}).get('access')
        if not access_token:
            print("❌ 未找到 access token")
            return
        
        print(f"Token: {access_token[:50]}...")
        
    except Exception as e:
        print(f"❌ 登录异常：{e}")
        return
    
    # 2. 测试更新题目完成状态
    print("\n[步骤 2] 测试更新题目完成状态...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 测试数据 - 使用 LeetCode 题目 ID（不是数据库主键）
    completion_data = {
        'problem_id': 1,  # LeetCode 第 1 题的 ID
        'status': 'completed',
        'solution_code': 'print("Hello World")',
        'notes': '测试笔记 - 第一次尝试就成功了'
    }
    
    try:
        response = requests.post(COMPLETION_URL, json=completion_data, headers=headers)
        print(f"提交响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ 测试成功！接口正常工作")
        else:
            print(f"\n❌ 测试失败，状态码：{response.status_code}")
            
    except Exception as e:
        print(f"❌ 提交异常：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_completion_api()
