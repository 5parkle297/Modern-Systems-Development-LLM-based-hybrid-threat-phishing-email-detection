"""
特征提取服务
参考：repositories/llm-email-spam-detection 的特征提取方法
"""
import re
import numpy as np
from typing import Dict, List, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """初始化特征提取器"""
        self.embedding_model = None
        self.embedding_model_name = embedding_model_name
        self.tfidf_vectorizer = None
        self._load_models()
    
    def _load_models(self):
        """加载模型"""
        try:
            logger.info(f"加载embedding模型: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
        except Exception as e:
            logger.error(f"加载embedding模型失败: {e}")
            self.embedding_model = None
    
    def extract_features(self, email_data: Dict) -> Dict[str, Any]:
        """提取所有特征"""
        features = {
            'text_features': self.extract_text_features(email_data),
            'url_features': self.extract_url_features(email_data),
            'header_features': self.extract_header_features(email_data),
            'statistical_features': self.extract_statistical_features(email_data),
            'embedding': self.extract_embedding(email_data)
        }
        return features
    
    def extract_text_features(self, email_data: Dict) -> Dict[str, Any]:
        """提取文本特征"""
        body_text = email_data.get('body_text', '')
        body_html = email_data.get('body_html', '')
        subject = email_data.get('subject', '')
        full_text = f"{subject} {body_text}"
        
        # TF-IDF特征（如果需要）
        if self.tfidf_vectorizer is None:
            self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            # 这里应该用训练数据拟合，暂时跳过
        
        # 文本统计特征
        text_features = {
            'length': len(full_text),
            'word_count': len(full_text.split()),
            'char_count': len(full_text),
            'has_html': len(body_html) > 0,
            'html_length': len(body_html),
            'subject_length': len(subject),
            'capital_ratio': sum(1 for c in full_text if c.isupper()) / max(len(full_text), 1),
            'digit_ratio': sum(1 for c in full_text if c.isdigit()) / max(len(full_text), 1),
            'special_char_ratio': sum(1 for c in full_text if not c.isalnum() and not c.isspace()) / max(len(full_text), 1),
            'exclamation_count': full_text.count('!'),
            'question_count': full_text.count('?'),
            'dollar_sign_count': full_text.count('$'),
            'url_count': len(email_data.get('urls', [])),
        }
        
        # 可疑短语检测
        suspicious_phrases = [
            'urgent', 'verify', 'confirm', 'suspended', 'expired',
            'click here', 'limited time', 'act now', 'free money',
            'winner', 'congratulations', 'prize', 'lottery'
        ]
        text_lower = full_text.lower()
        matched_phrases = [phrase for phrase in suspicious_phrases if phrase in text_lower]
        text_features['suspicious_phrases'] = matched_phrases
        text_features['suspicious_phrase_count'] = len(matched_phrases)
        
        return text_features
    
    def extract_url_features(self, email_data: Dict) -> List[Dict[str, Any]]:
        """提取URL特征"""
        urls = email_data.get('urls', [])
        url_features = []
        
        for url_info in urls:
            url = url_info.get('url', '')
            domain = url_info.get('domain', '')
            
            features = {
                'url': url,
                'domain': domain,
                'path_length': len(url_info.get('path', '')),
                'query_length': len(url_info.get('query', '')),
                'has_ip': self._is_ip_address(domain),
                'has_port': ':' in domain,
                'is_shortened': self._is_shortened_url(domain),
                'suspicious_tld': self._is_suspicious_tld(domain),
                'subdomain_count': domain.count('.') - 1 if '.' in domain else 0,
            }
            
            url_features.append(features)
        
        return url_features
    
    def extract_header_features(self, email_data: Dict) -> Dict[str, Any]:
        """提取Header特征"""
        headers = email_data.get('headers', {})
        from_addr = email_data.get('from', '')
        to_addr = email_data.get('to', '')
        reply_to = email_data.get('reply_to', '')
        
        # 提取域名
        from_domain = self._extract_domain(from_addr)
        to_domain = self._extract_domain(to_addr)
        reply_to_domain = self._extract_domain(reply_to) if reply_to else None
        
        header_features = {
            'from_domain': from_domain,
            'to_domain': to_domain,
            'reply_to_domain': reply_to_domain,
            'domain_mismatch': reply_to_domain and reply_to_domain != from_domain,
            'has_reply_to': bool(reply_to),
            'spf_status': email_data.get('spf_status', ''),
            'dkim_status': bool(email_data.get('dkim_status')),
            'dmarc_status': email_data.get('dmarc_status', ''),
            'header_count': len(headers),
            'has_mime_version': 'mime-version' in headers,
            'has_message_id': 'message-id' in headers,
        }
        
        return header_features
    
    def extract_statistical_features(self, email_data: Dict) -> Dict[str, Any]:
        """提取统计特征"""
        urls = email_data.get('urls', [])
        attachments = email_data.get('attachments', [])
        body_text = email_data.get('body_text', '')
        
        return {
            'url_count': len(urls),
            'attachment_count': len(attachments),
            'attachment_total_size': sum(att.get('size', 0) for att in attachments),
            'unique_domains': len(set(url.get('domain', '') for url in urls)),
            'avg_url_length': np.mean([len(url.get('url', '')) for url in urls]) if urls else 0,
        }
    
    def extract_embedding(self, email_data: Dict) -> Optional[List[float]]:
        """提取文本embedding"""
        if self.embedding_model is None:
            return None
        
        try:
            subject = email_data.get('subject', '')
            body_text = email_data.get('body_text', '')
            full_text = f"{subject} {body_text}"[:5000]  # 限制长度
            
            if not full_text.strip():
                return None
            
            embedding = self.embedding_model.encode(full_text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"提取embedding失败: {e}")
            return None
    
    def _is_ip_address(self, domain: str) -> bool:
        """检查是否是IP地址"""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, domain))
    
    def _is_shortened_url(self, domain: str) -> bool:
        """检查是否是短链接服务"""
        shortened_domains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd']
        return any(short in domain.lower() for short in shortened_domains)
    
    def _is_suspicious_tld(self, domain: str) -> bool:
        """检查是否是可疑TLD"""
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz']
        return any(domain.lower().endswith(tld) for tld in suspicious_tlds)
    
    def _extract_domain(self, email: str) -> str:
        """从邮箱地址提取域名"""
        if '@' in email:
            return email.split('@')[1]
        return email

