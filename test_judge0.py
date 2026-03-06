"""
Judge0 客户端测试脚本
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
django.setup()

from api.judge0_client import judge0_client, Judge0Client


def test_health_check():
    """测试健康检查"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)
    
    is_healthy = judge0_client.health_check()
    if is_healthy:
        print("✅ Judge0 服务运行正常")
    else:
        print("❌ Judge0 服务不可用")
    
    return is_healthy


def test_get_languages():
    """测试获取编程语言列表"""
    print("\n" + "=" * 60)
    print("测试 2: 获取编程语言列表")
    print("=" * 60)
    
    languages = judge0_client.get_languages()
    
    if languages:
        print(f"✅ 成功获取 {len(languages)} 种编程语言:")
        for lang in languages[:10]:  # 只显示前 10 个
            print(f"  - ID: {lang['id']}, Name: {lang['name']}")
        
        if len(languages) > 10:
            print(f"  ... 还有 {len(languages) - 10} 种语言")
    else:
        print("❌ 获取语言列表失败")
    
    return len(languages) > 0


def test_submit_python_code():
    """测试提交 Python 代码"""
    print("\n" + "=" * 60)
    print("测试 3: 提交 Python 代码")
    print("=" * 60)
    
    source_code = """
print("Hello from Judge0!")
print("Testing Python 3.8.1")

# 简单计算
a = 10
b = 20
print(f"{a} + {b} = {a + b}")
"""
    
    language_id = judge0_client.get_language_id('python3')
    print(f"使用语言：Python (ID: {language_id})")
    
    result = judge0_client.submit_and_wait(
        source_code=source_code,
        language_id=language_id,
        timeout=10
    )
    
    status_id = result.get('status', {}).get('id')
    status_desc = result.get('status', {}).get('description', 'Unknown')
    
    print(f"\n执行状态：{status_desc} (ID: {status_id})")
    
    if result.get('stdout'):
        print(f"\n输出结果:\n{result['stdout']}")
    
    if result.get('stderr'):
        print(f"\n错误信息:\n{result['stderr']}")
    
    if result.get('compile_output'):
        print(f"\n编译输出:\n{result['compile_output']}")
    
    if result.get('time'):
        print(f"\n执行时间：{result['time']} 秒")
    
    if result.get('memory'):
        print(f"内存使用：{result['memory']} KB")
    
    # 判断是否成功 (状态 3=Accepted)
    success = status_id == 3
    if success:
        print("\n✅ Python 代码执行成功")
    else:
        print("\n❌ Python 代码执行失败")
    
    return success


def test_submit_cpp_code():
    """测试提交 C++ 代码"""
    print("\n" + "=" * 60)
    print("测试 4: 提交 C++ 代码")
    print("=" * 60)
    
    source_code = """
#include <iostream>
using namespace std;

int main() {
    cout << "Hello from C++!" << endl;
    cout << "Testing GCC 9.2.0" << endl;
    
    int a = 15;
    int b = 25;
    cout << a << " + " << b << " = " << (a + b) << endl;
    
    return 0;
}
"""
    
    language_id = judge0_client.get_language_id('cpp')
    print(f"使用语言：C++ (ID: {language_id})")
    
    result = judge0_client.submit_and_wait(
        source_code=source_code,
        language_id=language_id,
        timeout=10
    )
    
    status_id = result.get('status', {}).get('id')
    status_desc = result.get('status', {}).get('description', 'Unknown')
    
    print(f"\n执行状态：{status_desc} (ID: {status_id})")
    
    if result.get('stdout'):
        print(f"\n输出结果:\n{result['stdout']}")
    
    if result.get('stderr'):
        print(f"\n错误信息:\n{result['stderr']}")
    
    if result.get('compile_output'):
        print(f"\n编译输出:\n{result['compile_output']}")
    
    if result.get('time'):
        print(f"\n执行时间：{result['time']} 秒")
    
    if result.get('memory'):
        print(f"内存使用：{result['memory']} KB")
    
    success = status_id == 3
    if success:
        print("\n✅ C++ 代码执行成功")
    else:
        print("\n❌ C++ 代码执行失败")
    
    return success


