"""
检测引擎
集成所有检测模块，实现ensemble机制
"""
from typing import Dict, Optional, List
import logging
from datetime import datetime
import uuid

from .email_parser import EmailParser
from .feature_extractor import FeatureExtractor
from .rule_engine import RuleEngine
from .llm_detector import LLMDetector
from .rag_module import RAGModule
from .multimodal_detector import MultimodalDetector
from ..models.schemas import DetectionLabel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Settings

logger = logging.getLogger(__name__)

class DetectionEngine:
    """检测引擎"""
    
    def __init__(self, settings: Settings):
        """初始化检测引擎"""
        self.settings = settings
        
        # 初始化各个模块
        self.email_parser = EmailParser()
        self.feature_extractor = FeatureExtractor(settings.EMBEDDING_MODEL)
        self.rule_engine = RuleEngine()
        self.llm_detector = LLMDetector(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL
        )
        
        # RAG模块（如果启用）
        if settings.RAG_ENABLED:
            self.rag_module = RAGModule(
                knowledge_base_dir=settings.KNOWLEDGE_BASE_DIR,
                similarity_threshold=settings.SIMILARITY_THRESHOLD
            )
        else:
            self.rag_module = None
        
        # 多模态检测（如果启用）
        if settings.MULTIMODAL_ENABLED:
            self.multimodal_detector = MultimodalDetector(
                provider=settings.VLM_PROVIDER,
                model=settings.VLM_MODEL
            )
        else:
            self.multimodal_detector = None
    
    async def detect(self, email_data: Dict) -> Dict:
        """执行完整检测流程"""
        job_id = str(uuid.uuid4())
        
        try:
            # 1. 特征提取
            logger.info(f"[{job_id}] 开始特征提取")
            features = self.feature_extractor.extract_features(email_data)
            
            # 2. 规则引擎检测
            logger.info(f"[{job_id}] 执行规则引擎检测")
            rule_result = self.rule_engine.detect(email_data, features)
            
            # 3. LLM检测
            logger.info(f"[{job_id}] 执行LLM检测")
            llm_result = self.llm_detector.detect(email_data, features)
            
            # 4. RAG检索（如果启用）
            rag_result = None
            if self.rag_module:
                logger.info(f"[{job_id}] 执行RAG检索")
                rag_result = self.rag_module.retrieve(email_data, features)
            
            # 5. 多模态检测（如果启用）
            multimodal_result = None
            if self.multimodal_detector:
                logger.info(f"[{job_id}] 执行多模态检测")
                multimodal_result = self.multimodal_detector.detect(email_data, features)
            
            # 6. Ensemble融合
            logger.info(f"[{job_id}] 执行结果融合")
            final_result = self._ensemble_fusion(
                rule_result,
                llm_result,
                rag_result,
                multimodal_result
            )
            
            # 7. 生成解释和建议
            explanation = self._generate_explanation(
                rule_result,
                llm_result,
                rag_result,
                multimodal_result,
                final_result
            )
            recommendations = self._generate_recommendations(final_result)
            
            # 8. 构建最终结果
            result = {
                'job_id': job_id,
                'label': final_result['label'],
                'overall_score': final_result['score'],
                'confidence': final_result['confidence'],
                'rule_engine': rule_result,
                'llm_detection': llm_result,
                'rag_result': rag_result,
                'multimodal_result': multimodal_result,
                'features': features,
                'explanation': explanation,
                'recommendations': recommendations,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[{job_id}] 检测完成: {final_result['label']}, 分数: {final_result['score']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"[{job_id}] 检测失败: {e}")
            raise
    
    def _ensemble_fusion(self, rule_result: Dict, llm_result: Dict,
                        rag_result: Optional[Dict], multimodal_result: Optional[Dict]) -> Dict:
        """Ensemble融合"""
        weights = {
            'rule': self.settings.RULE_ENGINE_WEIGHT,
            'llm': self.settings.LLM_WEIGHT,
            'rag': self.settings.RAG_WEIGHT,
            'multimodal': self.settings.MULTIMODAL_WEIGHT
        }
        
        # 计算加权分数
        rule_score = rule_result.get('score', 0.0) * weights['rule']
        llm_score = self._llm_score_to_numeric(llm_result) * weights['llm']
        
        rag_score = 0.0
        if rag_result and rag_result.get('matched_templates'):
            # 如果有匹配的模板，增加分数
            max_similarity = max(rag_result.get('similarity_scores', [0.0]))
            rag_score = max_similarity * weights['rag']
        
        multimodal_score = 0.0
        if multimodal_result and multimodal_result.get('image_analysis'):
            # 如果检测到可疑图像，增加分数
            multimodal_score = 0.5 * weights['multimodal']
        
        # 总分数
        total_score = rule_score + llm_score + rag_score + multimodal_score
        
        # 确定标签
        label = self._determine_label(total_score, llm_result, rule_result)
        
        # 计算置信度
        confidence = self._calculate_confidence(
            total_score,
            llm_result.get('confidence', 0.5),
            rule_result.get('score', 0.0)
        )
        
        return {
            'label': label,
            'score': min(1.0, total_score),
            'confidence': confidence
        }
    
    def _llm_score_to_numeric(self, llm_result: Dict) -> float:
        """将LLM结果转换为数值分数"""
        label = llm_result.get('label', 'benign')
        confidence = llm_result.get('confidence', 0.5)
        
        if label == 'phishing':
            return 0.8 + confidence * 0.2
        elif label == 'suspicious':
            return 0.4 + confidence * 0.3
        else:
            return (1.0 - confidence) * 0.3
    
    def _determine_label(self, score: float, llm_result: Dict, rule_result: Dict) -> DetectionLabel:
        """确定最终标签"""
        llm_label = llm_result.get('label', 'benign')
        rule_score = rule_result.get('score', 0.0)
        
        # 如果分数很高，直接判定为phishing
        if score >= 0.7:
            return DetectionLabel.PHISHING
        
        # 如果LLM判定为phishing且规则引擎也检测到问题
        if llm_label == 'phishing' and rule_score > 0.3:
            return DetectionLabel.PHISHING
        
        # 如果分数中等，判定为suspicious
        if score >= 0.4:
            return DetectionLabel.SUSPICIOUS
        
        # 否则判定为benign
        return DetectionLabel.BENIGN
    
    def _calculate_confidence(self, score: float, llm_confidence: float, rule_score: float) -> float:
        """计算置信度"""
        # 综合多个因素的置信度
        confidence = (score * 0.4 + llm_confidence * 0.4 + min(rule_score, 1.0) * 0.2)
        return min(1.0, max(0.0, confidence))
    
    def _generate_explanation(self, rule_result: Dict, llm_result: Dict,
                             rag_result: Optional[Dict], multimodal_result: Optional[Dict],
                             final_result: Dict) -> str:
        """生成解释性说明"""
        explanations = []
        
        # 规则引擎解释
        matched_rules = rule_result.get('matched_rules', [])
        if matched_rules:
            explanations.append(f"规则引擎检测到{len(matched_rules)}个可疑特征: {', '.join(matched_rules[:3])}")
        
        # LLM解释
        llm_reasoning = llm_result.get('reasoning', '')
        if llm_reasoning:
            explanations.append(f"LLM分析: {llm_reasoning[:200]}")
        
        # RAG解释
        if rag_result and rag_result.get('matched_templates'):
            templates = rag_result.get('matched_templates', [])
            template_names = [t.get('name', '') for t in templates[:2]]
            explanations.append(f"匹配到已知钓鱼模板: {', '.join(template_names)}")
        
        # 多模态解释
        if multimodal_result and multimodal_result.get('image_analysis'):
            explanations.append("检测到可疑图像内容")
        
        if not explanations:
            return "未检测到明显的钓鱼特征"
        
        return " | ".join(explanations)
    
    def _generate_recommendations(self, final_result: Dict) -> List[str]:
        """生成建议"""
        label = final_result.get('label')
        score = final_result.get('score', 0.0)
        
        recommendations = []
        
        if label == DetectionLabel.PHISHING:
            recommendations.append("强烈建议：不要点击邮件中的任何链接")
            recommendations.append("不要回复此邮件或提供任何个人信息")
            recommendations.append("如果涉及账户，请直接访问官方网站验证")
            recommendations.append("建议将此邮件标记为垃圾邮件并删除")
        elif label == DetectionLabel.SUSPICIOUS:
            recommendations.append("建议谨慎处理此邮件")
            recommendations.append("验证发件人身份后再采取行动")
            recommendations.append("不要点击可疑链接")
        else:
            recommendations.append("邮件看起来正常，但仍需保持警惕")
        
        return recommendations

