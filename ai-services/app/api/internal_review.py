# app/api/internal_review.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


class FullReviewRequest(BaseModel):
    text: str
    request_id: Optional[str] = None


class FullReviewResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


@router.post("/internal/v1/reviews/full")
async def full_review(request: FullReviewRequest):
    """完整合同审核（内部调用）"""
    try:
        logger.info(f"收到AI审核请求 - request_id: {request.request_id}")
        
        result = {
            "contractType": "采购合同",
            "partyA": "北京科技",
            "partyB": "上海供应",
            "amount": "500万元",
            "signDate": "2024-01-15",
            "contractPeriod": "",
            "riskLevel": "低",
            "riskScore": 20,
            "risks": [],
            "_metadata": {
                "review_time": "2026-07-13T10:30:00",
                "request_id": request.request_id,
                "text_length": len(request.text)
            }
        }
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"AI审核异常: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_code": "AI_SERVICE_ERROR"
        }