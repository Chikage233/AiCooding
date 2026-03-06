"""
Judge0 API 使用示例

这个文件展示了如何在项目中使用 Judge0 代码判题系统
"""

# ============================================================
# 示例 1: 在 Django 视图中使用 Judge0 客户端
# ============================================================

from rest_framework.views import APIView
from rest_framework.response import Response
from api.judge0_client import judge0_client


class MyCodeExecutionView(APIView):
    """自定义代码执行视图示例"""
    
    def post(self, request):
        # 获取用户提交的代码
        code = request.data.get('code', '')
        language = request.data.get('language', 'python3')
        
        # 获取语言 ID
        language_id = judge0_client.get_language_id(language)
        
        if not language_id:
            return Response({
                'error': f'不支持的语言：{language}'
            })
        
        # 提交并等待结果
        result = judge0_client.submit_and_wait(
            source_code=code,
            language_id=language_id,
            timeout=10
        )
        
        # 返回结果给前端
        return Response({
            'output': result.get('stdout', ''),
            'error': result.get('stderr', ''),
            'status': result.get('status', {}).get('description', ''),
            'time': result.get('time', 0),
            'memory': result.get('memory', 0)
        })


# ============================================================
# 示例 2: 批量测试多段代码
# ============================================================

def test_multiple_solutions():
    """批量测试多个解决方案"""
    
    solutions = [
        {
            'name': '方案 1 - Python',
            'source_code': '''
def solve(a, b):
    return a + b

print(solve(10, 20))
''',
            'language': 'python3'
        },
        {
            'name': '方案 2 - C++',
            'source_code': '''
#include <iostream>
using namespace std;

int main() {
    int a = 10, b = 20;
    cout << (a + b) << endl;
    return 0;
}
''',
            'language': 'cpp'
        },
        {
            'name': '方案 3 - Java',
            'source_code': '''
public class Main {
    public static void main(String[] args) {
        int a = 10, b = 20;
        System.out.println(a + b);
    }
}
''',
            'language': 'java'
        }
    ]
    
    # 批量提交
    submissions = []
    for solution in solutions:
        language_id = judge0_client.get_language_id(solution['language'])
        submissions.append({
            'source_code': solution['source_code'],
            'language_id': language_id
        })
    
    # 执行批量提交
    results = judge0_client.batch_submit(submissions, wait=True)
    
    # 打印结果
    for i, (solution, result) in enumerate(zip(solutions, results)):
        print(f"\n{solution['name']}:")
        print(f"状态：{result.get('status', {}).get('description', 'Unknown')}")
        print(f"输出：{result.get('stdout', 'N/A')}")
        print(f"时间：{result.get('time', 'N/A')}秒")
        print(f"内存：{result.get('memory', 'N/A')}KB")


# ============================================================
# 示例 3: 实现 LeetCode 风格的代码判题
# ============================================================

def leetcode_style_judge():
    """LeetCode 风格的代码判题示例"""
    
    # 题目：两数之和
    problem_description = """
    给定一个整数数组 nums 和一个目标值 target，
    请你在该数组中找出和为目标值的那两个整数。
    
    示例:
    输入：nums = [2, 7, 11, 15], target = 9
    输出：[0, 1]
    """
    
    # 用户提交的代码
    user_code = """
def twoSum(nums, target):
    hashmap = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in hashmap:
            return [hashmap[complement], i]
        hashmap[num] = i
    return []

# 测试
print(twoSum([2, 7, 11, 15], 9))
"""
    
    # 期望输出
    expected_output = "[0, 1]\n"
    
    # 提交判题
    result = judge0_client.submit_and_wait(
        source_code=user_code,
        language_id=71,  # Python
        stdin="",
        expected_output=expected_output,
        timeout=10
    )
    
    # 判题结果
    status_id = result.get('status', {}).get('id')
    
    if status_id == 3:
        print("✅ 答案正确!")
    elif status_id == 4:
        print("❌ 答案错误")
        print(f"期望输出：{expected_output}")
        print(f"实际输出：{result.get('stdout', '')}")
    elif status_id == 5:
        print("❌ 超时")
    elif status_id == 6:
        print("❌ 编译错误")
        print(result.get('compile_output', ''))
    elif status_id == 7:
        print("❌ 运行时错误")
        print(result.get('stderr', ''))
    
    return result


# ============================================================
# 示例 4: 带输入的代码执行
# ============================================================

