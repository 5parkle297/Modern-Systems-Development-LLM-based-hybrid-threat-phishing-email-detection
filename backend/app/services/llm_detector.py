"""
LLM检测模块
支持OpenAI、Anthropic、Google Gemini
可通过 OPENAI_BASE_URL 适配 SiliconFlow 等 OpenAI 兼容平台
"""
import os
from typing import Dict, Optional
import logging
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMDetector:
    """LLM检测器"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4-turbo-preview"):
        """初始化LLM检测器"""
        self.provider = provider
        self.model = model
        self.api_key = self._get_api_key()
        # 兼容 OpenAI 兼容平台（如 SiliconFlow）的自定义 Base URL
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self._client = None
        self._initialize_client()
    
    def _get_api_key(self) -> Optional[str]:
        """获取API密钥"""
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == "google":
            return os.getenv("GOOGLE_API_KEY")
        return None
    
    def _initialize_client(self):
        """初始化客户端"""
        try:
            if self.provider == "openai":
                # 使用 requests 直接调用 /v1/chat/completions，兼容 OpenAI 与 SiliconFlow
                if not self.api_key:
                    raise RuntimeError("未配置 OPENAI_API_KEY")
                self._client = requests.Session()
            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            elif self.provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
            self._client = None
    
    def detect(self, email_data: Dict, features: Dict) -> Dict:
        """使用LLM检测邮件"""
        if self._client is None:
            logger.warning("LLM客户端未初始化，返回默认结果")
            return {
                'label': 'benign',
                'confidence': 0.5,
                'reasoning': 'LLM服务不可用',
                'provider': self.provider
            }
        
        try:
            # 构建prompt
            prompt = self._build_prompt(email_data, features)
            
            # 调用LLM
            if self.provider == "openai":
                result = self._call_openai(prompt)
            elif self.provider == "anthropic":
                result = self._call_anthropic(prompt)
            elif self.provider == "google":
                result = self._call_google(prompt)
            else:
                result = self._default_result()
            
            return result
        except Exception as e:
            logger.error(f"LLM检测失败: {e}")
            return self._default_result()
    
    def _build_prompt(self, email_data: Dict, features: Dict) -> str:
        """构建检测prompt"""
        subject = email_data.get('subject', '')
        body_text = email_data.get('body_text', '')[:2000]  # 限制长度
        from_addr = email_data.get('from', '')
        urls = email_data.get('urls', [])
        url_list = '\n'.join([url.get('url', '') for url in urls[:5]])
        
        prompt = f"""你是一个专业的钓鱼邮件检测专家。请分析以下邮件并判断它是否是钓鱼邮件。

邮件信息：
发件人: {from_addr}
主题: {subject}
正文: {body_text}
链接: {url_list}

请按照以下格式回答：
1. 判断结果：phishing（钓鱼邮件）、suspicious（可疑邮件）或benign（正常邮件）
2. 置信度：0.0-1.0之间的数值
3. 判断理由：详细说明你的判断依据

请特别关注以下特征：
- 邮件内容是否包含紧急行动要求
- 链接是否可疑（短链接、可疑域名等）
- 发件人地址是否可疑
- 邮件内容是否要求提供敏感信息
- 是否存在拼写错误或语法问题
- 邮件格式是否异常

请以JSON格式返回结果：
{{
    "label": "phishing/suspicious/benign",
    "confidence": 0.0-1.0,
    "reasoning": "详细判断理由"
}}"""
        return prompt
    
    def _call_openai(self, prompt: str) -> Dict:
        """调用OpenAI API"""
        try:
            # 兼容 OpenAI 官方与 SiliconFlow 的 /v1/chat/completions 接口
            base_url = self.base_url or "https://api.openai.com/v1"
            url = base_url.rstrip("/") + "/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的钓鱼邮件检测专家。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            }
            resp = self._client.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return self._default_result()
    
    def _call_anthropic(self, prompt: str) -> Dict:
        """调用Anthropic API"""
        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = message.content[0].text
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {e}")
            return self._default_result()
    
    def _call_google(self, prompt: str) -> Dict:
        """调用Google Gemini API"""
        try:
            response = self._client.generate_content(prompt)
            content = response.text
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"Google API调用失败: {e}")
            return self._default_result()
    
    def _parse_response(self, content: str) -> Dict:
        """解析LLM响应"""
        import json
        import re
        
        # 尝试提取JSON
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                label = result.get('label', 'benign').lower()
                confidence = float(result.get('confidence', 0.5))
                reasoning = result.get('reasoning', '无详细理由')
                
                # 标准化label
                if 'phishing' in label:
                    label = 'phishing'
                elif 'suspicious' in label:
                    label = 'suspicious'
                else:
                    label = 'benign'
                
                return {
                    'label': label,
                    'confidence': max(0.0, min(1.0, confidence)),
                    'reasoning': reasoning,
                    'provider': self.provider
                }
            except:
                pass
        
        # 如果无法解析JSON，尝试从文本中提取
        label = 'benign'
        if 'phishing' in content.lower():
            label = 'phishing'
        elif 'suspicious' in content.lower():
            label = 'suspicious'
        
        confidence = 0.5
        if 'high' in content.lower() or '高' in content:
            confidence = 0.8
        elif 'low' in content.lower() or '低' in content:
            confidence = 0.3
        
        return {
            'label': label,
            'confidence': confidence,
            'reasoning': content[:200],
            'provider': self.provider
        }
    
    def _default_result(self) -> Dict:
        """返回默认结果"""
        return {
            'label': 'benign',
            'confidence': 0.5,
            'reasoning': 'LLM检测失败，返回默认结果',
            'provider': self.provider
        }

