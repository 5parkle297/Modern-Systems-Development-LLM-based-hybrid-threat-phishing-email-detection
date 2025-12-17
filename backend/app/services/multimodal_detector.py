"""
多模态检测模块
用于分析邮件中的图像和网页截图
参考：repositories/Multimodal_LLM_Phishing_Detection 和 PhishLLM
"""
import os
from typing import Dict, List, Optional
import logging
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

class MultimodalDetector:
    """多模态检测器"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4-vision-preview"):
        """初始化多模态检测器"""
        self.provider = provider
        self.model = model
        self.api_key = self._get_api_key()
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
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            elif self.provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
        except Exception as e:
            logger.error(f"初始化多模态客户端失败: {e}")
            self._client = None
    
    def detect(self, email_data: Dict, features: Dict) -> Dict:
        """多模态检测"""
        attachments = email_data.get('attachments', [])
        image_attachments = [att for att in attachments if att.get('content_type', '').startswith('image/')]
        
        result = {
            'has_images': len(image_attachments) > 0,
            'image_analysis': [],
            'webpage_analysis': None
        }
        
        # 分析图像附件
        if image_attachments:
            for attachment in image_attachments[:3]:  # 最多分析3张图片
                analysis = self._analyze_image(attachment)
                if analysis:
                    result['image_analysis'].append(analysis)
        
        # 分析邮件中的URL（如果有截图）
        urls = email_data.get('urls', [])
        if urls:
            # 这里可以添加网页截图分析逻辑
            # 参考：repositories/Multimodal_LLM_Phishing_Detection
            pass
        
        return result
    
    def _analyze_image(self, attachment: Dict) -> Optional[Dict]:
        """分析图像"""
        if self._client is None:
            return None
        
        try:
            # 读取图像文件
            filename = attachment.get('filename', '')
            file_path = Path(filename)
            
            if not file_path.exists():
                return None
            
            # 编码图像
            image_base64 = self._encode_image(file_path)
            if not image_base64:
                return None
            
            # 调用VLM API
            if self.provider == "openai":
                analysis = self._analyze_with_openai(image_base64, filename)
            elif self.provider == "anthropic":
                analysis = self._analyze_with_anthropic(image_base64, filename)
            elif self.provider == "google":
                analysis = self._analyze_with_google(image_base64, filename)
            else:
                return None
            
            return {
                'filename': filename,
                'analysis': analysis
            }
        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            return None
    
    def _encode_image(self, file_path: Path) -> Optional[str]:
        """编码图像为base64"""
        try:
            with open(file_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图像编码失败: {e}")
            return None
    
    def _analyze_with_openai(self, image_base64: str, filename: str) -> str:
        """使用OpenAI分析图像"""
        try:
            prompt = f"""分析这张图片，判断它是否可能是钓鱼邮件的一部分。
            
请关注：
1. 图片中是否包含可疑的登录页面
2. 是否包含品牌logo但域名可疑
3. 是否要求输入敏感信息
4. 整体设计是否可疑

图片文件名: {filename}"""
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI图像分析失败: {e}")
            return "图像分析失败"
    
    def _analyze_with_anthropic(self, image_base64: str, filename: str) -> str:
        """使用Anthropic分析图像"""
        try:
            # Anthropic Claude支持图像输入
            prompt = f"""分析这张图片，判断它是否可能是钓鱼邮件的一部分。
            
请关注：
1. 图片中是否包含可疑的登录页面
2. 是否包含品牌logo但域名可疑
3. 是否要求输入敏感信息
4. 整体设计是否可疑

图片文件名: {filename}"""
            
            # 注意：这里需要根据Anthropic的实际API格式调整
            # 示例代码，实际使用时需要根据API文档调整
            return "Anthropic图像分析（待实现）"
        except Exception as e:
            logger.error(f"Anthropic图像分析失败: {e}")
            return "图像分析失败"
    
    def _analyze_with_google(self, image_base64: str, filename: str) -> str:
        """使用Google Gemini分析图像"""
        try:
            import google.generativeai as genai
            
            prompt = f"""分析这张图片，判断它是否可能是钓鱼邮件的一部分。
            
请关注：
1. 图片中是否包含可疑的登录页面
2. 是否包含品牌logo但域名可疑
3. 是否要求输入敏感信息
4. 整体设计是否可疑

图片文件名: {filename}"""
            
            # 注意：这里需要根据Google Gemini的实际API格式调整
            return "Google图像分析（待实现）"
        except Exception as e:
            logger.error(f"Google图像分析失败: {e}")
            return "图像分析失败"

