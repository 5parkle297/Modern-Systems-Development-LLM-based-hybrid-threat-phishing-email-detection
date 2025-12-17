"""
配置文件
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# 先加载 .env 到环境变量，便于 os.getenv 使用（LLMDetector 等）
load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "Phishing Email Detection System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # 文件存储
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    EMAILS_DIR: Path = DATA_DIR / "emails"
    MODELS_DIR: Path = DATA_DIR / "models"
    KNOWLEDGE_BASE_DIR: Path = DATA_DIR / "knowledge_base"
    
    # LLM API配置（会从环境变量 / .env 读取）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None  # 例如 SiliconFlow 的 OpenAI 兼容地址
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM模型选择
    LLM_PROVIDER: str = "openai"  # openai, anthropic, google
    LLM_MODEL: str = "gpt-4-turbo-preview"  # 或 claude-3-opus, gemini-pro
    
    # 特征提取配置
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_EMAIL_LENGTH: int = 10000
    
    # RAG配置
    RAG_ENABLED: bool = True
    VECTOR_DB_TYPE: str = "faiss"  # faiss 或 chromadb
    SIMILARITY_THRESHOLD: float = 0.7
    
    # 检测引擎配置
    RULE_ENGINE_WEIGHT: float = 0.2
    ML_MODEL_WEIGHT: float = 0.2
    LLM_WEIGHT: float = 0.4
    RAG_WEIGHT: float = 0.1
    MULTIMODAL_WEIGHT: float = 0.1
    
    # 多模态配置
    MULTIMODAL_ENABLED: bool = True
    VLM_PROVIDER: str = "openai"  # openai, anthropic, google
    VLM_MODEL: str = "gpt-4-vision-preview"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建必要的目录
settings = Settings()
settings.EMAILS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

