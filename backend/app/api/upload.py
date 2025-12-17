"""
邮件上传API
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import aiofiles
from pathlib import Path
import uuid
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import Settings
from ..services.email_parser import EmailParser
from ..models.schemas import EmailUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

settings = Settings()
email_parser = EmailParser()

@router.post("/", response_model=EmailUploadResponse)
async def upload_email(
    email_file: Optional[UploadFile] = File(None),
    email_text: Optional[str] = Form(None)
):
    """上传邮件进行检测"""
    job_id = str(uuid.uuid4())
    
    try:
        # 保存邮件文件
        if email_file:
            # 保存上传的文件
            file_extension = Path(email_file.filename).suffix if email_file.filename else '.eml'
            saved_path = settings.EMAILS_DIR / f"{job_id}{file_extension}"
            
            async with aiofiles.open(saved_path, 'wb') as f:
                content = await email_file.read()
                await f.write(content)
            
            logger.info(f"[{job_id}] 邮件文件已保存: {saved_path}")
            
        elif email_text:
            # 保存文本邮件
            saved_path = settings.EMAILS_DIR / f"{job_id}.txt"
            async with aiofiles.open(saved_path, 'w', encoding='utf-8') as f:
                await f.write(email_text)
            
            logger.info(f"[{job_id}] 邮件文本已保存: {saved_path}")
        else:
            raise HTTPException(status_code=400, detail="请提供邮件文件或邮件文本")
        
        return EmailUploadResponse(
            job_id=job_id,
            message="邮件上传成功"
        )
    except Exception as e:
        logger.error(f"[{job_id}] 上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

