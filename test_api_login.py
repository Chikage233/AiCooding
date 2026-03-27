"""
测试 /api/user/login/ 接口 - 匹配前端格式
"""
import requests
import json
import pytest

# 测试数据
BASE_URL = 'http://127.0.0.1:8000/api/user/login/'


class TestLoginAPI:
    """登录接口测试类"""

    def test_login_with_email_success(self):
        """测试用例 1: 使用邮箱登录成功"""
        # 准备测试数据
        login_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }

        # 发送请求
        response = requests.post(BASE_URL, json=login_data)

        # 断言响应状态码
        assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"

        # 解析响应
        result = response.json()

        # 断言响应结构
        assert 'code' in result, "响应缺少 code 字段"
        assert 'data' in result, "响应缺少 data 字段"
        assert 'msg' in result, "响应缺少 msg 字段"

        # 断言 data 中的关键字段
        data = result['data']
        assert 'token' in data, "data 缺少 token 字段"
        assert 'user_id' in data, "data 缺少 user_id 字段"
        assert 'username' in data, "data 缺少 username 字段"
        assert 'email' in data, "data 缺少 email 字段"
        assert 'role' in data, "data 缺少 role 字段"

        # 断言 token 不为空
        assert len(data['token']) > 0, "token 为空"

        # 打印详细信息（使用 -s 参数时可见）
        print(f"\n✅ 登录成功!")
        print(f"   用户 ID: {data['user_id']}")
        print(f"   用户名：{data['username']}")
        print(f"   邮  箱：{data['email']}")
        print(f"   角  色：{data['role']}")
        print(f"   Token(前 50 字符): {data['token'][:50]}...")

    @pytest.mark.parametrize("username,password,description", [
        ("test@example.com", "wrong_password", "密码错误"),
        ("", "testpass123", "用户名为空"),
        ("test@example.com", "", "密码为空"),
        ("nonexistent@example.com", "testpass123", "用户不存在"),
    ])
    def test_login_failure_cases(self, username, password, description):
        """测试用例 2-5: 各种登录失败场景（参数化）"""
        login_data = {
            'username': username,
            'password': password
        }

        response = requests.post(BASE_URL, json=login_data)

        # 失败情况应该返回非 200 状态码
        assert response.status_code != 200, f"{description}: 期望失败，但返回了 200"

        print(f"\n❌ {description}: 正确返回错误状态码 {response.status_code}")

    def test_login_response_format(self):
        """测试用例 6: 验证响应格式完全匹配前端期望"""
        login_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }

        response = requests.post(BASE_URL, json=login_data)

        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})

            # 检查前端必需的所有字段
            required_fields = ['token', 'user_id', 'username', 'email', 'role', 'refresh_token']
            for field in required_fields:
                assert field in data, f"前端必需字段 '{field}' 缺失"

            print("\n🎉 响应格式完全匹配前端期望!")
            print(f"   所有必需字段都存在：{', '.join(required_fields)}")
        else:
            # 如果登录失败，跳过格式检查
            pytest.skip(f"登录失败 (状态码 {response.status_code})，无法验证响应格式")


if __name__ == '__main__':
    # 可以直接运行：python test_api_login.py
    # 或使用 pytest: pytest test_api_login.py -v
    pytest.main([__file__, '-v', '-s'])
