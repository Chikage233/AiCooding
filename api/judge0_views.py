"""
Judge0 代码判题系统 API 视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
from .judge0_client import judge0_client, Judge0Client
from .serializers import (
    CodeSubmissionSerializer, 
    CodeSubmissionResponseSerializer,
    LanguageInfoSerializer,
    BatchSubmissionSerializer,
    SystemInfoSerializer
)
import logging

logger = logging.getLogger(__name__)


class Judge0LanguagesView(APIView):
    """获取支持的编程语言列表"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            languages = judge0_client.get_languages()
            
            # 如果获取失败，返回错误信息
            if not languages:
                logger.warning("Judge0 返回的语言列表为空")
                return Response({
                    'code': 500,
                    'message': '无法从 Judge0 服务器获取语言列表',
                    'data': {
                        'languages': [],
                        'language_map': {},
                        'language_names': {}
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 使用序列化器
            serializer = LanguageInfoSerializer(languages, many=True)

            return Response({
                'code': 200,
                'message': '获取语言列表成功',
                'data': {
                    'languages': serializer.data,
                    'language_map': Judge0Client.LANGUAGE_MAP,
                    'language_names': Judge0Client.LANGUAGE_NAMES
                }
            })
        except Exception as e:
            logger.error(f"获取语言列表失败：{e}", exc_info=True)
            return Response({
                'code': 500,
                'message': f'获取语言列表失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class Judge0SubmitView(APIView):
    """提交代码执行"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CodeSubmissionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '请求参数错误',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validated_data = serializer.validated_data
            
            # 提取提交参数
            source_code = validated_data['source_code']
            language_id = validated_data['language_id']
            
            # 构建提交参数字典
            submit_kwargs = {}
            optional_fields = [
                'stdin', 'expected_output', 'cpu_time_limit', 'memory_limit',
                'stack_limit', 'max_processes_and_or_threads',
                'enable_per_process_and_thread_time_limit',
                'enable_per_process_and_thread_memory_limit',
                'max_file_size', 'redirect_stderr_to_stdout',
                'compiler_options', 'command_line_arguments', 'number_of_runs'
            ]
            
            for field in optional_fields:
                if field in validated_data:
                    submit_kwargs[field] = validated_data[field]
            
            # 提交代码并等待结果
            result = judge0_client.submit_and_wait(
                source_code=source_code,
                language_id=language_id,
                timeout=30,  # 最多等待 30 秒
                **submit_kwargs
            )
            
            # 使用响应序列化器
            response_serializer = CodeSubmissionResponseSerializer(result)
            
            # 判断是否成功
            status_id = result.get('status', {}).get('id')
            if status_id and status_id > 2:
                return Response({
                    'code': 200,
                    'message': '代码执行成功',
                    'data': response_serializer.data
                })
            else:
                return Response({
                    'code': 202,
                    'message': '代码正在执行中',
                    'data': response_serializer.data
                }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"代码提交失败：{e}")
            return Response({
                'code': 500,
                'message': f'代码提交失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Judge0BatchSubmitView(APIView):
    """批量提交代码"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = BatchSubmissionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'code': 400,
                'message': '请求参数错误',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validated_data = serializer.validated_data
            submissions = validated_data['submissions']
            wait = validated_data['wait']
            
            # 批量提交
            results = judge0_client.batch_submit(submissions, wait=wait)
            
            return Response({
                'code': 200,
                'message': '批量提交成功',
                'data': {
                    'results': results,
                    'count': len(results)
                }
            })
        
        except Exception as e:
            logger.error(f"批量提交失败：{e}")
            return Response({
                'code': 500,
                'message': f'批量提交失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Judge0SubmissionDetailView(APIView):
    """获取提交详情"""
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        try:
            fields = request.query_params.get('fields', None)
            field_list = fields.split(',') if fields else None
            
            result = judge0_client.get_submission(token, fields=field_list)
            
            response_serializer = CodeSubmissionResponseSerializer(result)
            
            return Response({
                'code': 200,
                'message': '获取提交详情成功',
                'data': response_serializer.data
            })
        except Exception as e:
            logger.error(f"获取提交详情失败：{e}")
            return Response({
                'code': 500,
                'message': f'获取提交详情失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Judge0SystemInfoView(APIView):
    """获取系统信息"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            system_info = judge0_client.get_system_info()
            
            response_serializer = SystemInfoSerializer(system_info)
            
            return Response({
                'code': 200,
                'message': '获取系统信息成功',
                'data': response_serializer.data
            })
        except Exception as e:
            logger.error(f"获取系统信息失败：{e}")
            return Response({
                'code': 500,
                'message': f'获取系统信息失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Judge0HealthCheckView(APIView):
    """健康检查"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            is_healthy = judge0_client.health_check()
            
            if is_healthy:
                return Response({
                    'code': 200,
                    'message': 'Judge0 服务运行正常',
                    'data': {'status': 'healthy'}
                })
            else:
                return Response({
                    'code': 503,
                    'message': 'Judge0 服务不可用',
                    'data': {'status': 'unhealthy'}
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"健康检查失败：{e}")
            return Response({
                'code': 503,
                'message': f'Judge0 服务不可用：{str(e)}',
                'data': {'status': 'error'}
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class Judge0QuickRunView(APIView):
    """快速运行代码 (简化版提交接口)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        快速运行代码，只需提供源代码和语言名称
        
        支持的语言名称:
        - python3 / python: Python 3.8.1
        - java: Java 11.0.6
        - cpp: C++ (GCC 9.2.0)
        - c: C (GCC 9.2.0)
        - javascript: JavaScript (Node.js 12.14.0)
        - go: Go 1.13.5
        - rust: Rust 1.40.0
        - csharp: C# (Mono 6.6.0.161)
        - php: PHP 7.4.1
        - ruby: Ruby 2.7.0
        - swift: Swift 5.2.3
        - kotlin: Kotlin 1.3.70
        - scala: Scala 2.13.2
        - typescript: TypeScript 3.7.4
        """
        source_code = request.data.get('source_code')
        language_name = request.data.get('language', 'python3')
        stdin = request.data.get('stdin', '')
        
        if not source_code:
            return Response({
                'code': 400,
                'message': '请提供源代码',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 根据语言名称获取语言 ID
            language_id = judge0_client.get_language_id(language_name)
            
            if not language_id:
                return Response({
                    'code': 400,
                    'message': f'不支持的编程语言：{language_name}',
                    'data': {
                        'supported_languages': list(Judge0Client.LANGUAGE_MAP.keys())
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 提交并等待结果
            result = judge0_client.submit_and_wait(
                source_code=source_code,
                language_id=language_id,
                stdin=stdin if stdin else None,
                timeout=30
            )
            
            response_serializer = CodeSubmissionResponseSerializer(result)
            
            return Response({
                'code': 200,
                'message': '代码执行完成',
                'data': response_serializer.data
            })
        
        except Exception as e:
            logger.error(f"快速运行失败：{e}")
            return Response({
                'code': 500,
                'message': f'快速运行失败：{str(e)}',
                'data': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
