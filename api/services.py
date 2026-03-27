# api/services.py
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import json
import hashlib
from .qwen_client import qwen_client
from .judge0_client import judge0_client
from .models import LeetCodeProblem, ProblemCompletion
import logging

logger = logging.getLogger(__name__)

def send_verification_code(email, code):
    """
    发送验证码邮件
    """
    subject = 'AiCooding - 邮箱验证码'
    message = f'您的验证码是：{code}，请在 5 分钟内完成验证。'
    from_email = settings.DEFAULT_FROM_EMAIL

    
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"发送邮件失败：{e}")
        return False


class AIJudgeService:
    """AI 判题服务"""
    
    # 缓存过期时间：同一题目 + 同一代码的判题结果缓存 1 小时
    CACHE_TIMEOUT = 3600
    
    @classmethod
    def _generate_cache_key(cls, problem_id, user_code_hash):
        """生成缓存键"""
        return f'ai_judge:problem:{problem_id}:code:{user_code_hash}'
    
    @classmethod
    def _normalize_code(cls, code):
        """标准化代码，去除空白和注释等不影响逻辑的差异"""
        if not code:
            return ""
        # 简单处理：移除首尾空白、多余空行
        lines = code.strip().split('\n')
        normalized_lines = []
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 处理多行注释
            if '"""' in stripped or "'''" in stripped:
                quote = '"""' if '"""' in stripped else "'''"
                count = stripped.count(quote)
                if count % 2 == 1:
                    in_multiline_comment = not in_multiline_comment
                continue
            
            if in_multiline_comment:
                continue
            
            # 跳过空行和单行注释
            if not stripped or stripped.startswith('#'):
                continue
            
            normalized_lines.append(stripped)
        
        return '\n'.join(normalized_lines)
    
    @classmethod
    def judge_submission(cls, problem_id, user_code, language='python3', user=None):
        """
        AI 判题主函数
        
        Args:
            problem_id: 题目 ID
            user_code: 用户提交的代码
            language: 编程语言 (默认 python3)
            user: 当前用户对象 (可选，用于更新完成记录)
            
        Returns:
            dict: 判题结果，包含：
                - correct: bool, 是否正确
                - reason: str, 判断原因
                - error_line: str, 错误位置 (错误时)
                - error_reason: str, 错误原因 (错误时)
                - suggestion: str, 修改建议 (错误时)
                - guide_question: str, 引导性问题 (错误时)
                - standard_approach: str, 标准答案思路
                - expected_output: str, 正确输出示例
        """
        # 1. 获取题目信息
        try:
            problem = LeetCodeProblem.objects.get(problem_id=problem_id)
        except LeetCodeProblem.DoesNotExist:
            return {
                'success': False,
                'error': '题目不存在',
                'correct': False,
                'reason': '题目不存在'
            }
        
        # 2. 生成代码哈希用于缓存
        normalized_code = cls._normalize_code(user_code)
        code_hash = hashlib.md5(normalized_code.encode('utf-8')).hexdigest()
        cache_key = cls._generate_cache_key(problem_id, code_hash)
        
        # 3. 尝试从缓存获取结果
        try:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"使用缓存的判题结果：problem={problem_id}, code_hash={code_hash}")
                return cached_result
        except Exception as e:
            logger.warning(f"Redis 缓存读取失败，使用 AI 判题：{e}")
            cached_result = None
        
        # 4. 构建 AI 判题 Prompt
        prompt = f"""你是一位专业的编程老师，现在要对学生的代码进行严格判题，遵循 PF 教学策略，不直接给修正代码，而是引导学生自主思考。

【题目名称】
{problem.title}

【题目描述】
{problem.content[:2000]}  # 限制长度避免超出 token

【学生提交的代码】
```{language}
{user_code}
```

请你严格按照以下要求判断：
1. 先生成这道题的【标准答案思路】（不写完整代码）和【正确输出示例】；
2. 再判断学生代码是否正确；
3. 如果正确，返回：
   {{
     "correct": true,
     "reason": "回答正确",
     "standard_approach": "标准答案思路",
     "expected_output": "正确输出示例"
   }}
4. 如果错误，返回：
   {{
     "correct": false,
     "error_line": "错误位置（如第 5 行）",
     "error_reason": "错误原因（简洁明了）",
     "suggestion": "修改建议（不直接给代码）",
     "guide_question": "苏格拉底式引导提问（如\"你认为循环的终止条件是否考虑了边界值？\"）",
     "standard_approach": "标准答案思路",
     "expected_output": "正确输出示例"
   }}

只返回 JSON，不要多余文字。确保 JSON 格式正确。
"""
        
        # 5. 调用 AI 进行判题
        try:
            ai_result = qwen_client.simple_chat(
                prompt=prompt,
                system_prompt="你是一个专业的编程判题助手，负责分析学生代码并给出评判。你必须返回标准的 JSON 格式。",
                max_tokens=1500
            )
            
            if not ai_result['success']:
                logger.error(f"AI 判题失败：{ai_result.get('error')}")
                return {
                    'success': False,
                    'error': f'AI 判题失败：{ai_result.get("error")}',
                    'correct': False,
                    'reason': 'AI 服务不可用'
                }
            
            # 6. 解析 AI 返回的 JSON
            ai_content = ai_result['content'].strip()
            
            # 清理可能的 markdown 标记
            if ai_content.startswith('```json'):
                ai_content = ai_content[7:]
            if ai_content.endswith('```'):
                ai_content = ai_content[:-3]
            ai_content = ai_content.strip()
            
            try:
                judge_data = json.loads(ai_content)
            except json.JSONDecodeError as e:
                logger.error(f"解析 AI 返回的 JSON 失败：{e}\n内容：{ai_content}")
                # 尝试容错处理
                return {
                    'success': False,
                    'error': 'AI 返回格式错误',
                    'correct': False,
                    'reason': '判题结果解析失败，请稍后重试',
                    'raw_response': ai_content
                }
            
            # 7. 构建标准化的判题结果
            result = {
                'success': True,
                'correct': judge_data.get('correct', False),
                'reason': judge_data.get('reason', ''),
                'standard_approach': judge_data.get('standard_approach', ''),
                'expected_output': judge_data.get('expected_output', ''),
            }
            
            # 如果是错误的，添加详细错误信息
            if not result['correct']:
                result.update({
                    'error_line': judge_data.get('error_line', '未知'),
                    'error_reason': judge_data.get('error_reason', '代码存在错误'),
                    'suggestion': judge_data.get('suggestion', ''),
                    'guide_question': judge_data.get('guide_question', '')
                })
            
            # 8. 如果判题正确，更新题目通过率
            if result['correct']:
                cls._update_problem_acceptance_rate(problem)
                # 如果有用户信息，更新用户的完成记录
                if user:
                    cls._update_user_completion(problem, user, user_code)
            
            # 9. 缓存判题结果
            try:
                cache.set(cache_key, result, cls.CACHE_TIMEOUT)
                logger.info(f"已缓存判题结果：problem={problem_id}, code_hash={code_hash}")
            except Exception as e:
                logger.warning(f"Redis 缓存写入失败：{e}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI 判题过程异常：{e}")
            return {
                'success': False,
                'error': f'判题异常：{str(e)}',
                'correct': False,
                'reason': '判题过程出错，请稍后重试'
            }
    
    @classmethod
    def _update_problem_acceptance_rate(cls, problem):
        """更新题目通过率"""
        try:
            # 增加提交次数和通过次数
            problem.submission_count += 1
            problem.accepted_count += 1
            
            # 重新计算通过率
            if problem.submission_count > 0:
                problem.acceptance_rate = (problem.accepted_count / problem.submission_count) * 100
            else:
                problem.acceptance_rate = 0.0
            
            problem.save(update_fields=['submission_count', 'accepted_count', 'acceptance_rate', 'updated_at'])
            logger.info(f"已更新题目 {problem.problem_id} 的通过率：{problem.acceptance_rate:.2f}%")
        except Exception as e:
            logger.error(f"更新题目通过率失败：{e}")
    
    @classmethod
    def _update_user_completion(cls, problem, user, solution_code):
        """更新用户题目完成记录"""
        try:
            # 获取或创建完成记录
            completion, created = ProblemCompletion.objects.get_or_create(
                user=user,
                problem=problem,
                defaults={
                    'status': 'completed',
                    'attempts': 1,
                    'solution_code': solution_code,
                }
            )
            
            if not created:
                # 更新现有记录
                completion.status = 'completed'
                completion.attempts += 1
                completion.solution_code = solution_code
                completion.save()
            
            logger.info(f"已更新用户 {user.username} 的题目完成记录")
        except Exception as e:
            logger.error(f"更新完成记录失败：{e}")


def ai_judge_problem(problem_id, user_code, language='python3', user=None):
    """
    快捷函数：AI 判题
    
    Args:
        problem_id: 题目 ID
        user_code: 用户代码
        language: 编程语言
        user: 当前用户
        
    Returns:
        dict: 判题结果
    """
    return AIJudgeService.judge_submission(problem_id, user_code, language, user)