def execute_with_input():
    """执行需要标准输入的代码"""
    
    # Python 代码：读取输入并计算 A+B
    code = """
import sys

for line in sys.stdin:
    a, b = map(int, line.split())
    print(a + b)
"""
    
    # 多组测试数据
    stdin_data = "1 2\n3 4\n5 6"
    
    result = judge0_client.submit_and_wait(
        source_code=code,
        language_id=71,
        stdin=stdin_data,
        timeout=10
    )
    
    print("输入:")
    print(stdin_data)
    print("\n输出:")
    print(result.get('stdout', ''))
    # 期望输出:
    # 3
    # 7
    # 11


# ============================================================
# 示例 5: 检查代码性能
# ============================================================

def benchmark_code():
    """代码性能测试"""
    
    # 测试不同算法的性能
    algorithms = [
        {
            'name': '方法 1: 循环求和',
            'code': '''
n = 1000000
total = 0
for i in range(n):
    total += i
print(total)
'''
        },
        {
            'name': '方法 2: sum 函数',
            'code': '''
n = 1000000
print(sum(range(n)))
'''
        },
        {
            'name': '方法 3: 数学公式',
            'code': '''
n = 1000000
print(n * (n - 1) // 2)
'''
        }
    ]
    
    print("代码性能对比:\n")
    
    for algo in algorithms:
        result = judge0_client.submit_and_wait(
            source_code=algo['code'],
            language_id=71,
            timeout=10
        )
        
        print(f"{algo['name']}:")
        print(f"  执行时间：{result.get('time', 'N/A')}秒")
        print(f"  内存使用：{result.get('memory', 'N/A')}KB")
        print(f"  结果：{result.get('stdout', '').strip()}")
        print()


# ============================================================
# 示例 6: 异步提交和轮询结果
# ============================================================

def async_submission_example():
    """异步提交示例"""
    
    code = """
import time
print("开始执行...")
time.sleep(2)
print("执行完成!")
"""
    
    # 异步提交 (不等待)
    submit_result = judge0_client.submit_code(
        source_code=code,
        language_id=71
    )
    
    token = submit_result['token']
    print(f"提交成功，Token: {token}")
    
    # 手动轮询获取结果
    import time
    
    max_attempts = 20
    for i in range(max_attempts):
        result = judge0_client.get_submission(token)
        status_id = result.get('status', {}).get('id')
        
        if status_id and status_id > 2:
            print(f"\n执行完成!")
            print(f"状态：{result['status']['description']}")
            print(f"输出：{result.get('stdout', '')}")
            break
        
        print(f"等待中... ({i+1}/{max_attempts})")
        time.sleep(0.5)
    else:
        print("等待超时")


# ============================================================
# 示例 7: 检查 Judge0 服务状态
# ============================================================

def check_service_status():
    """检查 Judge0 服务状态"""
    
    # 健康检查
    is_healthy = judge0_client.health_check()
    print(f"服务状态：{'正常' if is_healthy else '异常'}")
    
    # 获取系统信息
    system_info = judge0_client.get_system_info()
    
    if system_info:
        print("\n系统信息:")
        print(f"CPU: {system_info.get('cpu_info', 'N/A')}")
        print(f"核心数：{system_info.get('cpu_count', 'N/A')}")
        print(f"内存：{system_info.get('memory_info', 'N/A')}")
        print(f"磁盘：{system_info.get('disk_info', 'N/A')}")
        print(f"Judge0 版本：{system_info.get('judge0_version', 'N/A')}")
    
    # 获取支持的语言
    languages = judge0_client.get_languages()
    print(f"\n支持的编程语言数量：{len(languages)}")


# ============================================================
# 主函数 - 运行所有示例
# ============================================================

if __name__ == '__main__':
    import os
    import sys
    import django
    
    # 设置 Django 环境
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
    django.setup()
    
    print("=" * 60)
    print("Judge0 API 使用示例")
    print("=" * 60)
    
    # 示例 1: 检查服务状态
    print("\n【示例 1】检查服务状态")
    print("-" * 60)
    check_service_status()
    
    # 示例 2: LeetCode 风格判题
    print("\n【示例 2】LeetCode 风格判题")
    print("-" * 60)
    leetcode_style_judge()
    
    # 示例 3: 带输入的代码执行
    print("\n【示例 3】带输入的代码执行")
    print("-" * 60)
    execute_with_input()
    
    # 示例 4: 代码性能测试
    print("\n【示例 4】代码性能测试")
    print("-" * 60)
    benchmark_code()
    
    print("\n" + "=" * 60)
    print("更多示例请参考 JUDGE0_API_DOC.md 文档")
    print("=" * 60)
