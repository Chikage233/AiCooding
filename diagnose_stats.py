"""
完整诊断脚本：检查已做题数统计的整个流程
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'
CURRENT_USER_URL = f'{BASE_URL}/auth/jwt/me/'
COMPLETION_URL = f'{BASE_URL}/user/completions/'

# ========== 请根据实际情况修改 =========
EMAIL = 'test_20260216_003@example.com'
PASSWORD = 'User123456'  #
# ======================================

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_full_flow():
    """完整测试流程"""
    print_section("已做题数统计完整诊断")
    
    if PASSWORD == 'your_password':
        print("\n❌ 错误：请先修改密码！")
        print(f"当前 EMAIL: {EMAIL}")
        print(f"当前 PASSWORD: {PASSWORD}")
        return
    
    try:
        # Step 1: 登录
        print("\n[Step 1] 登录...")
        login_response = requests.post(LOGIN_URL, json={
            'username': EMAIL,  # 注意：接口需要 username 字段（实际上是邮箱）
            'password': PASSWORD
        })
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败：{login_response.status_code}")
            print(f"响应：{login_response.text}")
            return
        
        token = login_response.json().get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            return
        
        print(f"✅ 登录成功，Token: {token[:50]}...")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 2: 获取当前统计（提交前）
        print("\n[Step 2] 获取当前做题统计（提交前）...")
        user_response_before = requests.get(CURRENT_USER_URL, headers=headers)
        
        if user_response_before.status_code != 200:
            print(f"❌ 获取用户信息失败：{user_response_before.status_code}")
            return
        
        data_before = user_response_before.json()
        stats_before = data_before.get('data', {}).get('stats', {})
        
        print(f"\n📊 提交前的统计:")
        print(f"   problems_completed: {stats_before.get('problems_completed', 0)}")
        print(f"   problems_completed_easy: {stats_before.get('problems_completed_easy', 0)}")
        print(f"   problems_completed_medium: {stats_before.get('problems_completed_medium', 0)}")
        print(f"   problems_completed_hard: {stats_before.get('problems_completed_hard', 0)}")
        
        # Step 3: 提交一道新题目
        print("\n[Step 3] 提交一道新题目...")
        completion_data = {
            'problem_id': 2,  # 尝试第 2 题
            'status': 'completed',
            'solution_code': 'print("Test submission for stats")',
            'notes': '测试统计功能'
        }
        
        completion_response = requests.post(
            COMPLETION_URL, 
            json=completion_data, 
            headers=headers
        )
        
        print(f"提交响应状态码：{completion_response.status_code}")
        completion_result = completion_response.json()
        print(f"提交响应：{json.dumps(completion_result, indent=2, ensure_ascii=False)}")
        
        # Step 4: 再次获取统计（提交后）
        print("\n[Step 4] 获取提交后的做题统计...")
        user_response_after = requests.get(CURRENT_USER_URL, headers=headers)
        
        if user_response_after.status_code == 200:
            data_after = user_response_after.json()
            stats_after = data_after.get('data', {}).get('stats', {})
            
            print(f"\n📊 提交后的统计:")
            print(f"   problems_completed: {stats_after.get('problems_completed', 0)}")
            print(f"   problems_completed_easy: {stats_after.get('problems_completed_easy', 0)}")
            print(f"   problems_completed_medium: {stats_after.get('problems_completed_medium', 0)}")
            print(f"   problems_completed_hard: {stats_after.get('problems_completed_hard', 0)}")
            
            # Step 5: 对比分析
            print("\n[Step 5] 对比分析")
            before = stats_before.get('problems_completed', 0)
            after = stats_after.get('problems_completed', 0)
            
            if after > before:
                print(f"✅ 成功！统计数字增加了：{after - before}")
            else:
                print(f"⚠️  统计数字没有变化")
                print(f"   可能原因：这道题之前已经做过了")
            
            # Step 6: 显示完整响应结构供前端参考
            print("\n[Step 6] 完整响应结构（供前端解析参考）")
            print(json.dumps(data_after, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ 获取用户信息失败：{user_response_after.status_code}")
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          已做题数统计功能 - 完整诊断工具                     ║
║                                                              ║
║  功能：                                                       ║
║  1. 测试后端接口是否正确返回统计数据                         ║
║  2. 验证提交题目后统计是否更新                               ║
║  3. 提供完整响应结构供前端参考                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("⚠️  使用前必读:")
    print("  1. 确保 Django 服务器正在运行 (python manage.py runserver)")
    print("  2. 修改 EMAIL 和 PASSWORD 为实际的测试账号")
    print("  3. 数据库中应该有 LeetCode 题目数据")
    print()
    
    test_full_flow()
    
    print("\n" + "="*70)
    print("诊断完成")
    print("="*70)
