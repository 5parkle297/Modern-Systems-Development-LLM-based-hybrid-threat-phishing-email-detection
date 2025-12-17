"""
Pydantic数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DetectionLabel(str, Enum):
    """检测标签"""
    PHISHING = "phishing"
    SUSPICIOUS = "suspicious"
    BENIGN = "benign"

class EmailUploadRequest(BaseModel):
    """邮件上传请求"""
    email_text: Optional[str] = Field(None, description="原始邮件文本")
    email_file: Optional[str] = Field(None, description="邮件文件路径（.eml）")

class EmailUploadResponse(BaseModel):
    """邮件上传响应"""
    job_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="上传成功消息")
    timestamp: datetime = Field(default_factory=datetime.now)

class FeatureExtraction(BaseModel):
    """特征提取结果"""
    text_features: Dict[str, Any] = Field(default_factory=dict)
    url_features: List[Dict[str, Any]] = Field(default_factory=list)
    header_features: Dict[str, Any] = Field(default_factory=dict)
    statistical_features: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

class RuleEngineResult(BaseModel):
    """规则引擎检测结果"""
    score: float = Field(..., ge=0.0, le=1.0)
    matched_rules: List[str] = Field(default_factory=list)
    spf_status: Optional[str] = None
    dkim_status: Optional[str] = None
    dmarc_status: Optional[str] = None

class LLMDetectionResult(BaseModel):
    """LLM检测结果"""
    label: DetectionLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="LLM的判断理由")
    provider: str = Field(..., description="使用的LLM提供商")

class RAGResult(BaseModel):
    """RAG检索结果"""
    matched_templates: List[Dict[str, Any]] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)
    evidence: str = Field(..., description="检索到的证据")

class MultimodalResult(BaseModel):
    """多模态检测结果"""
    has_images: bool = False
    image_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    webpage_analysis: Optional[Dict[str, Any]] = None

class DetectionResult(BaseModel):
    """完整检测结果"""
    job_id: str
    label: DetectionLabel
    overall_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # 各模块结果
    rule_engine: RuleEngineResult
    llm_detection: LLMDetectionResult
    rag_result: Optional[RAGResult] = None
    multimodal_result: Optional[MultimodalResult] = None
    
    # 特征
    features: FeatureExtraction
    
    # 解释性信息
    explanation: str = Field(..., description="检测结果解释")
    recommendations: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.now)

class DetectionHistoryItem(BaseModel):
    """检测历史项"""
    job_id: str
    label: DetectionLabel
    score: float
    timestamp: datetime
    email_subject: Optional[str] = None

class DetectionHistoryResponse(BaseModel):
    """检测历史响应"""
    total: int
    items: List[DetectionHistoryItem]

