"""
结果查询API
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.schemas import DetectionHistoryResponse, DetectionHistoryItem
from .detection import detection_results

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/results", tags=["results"])

@router.get("/", response_model=DetectionHistoryResponse)
async def get_all_results(limit: int = 100, offset: int = 0):
    """获取所有检测结果"""
    items = []
    
    # 从存储中获取结果（实际应用中应从数据库查询）
    for job_id, result in list(detection_results.items())[offset:offset+limit]:
        items.append(DetectionHistoryItem(
            job_id=job_id,
            label=result['label'],
            score=result['overall_score'],
            timestamp=result['timestamp'],
            email_subject=result.get('features', {}).get('header_features', {}).get('subject', '')
        ))
    
    return DetectionHistoryResponse(
        total=len(detection_results),
        items=items
    )

@router.get("/{job_id}", response_model=DetectionHistoryItem)
async def get_result(job_id: str):
    """获取单个检测结果"""
    if job_id not in detection_results:
        raise HTTPException(status_code=404, detail="未找到检测结果")
    
    result = detection_results[job_id]
    return DetectionHistoryItem(
        job_id=job_id,
        label=result['label'],
        score=result['overall_score'],
        timestamp=result['timestamp'],
        email_subject=result.get('features', {}).get('header_features', {}).get('subject', '')
    )

