# app/api/extract.py

import json
import logging
import time

from fastapi import APIRouter

from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, ExtractData, ExtractItem
from app.prompts.extract_prompt import EXTRACT_PROMPT
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同要素提取"])


def _parse_element(data: dict, key: str) -> ExtractItem:
    """解析单个要素，兼容新旧格式"""
    if data is None:
        return ExtractItem()

    item = data.get(key, {})

    # 兼容旧格式：直接返回字符串
    if isinstance(item, str):
        return ExtractItem(value=item)

    # 兼容旧格式：嵌套在 data 下
    if isinstance(item, dict):
        return ExtractItem(
            value=item.get("value", item.get(key, "")),
            confidence=item.get("confidence"),
            position=item.get("position"),
            originalText=item.get("originalText")
        )

    return ExtractItem()


@router.post(
    "/extract",
    response_model=BaseResponse[ExtractData],
    summary="合同要素提取",
    description="从合同中提取甲方、乙方、金额、签订日期、合同期限、争议解决方式，每项含置信度和原文位置"
)
async def extract(request: ContractRequest):
    """
    合同要素提取接口

    参数：
        text: 合同全文

    返回：
        6项关键要素，每项包含值(value)、置信度(confidence)、原文位置(position)
    """
    start_time = time.time()

    try:
        logger.info(f"收到要素提取请求，文本长度：{len(request.text)}")

        prompt = EXTRACT_PROMPT.format(text=request.text)
        result = chat(prompt)

        cleaned = clean_json(result)

        if not cleaned:
            raise AIException("AI返回内容为空")

        data = json.loads(cleaned)

        # 解析各要素
        party_a = _parse_element(data, "partyA")
        party_b = _parse_element(data, "partyB")
        amount = _parse_element(data, "amount")
        sign_date = _parse_element(data, "signDate")
        contract_period = _parse_element(data, "contractPeriod")
        dispute_resolution = _parse_element(data, "disputeResolution")

        # 验证关键字段
        party_a.value = ContractValidator.validate_party_name(party_a.value)
        party_b.value = ContractValidator.validate_party_name(party_b.value)
        amount.value = ContractValidator.validate_amount(amount.value)
        sign_date.value = ContractValidator.validate_date(sign_date.value)
        contract_period.value = ContractValidator.validate_contract_period(contract_period.value)

        elapsed = time.time() - start_time

        logger.info(
            f"要素提取完成 - 耗时: {elapsed:.2f}s, "
            f"甲方: {party_a.value[:20] if party_a.value else 'N/A'}, "
            f"乙方: {party_b.value[:20] if party_b.value else 'N/A'}"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=ExtractData(
                partyA=party_a,
                partyB=party_b,
                amount=amount,
                signDate=sign_date,
                contractPeriod=contract_period,
                disputeResolution=dispute_resolution
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
        logger.exception("要素提取失败")
        raise AIException(f"要素提取失败：{str(e)}")
