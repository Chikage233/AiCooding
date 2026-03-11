from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .qwen_client import qwen_client
import logging

logger = logging.getLogger(__name__)


class QwenChatView(APIView):
    """Qwen 聊天接口"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        与 Qwen AI 对话
        
        Request Body:
        - message: 用户消息 (必填)
        - system_prompt: 系统提示词 (可选)
        - model: 模型名称 (可选)
        - temperature: 温度参数 (可选)
        - max_tokens: 最大 Token 数 (可选)
        """
        message = request.data.get('message')
        system_prompt = request.data.get('system_prompt')
        model = request.data.get('model')
        temperature = request.data.get('temperature')
        max_tokens = request.data.get('max_tokens')
        
        if not message:
            return Response({
                'code': 400,
                'message': '请提供消息内容',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = qwen_client.simple_chat(
                prompt=message,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # ... existing code ...
            if result['success']:
                return Response({
                    'code': 200,
                    'message': 'AI 回复成功',
                    'response': result['content'],  # 添加顶层 response 字段
                    'data': {
                        'response': result['content'],
                        'model': model or qwen_client.default_model
                    }
                })
# ... existing code ...

            else:
                logger.error(f"Qwen API 调用失败：{result.get('error')}")
                return Response({
                    'code': 500,
                    'message': f'AI 服务调用失败：{result.get("error")}',
                    'data': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"聊天接口异常：{e}")
            return Response({
                'code': 500,
                'message': f'服务器错误：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QwenCodeHelpView(APIView):
    """Qwen 代码助手接口"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        代码帮助功能
        
        Request Body:
        - action: 操作类型 (explain/debug/generate)
        - code: 代码内容
        - language: 编程语言
        - problem_description: 问题描述 (generate 动作时需要)
        - error_message: 错误信息 (debug 动作时可选)
        """
        action = request.data.get('action')
        code = request.data.get('code')
        language = request.data.get('language', 'Python')
        problem_description = request.data.get('problem_description')
        error_message = request.data.get('error_message')
        
        if not action:
            return Response({
                'code': 400,
                'message': '请指定操作类型',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = None
            
            if action == 'explain':
                if not code:
                    return Response({
                        'code': 400,
                        'message': '请提供代码',
                        'data': {}
                    }, status=status.HTTP_400_BAD_REQUEST)
                result = qwen_client.generate_code_explanation(code, language)
            
            elif action == 'debug':
                if not code:
                    return Response({
                        'code': 400,
                        'message': '请提供代码',
                        'data': {}
                    }, status=status.HTTP_400_BAD_REQUEST)
                result = qwen_client.debug_code(code, error_message)
            
            elif action == 'generate':
                if not problem_description:
                    return Response({
                        'code': 400,
                        'message': '请提供问题描述',
                        'data': {}
                    }, status=status.HTTP_400_BAD_REQUEST)
                result = qwen_client.generate_code_solution(problem_description, language)
            
            else:
                return Response({
                    'code': 400,
                    'message': '不支持的操作类型',
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if result and result['success']:
                return Response({
                    'code': 200,
                    'message': '操作成功',
                    'data': {
                        'result': result['content'],
                        'action': action
                    }
                })
            else:
                return Response({
                    'code': 500,
                    'message': f'AI 服务调用失败：{result.get("error") if result else "未知错误"}',
                    'data': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"代码助手接口异常：{e}")
            return Response({
                'code': 500,
                'message': f'服务器错误：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QwenTranslateView(APIView):
    """Qwen 翻译接口"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        翻译文本
        
        Request Body:
        - text: 要翻译的文本
        - target_language: 目标语言 (默认：中文)
        """
        text = request.data.get('text')
        target_language = request.data.get('target_language', '中文')
        
        if not text:
            return Response({
                'code': 400,
                'message': '请提供要翻译的文本',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = qwen_client.translate_text(text, target_language)
            
            if result['success']:
                return Response({
                    'code': 200,
                    'message': '翻译成功',
                    'data': {
                        'translation': result['content'],
                        'target_language': target_language
                    }
                })
            else:
                return Response({
                    'code': 500,
                    'message': f'翻译失败：{result.get("error")}',
                    'data': {}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"翻译接口异常：{e}")
            return Response({
                'code': 500,
                'message': f'服务器错误：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
