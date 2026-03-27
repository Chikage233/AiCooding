"""
测试题目完成状态接口 - 验证变量命名冲突修复
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/jwt/login/'
COMPLETION_URL = f'{BASE_URL}/user/completions/'
DEBUG_COMPLETION_URL = f'{BASE_URL}/debug/user/completions/'

# 测试账号（请根据实际情况修改）
EMAIL = 'test@example.com'  # 或你的用户名
PASSWORD = 'your_password'   # 你的密码

def test_with_correct_data():
    """测试正确的数据提交"""
    print("\n" + "="*60)
    print("测试 1: 提交完整且正确的数据")
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
            return None
        
        token = login_response.json().get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            return None
        
        print(f"✅ 登录成功，token: {token[:50]}...")
        
        # 2. 提交完成状态
        print("\n[2] 提交题目完成状态...")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'problem_id': 1,
            'status': 'completed',
            'solution_code': 'print("Hello World")',
            'notes': '测试 - 验证变量命名冲突修复'
        }
        
        print(f"请求数据：{json.dumps(data, indent=2)}")
        
        response = requests.post(COMPLETION_URL, json=data, headers=headers)
        print(f"\n响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ 测试通过！接口正常工作")
            return True
        else:
            print(f"\n❌ 测试失败：{response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_missing_status():
    """测试缺少 status 字段的情况"""
    print("\n" + "="*60)
    print("测试 2: 缺少 status 字段（应该返回 400）")
    print("="*60)
    
    try:
        # 1. 登录
        print("\n[1] 登录获取 token...")
        login_response = requests.post(LOGIN_URL, json={
            'email': EMAIL,
            'password': PASSWORD
        })
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败")
            return
        
        token = login_response.json().get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            return
        
        # 2. 提交不完整数据
        print("\n[2] 提交缺少 status 的数据...")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'problem_id': 1,
            # 故意省略 status 字段
            'solution_code': 'print("test")'
        }
        
        print(f"请求数据：{json.dumps(data, indent=2)}")
        
        response = requests.post(COMPLETION_URL, json=data, headers=headers)
        print(f"\n响应状态码：{response.status_code}")
        print(f"响应内容：{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 400:
            print("\n✅ 正确返回 400 错误（符合预期）")
        else:
            print(f"\n❌ 意外响应：{response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")

def test_with_debug_interface():
    """使用调试接口查看详细数据"""
    print("\n" + "="*60)
    print("测试 3: 使用调试接口查看详细请求数据")
    print("="*60)
    
    try:
        # 1. 登录
        print("\n[1] 登录获取 token...")
        login_response = requests.post(LOGIN_URL, json={
            'email': EMAIL,
            'password': PASSWORD
        })
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败")
            return
        
        token = login_response.json().get('data', {}).get('access')
        if not token:
            print("❌ 未找到 access token")
            return
        
        # 2. 使用调试接口
        print("\n[2] 调用调试接口...")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'problem_id': 1,
            'status': 'completed',
            'solution_code': 'test',
            'notes': 'debug test'
        }
        
        response = requests.post(DEBUG_COMPLETION_URL, json=data, headers=headers)
        print(f"\n响应状态码：{response.status_code}")
        
        result = response.json()
        if response.status_code == 200:
            print("\n✅ 调试接口响应成功")
            print(f"\n提取的字段信息:")
            fields = result.get('data', {}).get('extracted_fields', {})
            for key, value in fields.items():
                print(f"  {key}: {value}")
        else:
            print(f"\n❌ 调试接口失败：{result}")
            
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")

if __name__ == '__main__':
    print("\n" + "🚀"*30)
    print("开始测试题目完成状态接口")
    print("🚀"*30)
    
    # 提示用户修改测试账号
    if EMAIL == 'test@example.com' or PASSWORD == 'your_password':
        print("\n⚠️  警告：请先修改测试账号和密码！")
        print(f"当前配置:")
        print(f"  EMAIL: {EMAIL}")
        print(f"  PASSWORD: {PASSWORD}")
        print("\n请编辑此文件并修改为实际的测试账号\n")
    else:
        # 运行测试
        success = test_with_correct_data()
        
        if success:
            test_with_missing_status()
            test_with_debug_interface()
    
    print("\n" + "="*60)
    print("测试结束")
    print("="*60)
