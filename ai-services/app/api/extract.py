import json
import logging
import time

from fastapi import APIRouter, HTTPException

from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, ExtractData
from app.prompts.extract_prompt import EXTRACT_PROMPT
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
# ✅ 导入自定义异常
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同要素提取"])


@router.post(
    "/extract",
    response_model=BaseResponse[ExtractData],
    summary="合同要素提取",
    description="从合同中提取甲方、乙方、金额、签订日期、合同期限等信息"
)
async def extract(request: ContractRequest):
    """
    合同要素提取
    """

    start_time = time.time()

    try:
        logger.info(f"收到要素提取请求，文本长度：{len(request.text)}")

        prompt = EXTRACT_PROMPT.format(text=request.text)

        result = chat(prompt)

        # 使用统一 JSON 清洗工具
        cleaned = clean_json(result)

        # 验证是否为有效的JSON
        if not cleaned:
            raise AIException("AI返回内容为空")

        data = json.loads(cleaned)

        elapsed = time.time() - start_time

        logger.info(f"要素提取完成，耗时 {elapsed:.2f}s")

        return BaseResponse(
            code=0,
            message="success",
            data=ExtractData(
                partyA=data.get("partyA", ""),
                partyB=data.get("partyB", ""),
                amount=data.get("amount", ""),
                signDate=data.get("signDate", ""),
                contractPeriod=data.get("contractPeriod", "")
            )
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败：{e}")
        logger.error(f"AI返回内容：{result if 'result' in locals() else 'N/A'}")
        
        # ✅ 使用自定义异常
        raise JSONParseException(
            message=f"AI返回JSON解析失败：{str(e)}",
            raw_content=result if 'result' in locals() else None
        )

    except AIException:
        raise

    except Exception as e:
        logger.exception(e)
        raise AIException(f"要素提取失败：{str(e)}")