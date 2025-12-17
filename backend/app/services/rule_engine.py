"""
规则引擎
基于规则和黑名单的检测
"""
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.url_blacklist = self._load_url_blacklist()
        self.suspicious_phrases = [
            r'urgent.{0,20}action.{0,20}required',
            r'verify.{0,20}your.{0,20}account',
            r'click.{0,20}here.{0,20}immediately',
            r'suspended.{0,20}account',
            r'verify.{0,20}your.{0,20}identity',
            r'confirm.{0,20}your.{0,20}email',
            r'account.{0,20}verification',
            r'security.{0,20}alert',
            r'unauthorized.{0,20}access',
            r'password.{0,20}expired',
            r'limited.{0,20}time.{0,20}offer',
            r'free.{0,20}money',
            r'congratulations.{0,20}winner',
            r'claim.{0,20}your.{0,20}prize',
        ]
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
            'is.gd', 'short.link', 'rebrand.ly'
        ]
    
    def _load_url_blacklist(self) -> List[str]:
        """加载URL黑名单"""
        # 这里可以从文件或数据库加载
        # 参考：repositories/PhishLLM/datasets/hosting_blacklists.txt
        return []
    
    def detect(self, email_data: Dict, features: Dict) -> Dict:
        """执行规则检测"""
        matched_rules = []
        score = 0.0
        
        # 1. URL黑名单检查
        url_matches = self._check_url_blacklist(email_data.get('urls', []))
        if url_matches:
            matched_rules.append(f"匹配到黑名单URL: {len(url_matches)}个")
            score += 0.3
        
        # 2. 可疑短语检查
        phrase_matches = self._check_suspicious_phrases(
            email_data.get('body_text', '') + ' ' + email_data.get('subject', '')
        )
        if phrase_matches:
            matched_rules.append(f"检测到可疑短语: {', '.join(phrase_matches[:3])}")
            score += min(0.2, len(phrase_matches) * 0.05)
        
        # 3. 域名欺骗检测
        domain_spoofing = self._check_domain_spoofing(email_data, features)
        if domain_spoofing:
            matched_rules.append("检测到域名欺骗")
            score += 0.25
        
        # 4. SPF/DKIM/DMARC检查
        auth_results = self._check_email_auth(email_data)
        if auth_results['failures']:
            matched_rules.extend(auth_results['failures'])
            score += len(auth_results['failures']) * 0.1
        
        # 5. 短链接检查
        shortened_urls = self._check_shortened_urls(email_data.get('urls', []))
        if shortened_urls:
            matched_rules.append(f"检测到短链接: {len(shortened_urls)}个")
            score += min(0.15, len(shortened_urls) * 0.05)
        
        # 6. 可疑TLD检查
        suspicious_tlds = self._check_suspicious_tld(email_data.get('urls', []))
        if suspicious_tlds:
            matched_rules.append(f"检测到可疑TLD: {', '.join(suspicious_tlds)}")
            score += 0.1
        
        # 7. 发件人域名与回复地址不一致
        if self._check_reply_to_mismatch(email_data):
            matched_rules.append("发件人域名与回复地址不一致")
            score += 0.15
        
        # 归一化分数
        score = min(1.0, score)
        
        return {
            'score': score,
            'matched_rules': matched_rules,
            'spf_status': email_data.get('spf_status', ''),
            'dkim_status': 'pass' if email_data.get('dkim_status') else 'fail',
            'dmarc_status': email_data.get('dmarc_status', ''),
        }
    
    def _check_url_blacklist(self, urls: List[Dict]) -> List[str]:
        """检查URL黑名单"""
        matches = []
        for url_info in urls:
            url = url_info.get('url', '')
            domain = url_info.get('domain', '')
            for blacklisted in self.url_blacklist:
                if blacklisted in url or blacklisted in domain:
                    matches.append(url)
        return matches
    
    def _check_suspicious_phrases(self, text: str) -> List[str]:
        """检查可疑短语"""
        text_lower = text.lower()
        matches = []
        for pattern in self.suspicious_phrases:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern)
        return matches
    
    def _check_domain_spoofing(self, email_data: Dict, features: Dict) -> bool:
        """检查域名欺骗"""
        from_domain = features.get('header_features', {}).get('from_domain', '')
        reply_to_domain = features.get('header_features', {}).get('reply_to_domain')
        
        # 检查回复地址域名是否与发件人域名不一致
        if reply_to_domain and from_domain and reply_to_domain != from_domain:
            return True
        
        # 检查URL中的域名是否与发件人域名不一致
        urls = email_data.get('urls', [])
        for url_info in urls:
            url_domain = url_info.get('domain', '')
            if from_domain and url_domain:
                # 提取主域名（去掉www）
                from_main = from_domain.replace('www.', '')
                url_main = url_domain.replace('www.', '')
                if from_main not in url_main and url_main not in from_main:
                    return True
        
        return False
    
    def _check_email_auth(self, email_data: Dict) -> Dict:
        """检查邮件认证"""
        failures = []
        
        spf_status = email_data.get('spf_status', '').lower()
        if spf_status and 'fail' in spf_status:
            failures.append('SPF验证失败')
        
        dkim_status = email_data.get('dkim_status', '')
        if not dkim_status:
            failures.append('缺少DKIM签名')
        
        dmarc_status = email_data.get('dmarc_status', '').lower()
        if dmarc_status and 'fail' in dmarc_status:
            failures.append('DMARC验证失败')
        
        return {
            'failures': failures,
            'spf': 'pass' if 'pass' in spf_status else 'fail',
            'dkim': 'pass' if dkim_status else 'fail',
            'dmarc': 'pass' if 'pass' in dmarc_status else 'fail'
        }
    
    def _check_shortened_urls(self, urls: List[Dict]) -> List[str]:
        """检查短链接"""
        matches = []
        for url_info in urls:
            domain = url_info.get('domain', '').lower()
            if any(short in domain for short in self.suspicious_domains):
                matches.append(url_info.get('url', ''))
        return matches
    
    def _check_suspicious_tld(self, urls: List[Dict]) -> List[str]:
        """检查可疑TLD"""
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top']
        matches = []
        for url_info in urls:
            domain = url_info.get('domain', '').lower()
            for tld in suspicious_tlds:
                if domain.endswith(tld):
                    matches.append(domain)
        return list(set(matches))
    
    def _check_reply_to_mismatch(self, email_data: Dict) -> bool:
        """检查回复地址不匹配"""
        from_addr = email_data.get('from', '')
        reply_to = email_data.get('reply_to', '')
        
        if not reply_to:
            return False
        
        from_domain = from_addr.split('@')[1] if '@' in from_addr else ''
        reply_to_domain = reply_to.split('@')[1] if '@' in reply_to else ''
        
        return from_domain != reply_to_domain