def test_submit_java_code():
    """测试提交 Java 代码"""
    print("\n" + "=" * 60)
    print("测试 5: 提交 Java 代码")
    print("=" * 60)
    
    source_code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
        System.out.println("Testing Java 11.0.6");
        
        int a = 30;
        int b = 40;
        System.out.println(a + " + " + b + " = " + (a + b));
    }
}
"""
    
    language_id = judge0_client.get_language_id('java')
    print(f"使用语言：Java (ID: {language_id})")
    
    result = judge0_client.submit_and_wait(
        source_code=source_code,
        language_id=language_id,
        timeout=15  # Java 编译较慢，增加超时时间
    )
    
    status_id = result.get('status', {}).get('id')
    status_desc = result.get('status', {}).get('description', 'Unknown')
    
    print(f"\n执行状态：{status_desc} (ID: {status_id})")
    
    if result.get('stdout'):
        print(f"\n输出结果:\n{result['stdout']}")
    
    if result.get('stderr'):
        print(f"\n错误信息:\n{result['stderr']}")
    
    if result.get('compile_output'):
        print(f"\n编译输出:\n{result['compile_output']}")
    
    if result.get('time'):
        print(f"\n执行时间：{result['time']} 秒")
    
    if result.get('memory'):
        print(f"内存使用：{result['memory']} KB")
    
    success = status_id == 3
    if success:
        print("\n✅ Java 代码执行成功")
    else:
        print("\n❌ Java 代码执行失败")
    
    return success


def test_with_stdin():
    """测试带标准输入的代码"""
    print("\n" + "=" * 60)
    print("测试 6: 带标准输入的 Python 代码")
    print("=" * 60)
    
    source_code = """
import sys

# 读取标准输入
for line in sys.stdin:
    line = line.strip()
    if line:
        print(f"收到输入：{line}")
        print(f"输入长度：{len(line)}")
"""
    
    stdin_input = "Hello\nWorld\nTest123"
    
    language_id = judge0_client.get_language_id('python3')
    print(f"使用语言：Python (ID: {language_id})")
    print(f"标准输入：{stdin_input}")
    
    result = judge0_client.submit_and_wait(
        source_code=source_code,
        language_id=language_id,
        stdin=stdin_input,
        timeout=10
    )
    
    status_id = result.get('status', {}).get('id')
    status_desc = result.get('status', {}).get('description', 'Unknown')
    
    print(f"\n执行状态：{status_desc} (ID: {status_id})")
    
    if result.get('stdout'):
        print(f"\n输出结果:\n{result['stdout']}")
    
    if result.get('stderr'):
        print(f"\n错误信息:\n{result['stderr']}")
    
    success = status_id == 3
    if success:
        print("\n✅ 带输入的代码执行成功")
    else:
        print("\n❌ 带输入的代码执行失败")
    
    return success


def test_system_info():
    """测试获取系统信息"""
    print("\n" + "=" * 60)
    print("测试 7: 获取系统信息")
    print("=" * 60)
    
    system_info = judge0_client.get_system_info()
    
    if system_info:
        print("✅ 成功获取系统信息:")
        for key, value in system_info.items():
            print(f"  {key}: {value}")
    else:
        print("❌ 获取系统信息失败")
    
    return bool(system_info)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始 Judge0 客户端测试")
    print(f"服务器地址：{judge0_client.base_url}")
    print("=" * 60)
    
    results = {}
    
    # 测试 1: 健康检查
    results['health_check'] = test_health_check()
    
    # 测试 2: 获取语言列表
    results['get_languages'] = test_get_languages()
    
    # 测试 3: Python 代码
    results['python_code'] = test_submit_python_code()
    
    # 测试 4: C++ 代码
    results['cpp_code'] = test_submit_cpp_code()
    
    # 测试 5: Java 代码
    results['java_code'] = test_submit_java_code()
    
    # 测试 6: 带输入的代码
    results['with_stdin'] = test_with_stdin()
    
    # 测试 7: 系统信息
    results['system_info'] = test_system_info()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"总测试数：{total}")
    print(f"通过：{passed}")
    print(f"失败：{total - passed}")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  - {test_name}: {status}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过!")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
