# test_ai_judge.py
"""
测试 AI 判题功能
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
django.setup()

from api.services import AIJudgeService

print("=" * 80)
print("AI 判题功能测试")
print("=" * 80)

# 测试用例 1：正确代码
print("\n【测试 1】正确代码")
print("-" * 80)

correct_code = """
def two_sum(nums, target):
    hash_map = {}
    for i, num in enumerate(nums):
        if target - num in hash_map:
            return [hash_map[target - num], i]
        hash_map[num] = i
    return []
"""

print("提交代码:")
print(correct_code)
print("\n判题中...")

start_time = time.time()
result = AIJudgeService.judge_submission(
    problem_id=1,
    user_code=correct_code,
    language='python3'
)
end_time = time.time()

print(f"\n⏱️  响应时间：{end_time - start_time:.3f}秒")
print(f"✅ 是否正确：{result.get('correct')}")
print(f"📝 原因：{result.get('reason')}")
print(f"💡 标准思路：{result.get('standard_approach')}")
print(f"🎯 预期输出：{result.get('expected_output')}")

if result.get('success'):
    print("✨ 判题成功！")
else:
    print(f"❌ 判题失败：{result.get('error')}")

# 测试用例 2：错误代码
print("\n" + "=" * 80)
print("【测试 2】错误代码")
print("-" * 80)

wrong_code = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
"""

print("提交代码:")
print(wrong_code)
print("\n判题中...")

start_time = time.time()
result2 = AIJudgeService.judge_submission(
    problem_id=1,
    user_code=wrong_code,
    language='python3'
)
end_time = time.time()

print(f"\n⏱️  响应时间：{end_time - start_time:.3f}秒")
print(f"❌ 是否正确：{result2.get('correct')}")

if not result2.get('correct'):
    print(f"📍 错误位置：{result2.get('error_line')}")
    print(f"🔍 错误原因：{result2.get('error_reason')}")
    print(f"💡 修改建议：{result2.get('suggestion')}")
    print(f"❓ 引导问题：{result2.get('guide_question')}")
    print(f"💪 标准思路：{result2.get('standard_approach')}")

# 测试用例 3：缓存测试（重复提交相同代码）
print("\n" + "=" * 80)
print("【测试 3】缓存测试（第二次提交相同正确代码）")
print("-" * 80)

print("再次提交相同的正确代码...")
start_time = time.time()
result3 = AIJudgeService.judge_submission(
    problem_id=1,
    user_code=correct_code,
    language='python3'
)
end_time = time.time()

print(f"\n⏱️  响应时间：{end_time - start_time:.3f}秒")
print(f"✅ 是否正确：{result3.get('correct')}")

# 计算性能提升
if end_time - start_time < 1.0:
    print("🚀 使用了 Redis 缓存！性能大幅提升！")
else:
    print("⚠️  未使用缓存或缓存失效")

# 测试用例 4：边界情况测试
print("\n" + "=" * 80)
print("【测试 4】边界情况测试（不存在的题目）")
print("-" * 80)

result4 = AIJudgeService.judge_submission(
    problem_id=999999,
    user_code=correct_code,
    language='python3'
)

print(f"判题结果：{result4}")
print(f"是否成功：{result4.get('success')}")
print(f"错误信息：{result4.get('error')}")

# 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print(f"✅ 测试 1 (正确代码): {'通过' if result.get('correct') else '失败'}")
print(f"✅ 测试 2 (错误代码): {'通过' if not result2.get('correct') and result2.get('error_line') else '失败'}")
print(f"✅ 测试 3 (缓存测试): {'通过' if end_time - start_time < 1.0 else '失败'}")
print(f"✅ 测试 4 (异常处理): {'通过' if not result4.get('success') else '失败'}")

print("\n所有测试完成！")
