"""
邮件解析服务
参考：repositories中的邮件处理代码
"""
import email
import re
from email import message_from_string, message_from_bytes
from email.header import decode_header
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup
import aiofiles
import logging

logger = logging.getLogger(__name__)

class EmailParser:
    """邮件解析器"""
    
    def __init__(self):
        self.suspicious_phrases = [
            "urgent action required",
            "verify your account",
            "click here immediately",
            "suspended account",
            "verify your identity",
            "confirm your email",
            "account verification",
            "security alert",
            "unauthorized access",
            "password expired"
        ]
    
    async def parse_email_file(self, file_path: Path) -> Dict:
        """解析.eml文件"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                email_content = await f.read()
            return self.parse_email_bytes(email_content)
        except Exception as e:
            logger.error(f"解析邮件文件失败: {e}")
            raise
    
    def parse_email_bytes(self, email_bytes: bytes) -> Dict:
        """解析邮件字节流"""
        msg = message_from_bytes(email_bytes)
        return self._extract_email_info(msg)
    
    def parse_email_text(self, email_text: str) -> Dict:
        """解析原始邮件文本"""
        msg = message_from_string(email_text)
        return self._extract_email_info(msg)
    
    def _extract_email_info(self, msg: email.message.Message) -> Dict:
        """提取邮件信息"""
        # 解析Header
        headers = {}
        for key, value in msg.items():
            decoded_value = self._decode_header(value)
            headers[key.lower()] = decoded_value
        
        # 提取基本信息
        from_addr = self._extract_email_address(headers.get('from', ''))
        to_addr = self._extract_email_address(headers.get('to', ''))
        reply_to = self._extract_email_address(headers.get('reply-to', ''))
        subject = headers.get('subject', '')
        
        # 提取正文
        body_text, body_html = self._extract_body(msg)
        
        # 提取URL
        urls = self._extract_urls(body_text + body_html)
        
        # 提取附件信息
        attachments = self._extract_attachments(msg)
        
        # 提取SPF/DKIM/DMARC信息（从header中）
        spf_status = headers.get('received-spf', '')
        dkim_status = headers.get('dkim-signature', '')
        dmarc_status = headers.get('authentication-results', '')
        
        return {
            'headers': headers,
            'from': from_addr,
            'to': to_addr,
            'reply_to': reply_to,
            'subject': subject,
            'body_text': body_text,
            'body_html': body_html,
            'urls': urls,
            'attachments': attachments,
            'spf_status': spf_status,
            'dkim_status': dkim_status,
            'dmarc_status': dmarc_status,
            'raw_message': str(msg)
        }
    
    def _decode_header(self, header_value: str) -> str:
        """解码邮件头"""
        if not header_value:
            return ""
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        return decoded_string
    
    def _extract_email_address(self, header_value: str) -> str:
        """提取邮箱地址"""
        if not header_value:
            return ""
        # 匹配邮箱地址
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        matches = re.findall(pattern, header_value)
        return matches[0] if matches else header_value
    
    def _extract_body(self, msg: email.message.Message) -> Tuple[str, str]:
        """提取邮件正文"""
        body_text = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        try:
                            body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
                    elif content_type == "text/html":
                        try:
                            body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                try:
                    body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            elif content_type == "text/html":
                try:
                    body_html = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
        
        # 从HTML中提取纯文本
        if body_html:
            soup = BeautifulSoup(body_html, 'html.parser')
            body_text += soup.get_text(separator=' ', strip=True)
        
        return body_text.strip(), body_html.strip()
    
    def _extract_urls(self, text: str) -> List[Dict[str, str]]:
        """提取URL"""
        urls = []
        # URL模式
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, text)
        
        for url in matches:
            # 清理URL
            url = url.rstrip('.,;:!?)')
            parsed_url = self._parse_url(url)
            if parsed_url:
                urls.append(parsed_url)
        
        return urls
    
    def _parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """解析URL"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            return {
                'url': url,
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': parsed.query,
                'fragment': parsed.fragment
            }
        except:
            return None
    
    def _extract_attachments(self, msg: email.message.Message) -> List[Dict]:
        """提取附件信息"""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': self._decode_header(filename),
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })
        return attachments

