"""
检测API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import logging
import aiofiles

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Settings
from ..services.email_parser import EmailParser
from ..services.detection_engine import DetectionEngine
from ..models.schemas import DetectionResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/detect", tags=["detection"])

settings = Settings()
email_parser = EmailParser()
detection_engine = DetectionEngine(settings)

# 存储检测结果（实际应用中应使用数据库）
detection_results = {}

@router.post("/{job_id}", response_model=DetectionResult)
async def detect_email(job_id: str, background_tasks: BackgroundTasks):
    """执行邮件检测"""
    try:
        # 查找邮件文件
        email_files = list(settings.EMAILS_DIR.glob(f"{job_id}.*"))
        if not email_files:
            raise HTTPException(status_code=404, detail="未找到对应的邮件文件")
        
        email_file = email_files[0]
        
        # 解析邮件
        if email_file.suffix == '.eml':
            email_data = await email_parser.parse_email_file(email_file)
        else:
            # 读取文本文件
            async with aiofiles.open(email_file, 'r', encoding='utf-8') as f:
                email_text = await f.read()
            email_data = email_parser.parse_email_text(email_text)
        
        # 执行检测
        result = await detection_engine.detect(email_data)
        
        # 保存结果
        detection_results[job_id] = result
        
        logger.info(f"[{job_id}] 检测完成: {result['label']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] 检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@router.get("/{job_id}", response_model=DetectionResult)
async def get_detection_result(job_id: str):
    """获取检测结果"""
    if job_id not in detection_results:
        raise HTTPException(status_code=404, detail="未找到检测结果")
    
    return detection_results[job_id]

