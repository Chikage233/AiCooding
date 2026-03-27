"""
直接测试 CurrentUserView 接口返回
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'
CURRENT_USER_URL = f'{BASE_URL}/auth/jwt/me/'

# 测试账号
EMAIL = 'test_user_20260216_003@example.com'  # 根据上面输出的用户名调整
PASSWORD = 'your_password'  # 需要修改为实际密码

def test_current_user_api():
    """测试当前用户接口"""
    print("\n" + "="*60)
    print("测试 /api/auth/jwt/me/ 接口返回")
    print("="*60)
    
    try:
        # 1. 登录
        print("\n[1] 登录获取 token...")
        login_response = requests.post(LOGIN_URL, json={
            'email': EMAIL,
            'password': PASSWORD
        })
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败：{login_response.status_code}")
            print(f"响应：{login_response.text}")
            return
        
        login_result = login_response.json()
        print(f"✅ 登录成功")
        
        token = login_result.get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            print(f"完整响应：{json.dumps(login_result, indent=2)}")
            return
        
        print(f"Token: {token[:50]}...")
        
        # 2. 调用当前用户接口
        print("\n[2] 调用 /api/auth/jwt/me/ 接口...")
        headers = {
            'Authorization': f'Bearer {token}',
        }
        
        response = requests.get(CURRENT_USER_URL, headers=headers)
        print(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 接口调用成功！")
            
            # 打印完整响应
            print(f"\n📋 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 提取统计信息
            stats = result.get('data', {}).get('stats', {})
            if stats:
                print(f"\n📊 做题统计:")
                print(f"   总完成数：{stats.get('problems_completed', 0)}")
                print(f"   简单题：{stats.get('problems_completed_easy', 0)}")
                print(f"   中等题：{stats.get('problems_completed_medium', 0)}")
                print(f"   困难题：{stats.get('problems_completed_hard', 0)}")
            else:
                print(f"\n❌ 未找到 stats 字段！")
                print(f"data 内容：{result.get('data', {})}")
        else:
            print(f"❌ 接口调用失败：{response.status_code}")
            print(f"响应：{response.text}")
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n⚠️  请确保:")
    print("1. Django 服务器正在运行")
    print("2. 已修改正确的密码")
    print("="*60)
    
    if PASSWORD == 'your_password':
        print("\n⚠️  警告：请先修改密码！")
        exit()
    
    test_current_user_api()
