"""
Judge0 代码判题系统客户端封装
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class Judge0Client:
    """Judge0 API 客户端"""
    
    # 支持的编程语言 ID (常用语言)
    LANGUAGE_MAP = {
        'python3': 71,      # Python 3.8.1
        'python': 71,       # Python 3.8.1 (别名)
        'java': 62,         # Java 11.0.6
        'cpp': 54,          # C++ (GCC 9.2.0)
        'c': 50,            # C (GCC 9.2.0)
        'javascript': 63,   # JavaScript (Node.js 12.14.0)
        'go': 60,           # Go 1.13.5
        'rust': 73,         # Rust 1.40.0
        'csharp': 51,       # C# (Mono 6.6.0.161)
        'php': 68,          # PHP 7.4.1
        'ruby': 72,         # Ruby 2.7.0
        'swift': 74,        # Swift 5.2.3
        'kotlin': 78,       # Kotlin 1.3.70
        'scala': 81,        # Scala 2.13.2
        'typescript': 75,   # TypeScript 3.7.4
    }
    
    # 语言名称映射
    LANGUAGE_NAMES = {
        71: 'Python 3.8.1',
        62: 'Java 11.0.6',
        54: 'C++ (GCC 9.2.0)',
        50: 'C (GCC 9.2.0)',
        63: 'JavaScript (Node.js 12.14.0)',
        60: 'Go 1.13.5',
        73: 'Rust 1.40.0',
        51: 'C# (Mono 6.6.0.161)',
        68: 'PHP 7.4.1',
        72: 'Ruby 2.7.0',
        74: 'Swift 5.2.3',
        78: 'Kotlin 1.3.70',
        81: 'Scala 2.13.2',
        75: 'TypeScript 3.7.4',
    }
    
    def __init__(self, base_url=None, api_key=None):
        """
        初始化 Judge0 客户端
        
        Args:
            base_url: Judge0 API 基础 URL
            api_key: API Key (如果需要认证)
        """
        self.base_url = base_url or getattr(settings, 'JUDGE0_BASE_URL', 'http://106.53.59.120:2358')
        self.api_key = api_key or getattr(settings, 'JUDGE0_API_KEY', None)
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'X-Auth-Token': self.api_key})
        
        # 默认配置
        self.default_wait_time = getattr(settings, 'JUDGE0_WAIT_TIME', 3.0)  # 等待时间 (秒)
        self.default_cpu_time_limit = getattr(settings, 'JUDGE0_CPU_TIME_LIMIT', 5.0)  # CPU 时间限制 (秒)
        self.default_memory_limit = getattr(settings, 'JUDGE0_MEMORY_LIMIT', 128000)  # 内存限制 (KB)
        self.default_stack_limit = getattr(settings, 'JUDGE0_STACK_LIMIT', 64000)  # 栈限制 (KB)
        self.default_max_processes_and_or_threads = getattr(settings, 'JUDGE0_MAX_PROCESSES', 60)
    
    def _make_request(self, method, endpoint, **kwargs):
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 请求参数
            
        Returns:
            requests.Response 对象
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            
            # 如果是 401 错误且没有设置 API Key，可能是服务器需要认证
            if response.status_code == 401 and not self.api_key:
                logger.warning(
                    f"Judge0 返回 401 错误，可能需要 API Key。\n"
                    f"请在 settings.py 中配置 JUDGE0_API_KEY\n"
                    f"或者确认 Judge0 服务器是否允许匿名访问"
                )
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Judge0 API 请求失败：{e}")
            raise
    
    def get_languages(self):
        """
        获取所有支持的编程语言
        
        Returns:
            list: 语言列表
        """
        cache_key = 'judge0_languages'
        languages = cache.get(cache_key)
        
        if languages is None:
            try:
                response = self._make_request('GET', '/languages')
                languages = response.json()
                cache.set(cache_key, languages, 3600 * 24)  # 缓存 24 小时
            except Exception as e:
                logger.error(f"获取语言列表失败：{e}")
                # 返回空的列表而不是 None，避免序列化器错误
                return []

        return languages

    
    def get_language_id(self, language_name):
        """
        根据语言名称获取语言 ID
        
        Args:
            language_name: 语言名称 (如 'python3', 'java', 'cpp')
            
        Returns:
            int: 语言 ID，如果找不到则返回 None
        """
        return self.LANGUAGE_MAP.get(language_name.lower())
    
    def submit_code(self, source_code, language_id, stdin=None, expected_output=None, 
                    cpu_time_limit=None, memory_limit=None, stack_limit=None,
                    max_processes_and_or_threads=None, enable_per_process_and_thread_time_limit=False,
                    enable_per_process_and_thread_memory_limit=False, max_file_size=None,
                    redirect_stderr_to_stdout=False, callback_url=None,
                    compiler_options=None, command_line_arguments=None, number_of_runs=None):
        """
        提交代码执行
        
        Args:
            source_code: 源代码字符串
            language_id: 编程语言 ID
            stdin: 标准输入
            expected_output: 期望输出 (用于判断是否正确)
            cpu_time_limit: CPU 时间限制 (秒)
            memory_limit: 内存限制 (KB)
            stack_limit: 栈限制 (KB)
            max_processes_and_or_threads: 最大进程/线程数
            enable_per_process_and_thread_time_limit: 是否启用每个进程/线程的时间限制
            enable_per_process_and_thread_memory_limit: 是否启用每个进程/线程的内存限制
            max_file_size: 最大文件大小 (字节)
            redirect_stderr_to_stdout: 是否将标准错误重定向到标准输出
            callback_url: 回调 URL (异步执行时使用)
            compiler_options: 编译器选项
            command_line_arguments: 命令行参数
            number_of_runs: 运行次数
            
        Returns:
            dict: 提交结果，包含 token
        """
        submission_data = {
            'source_code': source_code,
            'language_id': language_id,
        }
        
        # 添加可选参数
        if stdin is not None:
            submission_data['stdin'] = stdin
        if expected_output is not None:
            submission_data['expected_output'] = expected_output
        if cpu_time_limit is not None:
            submission_data['cpu_time_limit'] = cpu_time_limit
        else:
            submission_data['cpu_time_limit'] = self.default_cpu_time_limit
        if memory_limit is not None:
            submission_data['memory_limit'] = memory_limit
        else:
            submission_data['memory_limit'] = self.default_memory_limit
        if stack_limit is not None:
            submission_data['stack_limit'] = stack_limit
        else:
            submission_data['stack_limit'] = self.default_stack_limit
        if max_processes_and_or_threads is not None:
            submission_data['max_processes_and_or_threads'] = max_processes_and_or_threads
        else:
            submission_data['max_processes_and_or_threads'] = self.default_max_processes_and_or_threads
        if enable_per_process_and_thread_time_limit:
            submission_data['enable_per_process_and_thread_time_limit'] = True
        if enable_per_process_and_thread_memory_limit:
            submission_data['enable_per_process_and_thread_memory_limit'] = True
        if max_file_size is not None:
            submission_data['max_file_size'] = max_file_size
        if redirect_stderr_to_stdout:
            submission_data['redirect_stderr_to_stdout'] = True
        if callback_url is not None:
            submission_data['callback_url'] = callback_url
        if compiler_options is not None:
            submission_data['compiler_options'] = compiler_options
        if command_line_arguments is not None:
            submission_data['command_line_arguments'] = command_line_arguments
        if number_of_runs is not None:
            submission_data['number_of_runs'] = number_of_runs
        
        # 提交代码 (wait=false 表示异步执行)
        response = self._make_request(
            'POST',
            '/submissions',
            json=submission_data,
            params={'wait': 'false'}
        )
        
        return response.json()
    
    def get_submission(self, token, fields=None):
        """
        获取提交结果
        
        Args:
            token: 提交令牌
            fields: 需要返回的字段列表
            
        Returns:
            dict: 提交结果
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        response = self._make_request('GET', f'/submissions/{token}', params=params)
        return response.json()
    
    def wait_for_result(self, token, timeout=10, interval=0.5):
        """
        等待提交结果
        
        Args:
            token: 提交令牌
            timeout: 超时时间 (秒)
            interval: 轮询间隔 (秒)
            
        Returns:
            dict: 提交结果
        """
        import time
        
        start_time = time.time()
        while True:
            try:
                result = self.get_submission(token)
                status_id = result.get('status', {}).get('id')
                
                # 状态 1-5: 1=In Queue, 2=Processing, 3=Accepted, 4=Wrong Answer, 
                # 5=Time Limit Exceeded, 6=Compilation Error, 7=Runtime Error, etc.
                if status_id and status_id > 2:
                    return result
            except Exception as e:
                logger.error(f"获取提交结果失败：{e}")
                return {'status': {'id': -1, 'description': 'Error fetching result'}, 'error': str(e)}
            
            # 检查超时
            if time.time() - start_time > timeout:
                return {'status': {'id': -2, 'description': 'Timeout'}, 'error': 'Wait for result timeout'}
            
            time.sleep(interval)
    
    def submit_and_wait(self, source_code, language_id, timeout=10, **kwargs):
        """
        提交代码并等待结果
        
        Args:
            source_code: 源代码
            language_id: 语言 ID
            timeout: 超时时间 (秒)
            **kwargs: 其他提交参数
            
        Returns:
            dict: 提交结果
        """
        try:
            # 提交代码
            submit_result = self.submit_code(source_code, language_id, **kwargs)
            token = submit_result.get('token')
            
            if not token:
                return {'status': {'id': -1, 'description': 'Failed to submit'}, 'error': 'No token returned'}
            
            # 等待结果
            return self.wait_for_result(token, timeout=timeout)
        
        except Exception as e:
            logger.error(f"提交并等待结果失败：{e}")
            return {'status': {'id': -1, 'description': 'Submission failed'}, 'error': str(e)}
    
    def batch_submit(self, submissions, wait=True):
        """
        批量提交代码
        
        Args:
            submissions: 提交列表，每个元素是包含 source_code 和 language_id 的字典
            wait: 是否等待结果
            
        Returns:
            list: 提交结果列表
        """
        results = []
        tokens = []
        
        # 批量提交
        for submission in submissions:
            try:
                result = self.submit_code(
                    source_code=submission['source_code'],
                    language_id=submission['language_id'],
                    **submission.get('options', {})
                )
                tokens.append(result['token'])
                results.append({'token': result['token'], 'status': 'submitted'})
            except Exception as e:
                results.append({'status': 'failed', 'error': str(e)})
        
        # 如果需要等待结果
        if wait:
            for i, token in enumerate(tokens):
                if results[i]['status'] == 'submitted':
                    results[i] = self.wait_for_result(token)
        
        return results
    
    def get_system_info(self):
        """
        获取系统信息
        
        Returns:
            dict: 系统信息
        """
        try:
            response = self._make_request('GET', '/system_info')
            return response.json()
        except Exception as e:
            logger.error(f"获取系统信息失败：{e}")
            return {}
    
    def health_check(self):
        """
        健康检查
        
        Returns:
            bool: 是否健康
        """
        try:
            response = self._make_request('GET', '')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败：{e}")
            return False


# 创建全局客户端实例
judge0_client = Judge0Client()
