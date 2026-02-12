# api/tasks.py
from celery import shared_task
from django.core.cache import cache
import time

# ===================== 测试任务（先验证Celery是否能跑通） =====================
@shared_task
def test_celery_task():
    """测试Celery异步任务（模拟3秒耗时操作）"""
    time.sleep(3)  # 模拟耗时操作（比如LLM调用、代码运行）
    cache.set("celery_test", "Celery任务执行成功", 60)  # 往Redis写缓存标记
    return "Celery任务执行完成"

# ===================== 毕业设计核心任务：模拟LLM调用（后续替换为真实Qwen Max） =====================
@shared_task(bind=True, retry_backoff=3, retry_kwargs={"max_retries": 2})
def call_qwen_max_task(self, user_id, question):
    """
    异步调用Qwen Max（适配PF教学策略，不直接给答案）
    :param user_id: 用户ID
    :param question: 学生的编程问题
    :return: 引导式回复
    """
    try:
        time.sleep(2)  # 模拟LLM调用耗时
        # 引导式回复示例（符合PF教学策略）
        guide_response = f"""
        你问的问题是：{question}
        提示：先思考这个问题涉及的核心知识点（如Python循环/函数），尝试写伪代码，再逐步调试。
        例如：如果是循环问题，先确认循环条件是否正确，再测试边界值。
        """
        cache.set(f"llm_response_{user_id}", guide_response, 3600)  # 缓存结果
        return guide_response
    except Exception as e:
        self.retry(exc=e)  # 失败自动重试（3秒后重试，最多2次）

# ===================== 毕业设计核心任务：模拟作业批改 =====================
@shared_task
def grade_homework_task(homework_id, student_code):
    """
    异步批改作业（模拟代码运行+结构化反馈）
    :param homework_id: 作业ID
    :param student_code: 学生提交的代码
    :return: 批改结果
    """
    time.sleep(4)  # 模拟批改耗时
    # 结构化反馈示例（适配PF教学策略）
    feedback = {
        "score": 85,
        "error_analysis": "代码逻辑正确，但缺少异常处理（如输入非数字时的报错）",
        "guide": "建议添加try-except语句捕获异常，提升代码健壮性",
        "standard_solution": "def solve():\n    try:\n        num = int(input())\n        print(num*2)\n    except ValueError:\n        print('请输入有效数字')"
    }
    cache.set(f"homework_feedback_{homework_id}", feedback, 86400)  # 缓存批改结果
    return feedback