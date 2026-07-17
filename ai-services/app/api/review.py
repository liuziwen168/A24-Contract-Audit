# app/api/review.py

import json
import logging
import time
from datetime import datetime

from fastapi import APIRouter

from app.schemas.request import ContractRequest
from app.schemas.response import (
    BaseResponse,
    FullReviewData,
    ReviewRiskItem,
    ReviewElementItem
)
from app.services.qwen_service import chat
from app.prompts.full_review_prompt import FULL_REVIEW_PROMPT
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同完整审核"])


def _parse_element(data: dict, key: str) -> ReviewElementItem:
    """解析单个要素，兼容新旧格式"""
    item = data.get(key, {})

    if isinstance(item, str):
        return ReviewElementItem(value=item)

    if isinstance(item, dict):
        return ReviewElementItem(
            value=item.get("value", item.get(key, "")),
            confidence=item.get("confidence"),
            position=item.get("position")
        )

    return ReviewElementItem()


@router.post(
    "/review",
    response_model=BaseResponse[FullReviewData],
    summary="合同完整审核（一键审核）",
    description="""
一站式完成合同分类、要素提取、风险评估和缺失条款检测。

返回AI初审快照（不可变），包含：
- 合同类型及置信度
- 6项关键要素（含置信度和位置）
- 风险列表（含原文、位置、依据、建议）
- 缺失条款清单
- 总体风险等级和评分
    """
)
async def review(request: ContractRequest):
    """
    完整合同审核接口

    参数：
        text: 合同全文

    返回：
        完整的AI初审结果快照
    """
    start_time = time.time()

    try:
        logger.info(f"收到完整审核请求，文本长度：{len(request.text)}")

        prompt = FULL_REVIEW_PROMPT.format(text=request.text)
        result = chat(prompt)

        cleaned = clean_json(result)

        if not cleaned:
            raise AIException("AI返回内容为空")

        data = json.loads(cleaned)

        # 解析合同类型
        contract_type = ContractValidator.validate_contract_type(
            data.get("contractType", "")
        )
        contract_type_confidence = data.get("contractTypeConfidence")

        # 解析要素
        party_a = _parse_element(data, "partyA")
        party_b = _parse_element(data, "partyB")
        amount = _parse_element(data, "amount")
        sign_date = _parse_element(data, "signDate")
        contract_period = _parse_element(data, "contractPeriod")
        dispute_resolution = _parse_element(data, "disputeResolution")

        # 验证要素值
        party_a.value = ContractValidator.validate_party_name(party_a.value)
        party_b.value = ContractValidator.validate_party_name(party_b.value)
        amount.value = ContractValidator.validate_amount(amount.value)
        sign_date.value = ContractValidator.validate_date(sign_date.value)
        contract_period.value = ContractValidator.validate_contract_period(contract_period.value)

        # 解析风险评估
        risk_level = ContractValidator.validate_risk_level(data.get("riskLevel", ""))
        risk_score = ContractValidator.validate_risk_score(data.get("riskScore", 0))

        risk_list = []
        for item in data.get("risks", []):
            risk_list.append(ReviewRiskItem(
                type=item.get("type", item.get("riskType", "")),
                level=ContractValidator.validate_risk_level(
                    item.get("level", item.get("riskLevel", ""))
                ),
                content=item.get("content", item.get("description", "")),
                basis=item.get("basis", ""),
                suggestion=item.get("suggestion", ""),
                originalText=item.get("originalText"),
                position=item.get("position")
            ))

        # 缺失条款
        missing_clauses = data.get("missingClauses", [])
        if isinstance(missing_clauses, list):
            missing_clauses = [str(c) for c in missing_clauses if c]
        else:
            missing_clauses = []

        # 解析告警
        parse_warnings = data.get("parseWarnings", [])
        if not isinstance(parse_warnings, list):
            parse_warnings = []

        elapsed = time.time() - start_time
        snapshot_time = datetime.now().isoformat()

        logger.info(
            f"完整审核完成 - 耗时: {elapsed:.2f}s, "
            f"类型: {contract_type}, "
            f"风险数: {len(risk_list)}, "
            f"缺失条款: {len(missing_clauses)}, "
            f"总体风险: {risk_level}({risk_score})"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=FullReviewData(
                contractType=contract_type,
                contractTypeConfidence=contract_type_confidence,
                partyA=party_a,
                partyB=party_b,
                amount=amount,
                signDate=sign_date,
                contractPeriod=contract_period,
                disputeResolution=dispute_resolution,
                riskLevel=risk_level,
                riskScore=risk_score,
                risks=risk_list,
                missingClauses=missing_clauses,
                parseWarnings=parse_warnings,
                snapshotVersion="1.0",
                snapshotCreatedAt=snapshot_time
            )
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        raise JSONParseException(
            message=f"AI返回JSON解析失败: {str(e)}",
            raw_content=result if 'result' in locals() else None
        )
    except AIException:
        raise
    except Exception as e:
        logger.exception("完整审核失败")
        raise AIException(f"完整审核失败：{str(e)}")
