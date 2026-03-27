"""
测试用户统计信息接口
验证已做题数是否正确显示
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'
CURRENT_USER_URL = f'{BASE_URL}/auth/jwt/me/'
COMPLETION_URL = f'{BASE_URL}/user/completions/'

# 测试账号（请根据实际情况修改）
EMAIL = 'test@example.com'
PASSWORD = 'your_password'

def test_user_stats():
    """测试用户统计信息"""
    print("\n" + "="*60)
    print("测试用户统计信息（已做题数）")
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
            return
        
        token = login_response.json().get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            return
        
        print(f"✅ 登录成功")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 获取当前用户信息（包含统计）
        print("\n[2] 获取当前用户信息（查看统计前）...")
        user_response = requests.get(CURRENT_USER_URL, headers=headers)
        
        if user_response.status_code != 200:
            print(f"❌ 获取用户信息失败：{user_response.status_code}")
            return
        
        user_data = user_response.json()
        stats_before = user_data.get('data', {}).get('stats', {})
        
        print(f"\n📊 当前做题统计:")
        print(f"   总完成数：{stats_before.get('problems_completed', 0)}")
        print(f"   简单题：{stats_before.get('problems_completed_easy', 0)}")
        print(f"   中等题：{stats_before.get('problems_completed_medium', 0)}")
        print(f"   困难题：{stats_before.get('problems_completed_hard', 0)}")
        
        # 3. 提交一道题目
        print("\n[3] 提交一道新题目...")
        completion_data = {
            'problem_id': 1,  # LeetCode 第 1 题（通常是简单题）
            'status': 'completed',
            'solution_code': 'print("Hello World")',
            'notes': '测试统计功能'
        }
        
        completion_response = requests.post(COMPLETION_URL, json=completion_data, headers=headers)
        
        if completion_response.status_code == 200:
            print(f"✅ 提交成功")
        else:
            print(f"⚠️  提交返回：{completion_response.status_code}")
            # 继续执行，因为可能已经做过了
        
        # 4. 再次获取用户信息（查看统计后）
        print("\n[4] 再次获取用户信息（查看统计后）...")
        user_response_after = requests.get(CURRENT_USER_URL, headers=headers)
        
        if user_response_after.status_code == 200:
            user_data_after = user_response_after.json()
            stats_after = user_data_after.get('data', {}).get('stats', {})
            
            print(f"\n📊 更新后的做题统计:")
            print(f"   总完成数：{stats_after.get('problems_completed', 0)}")
            print(f"   简单题：{stats_after.get('problems_completed_easy', 0)}")
            print(f"   中等题：{stats_after.get('problems_completed_medium', 0)}")
            print(f"   困难题：{stats_after.get('problems_completed_hard', 0)}")
            
            # 5. 对比统计变化
            print("\n📈 统计变化:")
            before_total = stats_before.get('problems_completed', 0)
            after_total = stats_after.get('problems_completed', 0)
            
            if after_total > before_total:
                print(f"   ✅ 统计正确！增加了 {after_total - before_total} 道题")
            else:
                print(f"   ⚠️  统计数字没有变化（可能这道题之前已经做过了）")
                
            # 6. 显示完整响应结构
            print("\n📋 完整响应数据结构:")
            print(json.dumps(user_data_after.get('data', {}), indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ 获取用户信息失败：{user_response_after.status_code}")
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "🚀"*30)
    print("开始测试用户统计功能")
    print("🚀"*30)
    
    # 提示用户修改测试账号
    if EMAIL == 'test@example.com' or PASSWORD == 'your_password':
        print("\n⚠️  警告：请先修改测试账号和密码！")
        print(f"当前配置:")
        print(f"  EMAIL: {EMAIL}")
        print(f"  PASSWORD: {PASSWORD}")
        print("\n请编辑此文件并修改为实际的测试账号\n")
    else:
        test_user_stats()
    
    print("\n" + "="*60)
    print("测试结束")
    print("="*60)
