import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class QwenClient:
    """通义千问 (Qwen) API 客户端"""
    
    def __init__(self, api_key=None, base_url=None, default_model=None):
        """
        初始化 Qwen 客户端
        
        Args:
            api_key: API Key
            base_url: API 基础 URL
            default_model: 默认使用的模型
        """
        self.api_key = api_key or getattr(settings, 'QWEN_API_KEY', None)
        self.base_url = base_url or getattr(settings, 'QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1')
        self.default_model = default_model or getattr(settings, 'QWEN_DEFAULT_MODEL', 'qwen-plus')
        self.timeout = getattr(settings, 'QWEN_TIMEOUT', 30)
        self.max_tokens = getattr(settings, 'QWEN_MAX_TOKENS', 2000)
        self.temperature = getattr(settings, 'QWEN_TEMPERATURE', 0.7)
        
        if not self.api_key:
            logger.warning("未配置 QWEN_API_KEY，请在 settings.py 中设置")
    
    def _make_request(self, endpoint, data):
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API 请求失败：{e}")
            raise
    
    def chat(self, messages, model=None, **kwargs):
        """
        聊天对话接口
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "你好"}]
            model: 模型名称 (可选，默认使用配置的模型)
            **kwargs: 其他参数 (temperature, max_tokens 等)
            
        Returns:
            dict: API 响应结果
        """
        model = model or self.default_model
        
        payload = {
            'model': model,
            'input': {
                'messages': messages
            },
            'parameters': {
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'temperature': kwargs.get('temperature', self.temperature),
            }
        }
        
        try:
            result = self._make_request('/services/aigc/text-generation/generation', payload)
            return {
                'success': True,
                'data': result,
                'content': result.get('output', {}).get('text', '')
            }
        except Exception as e:
            logger.error(f"Qwen 聊天接口调用失败：{e}")
            return {
                'success': False,
                'error': str(e),
                'content': None
            }
    
    def simple_chat(self, prompt, system_prompt=None, **kwargs):
        """
        简化的聊天接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词 (可选)
            **kwargs: 其他参数
            
        Returns:
            dict: API 响应结果
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, **kwargs)
    
    def generate_code_explanation(self, code, language="Python"):
        """生成代码解释"""
        system_prompt = "你是一个专业的编程助手，擅长解释代码。请用简洁清晰的中文解释代码的功能。"
        prompt = f"请解释以下{language}代码的功能：\n\n```{language.lower()}\n{code}\n```"
        
        return self.simple_chat(prompt, system_prompt=system_prompt)
    
    def generate_code_solution(self, problem_description, language="Python"):
        """生成代码解决方案"""
        system_prompt = f"你是一个优秀的程序员，请根据问题描述编写{language}代码解决方案。代码应该简洁、高效、可读性好。"
        prompt = f"问题描述：\n{problem_description}\n\n请提供完整的{language}代码实现。"
        
        return self.simple_chat(prompt, system_prompt=system_prompt)
    
    def debug_code(self, code, error_message=None):
        """调试代码"""
        system_prompt = "你是一个经验丰富的调试专家，擅长发现和修复代码中的 bug。"
        
        prompt = f"请帮我分析以下代码的问题：\n\n```python\n{code}\n```\n"
        
        if error_message:
            prompt += f"\n错误信息：{error_message}"
        
        prompt += "\n请指出问题所在并提供修复建议。"
        
        return self.simple_chat(prompt, system_prompt=system_prompt)
    
    def translate_text(self, text, target_language="中文"):
        """翻译文本"""
        system_prompt = f"你是一个专业的翻译，请将文本翻译成{target_language}。保持原意，表达自然流畅。"
        prompt = f"请翻译：\n{text}"
        
        return self.simple_chat(prompt, system_prompt=system_prompt)


# 创建全局客户端实例
qwen_client = QwenClient()
