# app/api/internal_review.py
"""
内部服务调用接口
供业务后端通过内部API调用AI审核能力
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.qwen_service import chat
from app.prompts.full_review_prompt import FULL_REVIEW_PROMPT
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])


class FullReviewRequest(BaseModel):
    """完整审核请求"""
    text: str
    request_id: Optional[str] = None


class FullReviewResponse(BaseModel):
    """完整审核响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


@router.post("/internal/v1/reviews/full")
async def full_review(request: FullReviewRequest):
    """
    完整合同审核（内部调用）

    供业务后端调用，完成合同分类、要素提取、风险评估的一站式审核。
    返回结构化的审核结果。
    """
    start_time = time.time()
    request_id = request.request_id or "N/A"

    try:
        logger.info(
            f"收到内部AI审核请求 - request_id: {request_id}, "
            f"文本长度: {len(request.text)}"
        )

        # 1. 构造 Prompt 并调用 AI
        prompt = FULL_REVIEW_PROMPT.format(text=request.text)
        result = chat(prompt)

        # 2. 清洗 JSON
        cleaned = clean_json(result)
        if not cleaned:
            logger.error(f"AI返回内容为空 - request_id: {request_id}")
            return FullReviewResponse(
                success=False,
                error="AI返回内容为空",
                error_code="AI_EMPTY_RESPONSE"
            )

        # 3. 解析 JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                f"AI返回JSON解析失败 - request_id: {request_id}, "
                f"error: {e}"
            )
            # 降级：返回原始文本
            return FullReviewResponse(
                success=True,
                data={
                    "raw": cleaned,
                    "_metadata": {
                        "review_time": datetime.now().isoformat(),
                        "request_id": request_id,
                        "text_length": len(request.text),
                        "warning": "AI返回格式异常，返回原始内容"
                    }
                }
            )

        # 4. 验证和规范化数据
        contract_type = ContractValidator.validate_contract_type(
            data.get("contractType", "")
        )

        risk_level = ContractValidator.validate_risk_level(
            data.get("riskLevel", "")
        )
        risk_score = ContractValidator.validate_risk_score(
            data.get("riskScore", 0)
        )

        # 规范化风险列表
        risks = []
        for item in data.get("risks", []):
            risks.append({
                "type": item.get("type", item.get("riskType", "")),
                "level": ContractValidator.validate_risk_level(
                    item.get("level", item.get("riskLevel", ""))
                ),
                "content": item.get("content", item.get("description", "")),
                "basis": item.get("basis", ""),
                "suggestion": item.get("suggestion", ""),
                "originalText": item.get("originalText"),
                "position": item.get("position")
            })

        # 5. 构建审核结果
        review_result = {
            "contractType": contract_type,
            "contractTypeConfidence": data.get("contractTypeConfidence"),

            "partyA": data.get("partyA", {}).get("value", "") if isinstance(data.get("partyA"), dict) else data.get("partyA", ""),
            "partyB": data.get("partyB", {}).get("value", "") if isinstance(data.get("partyB"), dict) else data.get("partyB", ""),
            "amount": data.get("amount", {}).get("value", "") if isinstance(data.get("amount"), dict) else data.get("amount", ""),
            "signDate": data.get("signDate", {}).get("value", "") if isinstance(data.get("signDate"), dict) else data.get("signDate", ""),
            "contractPeriod": data.get("contractPeriod", {}).get("value", "") if isinstance(data.get("contractPeriod"), dict) else data.get("contractPeriod", ""),
            "disputeResolution": data.get("disputeResolution", {}).get("value", "") if isinstance(data.get("disputeResolution"), dict) else data.get("disputeResolution", ""),

            "riskLevel": risk_level,
            "riskScore": risk_score,
            "risks": risks,
            "missingClauses": data.get("missingClauses", []),
            "parseWarnings": data.get("parseWarnings", []),

            "_metadata": {
                "review_time": datetime.now().isoformat(),
                "request_id": request_id,
                "text_length": len(request.text),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "snapshot_version": "1.0"
            }
        }

        elapsed = time.time() - start_time
        logger.info(
            f"内部AI审核完成 - request_id: {request_id}, "
            f"耗时: {elapsed:.2f}s, "
            f"类型: {contract_type}, "
            f"风险数: {len(risks)}, "
            f"风险等级: {risk_level}({risk_score})"
        )

        return FullReviewResponse(
            success=True,
            data=review_result
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"内部AI审核异常 - request_id: {request_id}, "
            f"耗时: {elapsed:.2f}s, "
            f"error: {e}",
            exc_info=True
        )
        return FullReviewResponse(
            success=False,
            error=str(e),
            error_code="AI_SERVICE_ERROR"
        )
