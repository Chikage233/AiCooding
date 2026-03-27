"""
调试题目完成状态接口的 500 错误
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class DebugProblemCompletionsView(APIView):
    """调试用的题目完成状态视图 - 用于查看详细请求数据"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """记录所有请求详情"""
        logger.error("=" * 80)
        logger.error("🔍 收到 POST 请求 - 详细调试信息")
        logger.error("=" * 80)
        
        # 1. 记录请求头
        logger.error(f"📋 请求头:")
        for key, value in request.headers.items():
            logger.error(f"   {key}: {value}")
        
        # 2. 记录请求体类型
        logger.error(f"\n📦 请 求体类型：{type(request.data)}")
        logger.error(f"📦 原始请求体内容：{request.data}")
        
        # 3. 尝试获取字段
        logger.error(f"\n🔍 尝试获取字段:")
        problem_id = request.data.get('problem_id')
        status_field = request.data.get('status')
        solution_code = request.data.get('solution_code')
        notes = request.data.get('notes')
        
        logger.error(f"   problem_id: {problem_id} (类型：{type(problem_id)})")
        logger.error(f"   status: {status_field} (类型：{type(status_field)})")
        logger.error(f"   solution_code: {solution_code} (类型：{type(solution_code)})")
        logger.error(f"   notes: {notes} (类型：{type(notes)})")
        
        # 4. 如果是 form-data 或 x-www-form-urlencoded，记录所有键
        if hasattr(request.data, 'keys'):
            logger.error(f"\n🔑 请求体的所有键：{list(request.data.keys())}")
        
        # 5. 用户信息
        logger.error(f"\n👤 用户信息:")
        logger.error(f"   user: {request.user}")
        logger.error(f"   user.id: {request.user.id}")
        logger.error(f"   user.username: {request.user.username}")
        
        logger.error("=" * 80)
        
        # 返回调试信息给前端
        return Response({
            'code': 200,
            'message': '调试信息已记录',
            'data': {
                'request_headers': dict(request.headers),
                'request_data_type': str(type(request.data)),
                'request_data': str(request.data),
                'extracted_fields': {
                    'problem_id': problem_id,
                    'problem_id_type': str(type(problem_id)) if problem_id is not None else None,
                    'status': status_field,
                    'status_type': str(type(status_field)) if status_field is not None else None,
                    'solution_code': solution_code,
                    'notes': notes,
                },
                'user_info': {
                    'id': request.user.id,
                    'username': request.user.username,
                }
            }
        })
