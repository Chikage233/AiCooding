# api/ai_judge_views.py
"""
AI 判题系统 API 视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .services import AIJudgeService
from .models import LeetCodeProblem, ProblemCompletion
import logging

logger = logging.getLogger(__name__)


class AIJudgeSubmitView(APIView):
    """AI 判题提交接口"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        提交代码进行 AI 判题
        
        Request Body:
        - problem_id: 题目 ID (必填)
        - source_code: 用户提交的源代码 (必填)
        - language: 编程语言 (可选，默认 python3)
        
        Response:
        - correct: bool, 代码是否正确
        - reason: str, 判断原因
        - error_line: str, 错误位置 (错误时)
        - error_reason: str, 错误原因 (错误时)
        - suggestion: str, 修改建议 (错误时)
        - guide_question: str, 引导性问题 (错误时)
        - standard_approach: str, 标准答案思路
        - expected_output: str, 正确输出示例
        - can_submit: bool, 是否可以提交 (正确时)
        """
        problem_id = request.data.get('problem_id')
        source_code = request.data.get('source_code')
        language = request.data.get('language', 'python3')
        
        # 参数验证
        if not problem_id:
            return Response({
                'code': 400,
                'message': '请提供题目 ID',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not source_code:
            return Response({
                'code': 400,
                'message': '请提交源代码',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 调用 AI 判题服务
            judge_result = AIJudgeService.judge_submission(
                problem_id=problem_id,
                user_code=source_code,
                language=language,
                user=request.user
            )
            
            # 如果判题失败
            if not judge_result.get('success'):
                return Response({
                    'code': 500,
                    'message': judge_result.get('error', '判题失败'),
                    'data': judge_result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 构建响应数据
            response_data = {
                'correct': judge_result['correct'],
                'reason': judge_result.get('reason', ''),
                'standard_approach': judge_result.get('standard_approach', ''),
                'expected_output': judge_result.get('expected_output', ''),
            }
            
            # 如果错误，添加详细信息
            if not judge_result['correct']:
                response_data.update({
                    'error_line': judge_result.get('error_line', ''),
                    'error_reason': judge_result.get('error_reason', ''),
                    'suggestion': judge_result.get('suggestion', ''),
                    'guide_question': judge_result.get('guide_question', '')
                })
            
            # 如果正确，添加提交成功标志
            if judge_result['correct']:
                response_data['can_submit'] = True
                response_data['message'] = '恭喜！答案正确，可以提交'
            
            return Response({
                'code': 200,
                'message': '判题成功' if judge_result['success'] else '判题完成',
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"AI 判题接口异常：{e}")
            return Response({
                'code': 500,
                'message': f'服务器错误：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_and_complete_problem(request):
    """
    一体化判题接口（推荐使用）
    
    这个接口会：
    1. 进行 AI 判题
    2. 如果正确，自动创建/更新完成记录
    3. 更新题目通过率
    
    Request Body:
    - problem_id: 题目 ID
    - source_code: 源代码
    - language: 编程语言 (可选)
    - notes: 笔记 (可选)
    """
    problem_id = request.data.get('problem_id')
    source_code = request.data.get('source_code')
    language = request.data.get('language', 'python3')
    notes = request.data.get('notes', '')
    
    if not problem_id or not source_code:
        return Response({
            'code': 400,
            'message': '请提供题目 ID 和源代码',
            'data': {}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 1. AI 判题
        judge_result = AIJudgeService.judge_submission(
            problem_id=problem_id,
            user_code=source_code,
            language=language,
            user=request.user
        )
        
        if not judge_result.get('success'):
            return Response({
                'code': 500,
                'message': judge_result.get('error', '判题失败'),
                'data': judge_result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 2. 构建基础响应
        response_data = {
            'correct': judge_result['correct'],
            'reason': judge_result.get('reason', ''),
            'standard_approach': judge_result.get('standard_approach', ''),
        }
        
        # 3. 如果正确，更新完成记录
        if judge_result['correct']:
            try:
                problem = LeetCodeProblem.objects.get(problem_id=problem_id)
                
                # 获取或创建完成记录
                completion, created = ProblemCompletion.objects.get_or_create(
                    user=request.user,
                    problem=problem,
                    defaults={
                        'status': 'completed',
                        'attempts': 1,
                        'solution_code': source_code,
                        'notes': notes
                    }
                )
                
                if not created:
                    # 更新现有记录
                    completion.status = 'completed'
                    completion.attempts += 1
                    completion.solution_code = source_code
                    if notes:
                        completion.notes = notes
                    completion.save()
                
                response_data['completion'] = {
                    'id': completion.id,
                    'status': completion.get_status_display(),
                    'attempts': completion.attempts,
                    'completed_at': completion.completed_at.isoformat() if completion.completed_at else None
                }
                
            except Exception as e:
                logger.error(f"更新完成记录失败：{e}")
                # 不影响主要流程，继续返回
        
        # 4. 添加错误详情（如果有）
        if not judge_result['correct']:
            response_data.update({
                'error_line': judge_result.get('error_line', ''),
                'error_reason': judge_result.get('error_reason', ''),
                'suggestion': judge_result.get('suggestion', ''),
                'guide_question': judge_result.get('guide_question', '')
            })
        
        return Response({
            'code': 200,
            'message': '判题完成',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"一体化判题接口异常：{e}")
        return Response({
            'code': 500,
            'message': f'服务器错误：{str(e)}',
            'data': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
