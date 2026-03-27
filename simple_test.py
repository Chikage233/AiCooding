"""
快速测试登录和统计接口
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'  # 使用 JWT 登录接口
CURRENT_USER_URL = f'{BASE_URL}/auth/jwt/me/'

# 测试账号
USERNAME = 'test_20260216_003@example.com'  # 用户名（邮箱）
PASSWORD = 'User123456'

def quick_test():
    print("="*60)
    print("快速测试登录和统计接口")
    print("="*60)
    
    # 1. 登录
    print("\n[1] 尝试登录...")
    print(f"用户名：{USERNAME}")
    print(f"密码：{PASSWORD}")
    
    login_data = {
        'username': USERNAME,  # 使用 username 字段
        'password': PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        print(f"\n响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 登录成功！")
            print(f"\n完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 获取 token
            token = result.get('data', {}).get('token') or result.get('data', {}).get('access')
            if not token:
                print(f"\n❌ 未找到 token!")
                return
            
            print(f"\nToken: {token[:50]}...")
            
            # 2. 获取用户信息
            print(f"\n[2] 获取用户信息...")
            headers = {'Authorization': f'Bearer {token}'}
            user_response = requests.get(CURRENT_USER_URL, headers=headers)
            
            print(f"响应状态码：{user_response.status_code}")
            
            if user_response.status_code == 200:
                user_result = user_response.json()
                print(f"\n✅ 获取成功！")
                print(f"\n完整响应:")
                print(json.dumps(user_result, indent=2, ensure_ascii=False))
                
                # 提取统计
                stats = user_result.get('data', {}).get('stats', {})
                if stats:
                    print(f"\n📊 做题统计:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"\n⚠️  未找到 stats 字段")
            else:
                print(f"\n❌ 获取用户信息失败：{user_response.text}")
        else:
            print(f"\n❌ 登录失败：{response.text}")
            
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_test()
