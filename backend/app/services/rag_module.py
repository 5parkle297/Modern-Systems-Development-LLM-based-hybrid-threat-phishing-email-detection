"""
RAG检索增强生成模块
参考：repositories/Phishing-Detection-System-with-RAG-and-LLM-Integration
"""
import os
from typing import Dict, List, Optional
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class RAGModule:
    """RAG检索模块"""
    
    def __init__(self, knowledge_base_dir: Path, similarity_threshold: float = 0.7):
        """初始化RAG模块"""
        self.knowledge_base_dir = knowledge_base_dir
        self.similarity_threshold = similarity_threshold
        self.vector_store = None
        self.embeddings = None
        self.knowledge_base = []
        self._initialize_rag()
    
    def _initialize_rag(self):
        """初始化RAG系统"""
        try:
            # 加载知识库
            self._load_knowledge_base()
            
            # 初始化向量数据库（如果可用）
            try:
                from langchain.embeddings import HuggingFaceEmbeddings
                from langchain.vectorstores import FAISS
                try:
                    # langchain 0.0.350
                    from langchain.schema import Document
                except ImportError:
                    # fallback for older versions
                    from langchain.docstore.document import Document
                
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                # 如果已有向量数据库，加载它
                vector_store_path = self.knowledge_base_dir / "vector_store"
                if vector_store_path.exists():
                    # 对当前依赖版本，直接使用基本签名加载
                    self.vector_store = FAISS.load_local(
                        str(vector_store_path),
                        self.embeddings,
                    )
                else:
                    # 创建新的向量数据库
                    self._build_vector_store()
            except Exception as e:
                logger.warning(f"向量数据库初始化失败，将使用简单匹配: {e}")
                self.vector_store = None
        except Exception as e:
            logger.error(f"RAG模块初始化失败: {e}")
    
    def _load_knowledge_base(self):
        """加载知识库"""
        # 加载已知钓鱼模板
        templates_file = self.knowledge_base_dir / "phishing_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
            except Exception as e:
                logger.error(f"加载知识库失败: {e}")
                self.knowledge_base = []
        else:
            # 创建默认知识库
            self.knowledge_base = self._create_default_knowledge_base()
            self._save_knowledge_base()
    
    def _create_default_knowledge_base(self) -> List[Dict]:
        """创建默认知识库"""
        return [
            {
                "id": "template_1",
                "name": "银行账户验证",
                "pattern": "verify your bank account",
                "description": "要求验证银行账户的钓鱼邮件",
                "indicators": ["银行", "验证", "账户", "安全"]
            },
            {
                "id": "template_2",
                "name": "密码重置",
                "pattern": "reset your password",
                "description": "要求重置密码的钓鱼邮件",
                "indicators": ["密码", "重置", "过期", "安全"]
            },
            {
                "id": "template_3",
                "name": "中奖通知",
                "pattern": "congratulations winner",
                "description": "虚假中奖通知钓鱼邮件",
                "indicators": ["中奖", "奖品", "领取", "限时"]
            }
        ]
    
    def _save_knowledge_base(self):
        """保存知识库"""
        templates_file = self.knowledge_base_dir / "phishing_templates.json"
        try:
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
    
    def _build_vector_store(self):
        """构建向量数据库"""
        if not self.embeddings or not self.knowledge_base:
            return
        
        try:
            from langchain.vectorstores import FAISS
            try:
                from langchain.schema import Document
            except ImportError:
                from langchain.docstore.document import Document
            
            # 创建文档
            documents = []
            for item in self.knowledge_base:
                doc_text = f"{item.get('name', '')} {item.get('description', '')} {item.get('pattern', '')}"
                doc = Document(page_content=doc_text, metadata={"id": item.get('id', '')})
                documents.append(doc)
            
            # 构建向量数据库
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            
            # 保存向量数据库
            vector_store_path = self.knowledge_base_dir / "vector_store"
            self.vector_store.save_local(str(vector_store_path))
        except Exception as e:
            logger.error(f"构建向量数据库失败: {e}")
    
    def retrieve(self, email_data: Dict, features: Dict) -> Dict:
        """检索相关信息"""
        if not self.knowledge_base:
            return {
                'matched_templates': [],
                'similarity_scores': [],
                'evidence': '知识库为空'
            }
        
        # 构建查询文本
        query_text = self._build_query(email_data, features)
        
        # 使用向量数据库检索（如果可用）
        if self.vector_store:
            return self._vector_retrieve(query_text)
        else:
            # 使用简单文本匹配
            return self._simple_retrieve(query_text)
    
    def _build_query(self, email_data: Dict, features: Dict) -> str:
        """构建查询文本"""
        subject = email_data.get('subject', '')
        body_text = email_data.get('body_text', '')[:500]
        text_features = features.get('text_features', {})
        suspicious_phrases = text_features.get('suspicious_phrases', [])
        
        query = f"{subject} {body_text} {' '.join(suspicious_phrases)}"
        return query
    
    def _vector_retrieve(self, query_text: str) -> Dict:
        """使用向量数据库检索"""
        try:
            # 检索最相似的文档
            docs = self.vector_store.similarity_search_with_score(
                query_text,
                k=3
            )
            
            matched_templates = []
            similarity_scores = []
            
            for doc, score in docs:
                # 分数越低越相似（FAISS使用L2距离）
                similarity = 1.0 / (1.0 + score) if score > 0 else 1.0
                
                if similarity >= self.similarity_threshold:
                    template_id = doc.metadata.get('id', '')
                    template = next(
                        (t for t in self.knowledge_base if t.get('id') == template_id),
                        None
                    )
                    if template:
                        matched_templates.append(template)
                        similarity_scores.append(similarity)
            
            evidence = f"找到{len(matched_templates)}个匹配的钓鱼模板" if matched_templates else "未找到匹配的钓鱼模板"
            
            return {
                'matched_templates': matched_templates,
                'similarity_scores': similarity_scores,
                'evidence': evidence
            }
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return self._simple_retrieve(query_text)
    
    def _simple_retrieve(self, query_text: str) -> Dict:
        """简单文本匹配检索"""
        query_lower = query_text.lower()
        matched_templates = []
        similarity_scores = []
        
        for template in self.knowledge_base:
            pattern = template.get('pattern', '').lower()
            indicators = template.get('indicators', [])
            
            # 检查模式匹配
            if pattern and pattern in query_lower:
                matched_templates.append(template)
                similarity_scores.append(0.8)
            # 检查指标匹配
            elif indicators:
                match_count = sum(1 for ind in indicators if ind.lower() in query_lower)
                if match_count > 0:
                    similarity = min(0.7, match_count * 0.2)
                    matched_templates.append(template)
                    similarity_scores.append(similarity)
        
        evidence = f"找到{len(matched_templates)}个匹配的钓鱼模板" if matched_templates else "未找到匹配的钓鱼模板"
        
        return {
            'matched_templates': matched_templates[:3],  # 只返回前3个
            'similarity_scores': similarity_scores[:3],
            'evidence': evidence
        }

