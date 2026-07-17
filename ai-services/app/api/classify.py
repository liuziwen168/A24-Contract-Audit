# app/api/classify.py

import json
import logging
import time

from fastapi import APIRouter

from app.prompts.classify_prompt import CLASSIFY_PROMPT
from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, ContractTypeData
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同分类"])


@router.post(
    "/classify",
    response_model=BaseResponse[ContractTypeData],
    summary="合同分类",
    description="自动识别合同类型（采购/销售/劳动/保密/服务外包/其他），返回类型及置信度"
)
async def classify(request: ContractRequest):
    """
    合同分类接口

    参数：
        text: 合同全文

    返回：
        合同类型及分类置信度(0~1)
    """
    start_time = time.time()

    try:
        logger.info(f"收到合同分类请求，文本长度：{len(request.text)}")

        # 构造 Prompt
        prompt = CLASSIFY_PROMPT.format(text=request.text)

        # 调用 AI
        result = chat(prompt)

        # 清洗并解析 JSON
        cleaned = clean_json(result)

        if not cleaned:
            raise AIException("AI返回结果为空")

        data = json.loads(cleaned)

        contract_type = data.get("contractType", "").strip()
        confidence = data.get("confidence", None)

        # 验证合同类型
        contract_type = ContractValidator.validate_contract_type(contract_type)

        # 校验置信度
        if confidence is not None:
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                confidence = None

        elapsed = time.time() - start_time

        logger.info(
            f"合同分类完成 - 耗时: {elapsed:.2f}s, "
            f"类型: {contract_type}, 置信度: {confidence}"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=ContractTypeData(
                contractType=contract_type,
                confidence=confidence
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
        logger.exception("合同分类失败")
        raise AIException(message=f"合同分类失败：{str(e)}")
