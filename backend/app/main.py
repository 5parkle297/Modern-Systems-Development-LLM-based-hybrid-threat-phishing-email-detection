"""
FastAPI应用主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Settings
from .api import upload, detection, results

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 加载配置
settings = Settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于LLM的混合威胁钓鱼邮件检测系统"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix=settings.API_V1_PREFIX)
app.include_router(detection.router, prefix=settings.API_V1_PREFIX)
app.include_router(results.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Phishing Email Detection System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

