"""
测试管理员统计接口，验证题目数量是否正确返回
"""
import os
import django
import requests
import json

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
django.setup()

# 配置
BASE_URL = 'http://127.0.0.1:8000'

def test_admin_stats():
    """测试管理员统计接口"""
    print("=" * 80)
    print("测试管理员统计接口 - 验证题目数量")
    print("=" * 80)
    
    # 第一步：登录获取 token（使用管理员账号）
    login_url = f'{BASE_URL}/api/auth/jwt/login/'
    login_data = {
        'username': 'admin',  # 替换为你的管理员账号
        'password': 'admin123456'  # 替换为你的管理员密码
    }
    
    print(f"\n[1] 尝试登录：{login_url}")
    print(f"账号：{login_data['username']}")
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录状态码：{login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败：{login_response.text}")
            print("\n提示：请确保:")
            print("1. 服务器正在运行 (python manage.py runserver)")
            print("2. 账号密码正确")
            print("3. 该账号是管理员角色 (role='admin')")
            return
        
        login_data = login_response.json()
        access_token = login_data['data']['access']
        print(f"✅ 登录成功！")
        print(f"Access Token: {access_token[:50]}...")
        
    except Exception as e:
        print(f"❌ 登录请求失败：{e}")
        print("\n提示：请确保 Django 服务器正在运行")
        return
    
    # 第二步：调用管理员统计接口
    stats_url = f'{BASE_URL}/api/admin/statistics/users/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n[2] 调用管理员统计接口：{stats_url}")
    
    try:
        stats_response = requests.get(stats_url, headers=headers)
        print(f"接口状态码：{stats_response.status_code}")
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"✅ 获取统计数据成功！")
            
            # 解析数据
            data = stats_data.get('data', {})
            
            print("\n" + "=" * 80)
            print("📊 统计数据详情")
            print("=" * 80)
            
            # 用户统计
            print(f"\n👤 用户统计:")
            print(f"   - 总用户数：{data.get('total_users', 'N/A')}")
            print(f"   - 今日活跃用户：{data.get('active_users_today', 'N/A')}")
            print(f"   - 本周活跃用户：{data.get('active_users_week', 'N/A')}")
            
            # 题目统计（重点）
            print(f"\n📚 题目统计:")
            total_problems = data.get('total_problems', 'N/A')
            print(f"   - 🎯 总题目数：{total_problems} ⭐⭐⭐")
            print(f"   - 今日完成题目：{data.get('problems_completed_today', 'N/A')}")
            print(f"   - 平均完成率：{data.get('avg_completion_rate', 'N/A')}%")
            
            # 验证题目数量
            print("\n" + "=" * 80)
            print("🔍 验证结果")
            print("=" * 80)
            
            if isinstance(total_problems, int):
                if total_problems > 20:
                    print(f"✅ 正确！总题目数为 {total_problems}，不是 20")
                    print(f"   说明接口返回的是数据库中的完整题目数量")
                elif total_problems == 20:
                    print(f"⚠️  警告：总题目数正好是 20")
                    print(f"   可能数据库中确实只有 20 道题")
                    print(f"   或者接口仍有分页限制问题")
                else:
                    print(f"✅ 总题目数为 {total_problems}")
            else:
                print(f"❌ 错误：total_problems 字段不是整数：{total_problems}")
            
            # 完整响应数据
            print("\n" + "=" * 80)
            print("📄 完整响应数据:")
            print("=" * 80)
            print(json.dumps(stats_data, indent=2, ensure_ascii=False))
            
        elif stats_response.status_code == 401:
            print(f"❌ 未授权：Token 无效或过期")
        elif stats_response.status_code == 403:
            print(f"❌ 权限不足：该用户不是管理员")
        else:
            print(f"❌ 请求失败：{stats_response.text}")
            
    except Exception as e:
        print(f"❌ 请求统计接口失败：{e}")
        import traceback
        traceback.print_exc()
    
    # 第三步：对比 LeetCode 题目列表接口
    print("\n" + "=" * 80)
    print("[3] 对比 LeetCode 题目列表接口")
    print("=" * 80)
    
    problems_url = f'{BASE_URL}/api/leetcode/problems/'
    params = {'page': 1, 'page_size': 20}
    
    try:
        problems_response = requests.get(problems_url, params=params)
        print(f"接口状态码：{problems_response.status_code}")
        
        if problems_response.status_code == 200:
            problems_data = problems_response.json()
            pagination = problems_data.get('data', {}).get('pagination', {})
            
            print(f"\n📊 题目列表分页信息:")
            print(f"   - 当前页：{pagination.get('current_page', 'N/A')}")
            print(f"   - 每页数量：{pagination.get('page_size', 'N/A')}")
            print(f"   - 总记录数：{pagination.get('total_count', 'N/A')} ⭐")
            print(f"   - 总页数：{pagination.get('total_pages', 'N/A')}")
            
            problems_list = problems_data.get('data', {}).get('problems', [])
            print(f"\n⚠️  注意:")
            print(f"   - 返回的题目数组长度：{len(problems_list)}")
            print(f"   - 应该使用 pagination.total_count 获取总数，而不是数组长度")
            
    except Exception as e:
        print(f"❌ 请求题目列表接口失败：{e}")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🧪 开始测试管理员统计接口")
    print("=" * 80)
    test_admin_stats()
    print("\n" + "=" * 80)
    print("🏁 测试完成")
    print("=" * 80)
