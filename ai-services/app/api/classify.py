import logging
import time

from fastapi import APIRouter, HTTPException

from app.prompts.classify_prompt import CLASSIFY_PROMPT
from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, ContractTypeData
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
# ✅ 导入自定义异常
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["合同分类"]
)


@router.post(
    "/classify",
    response_model=BaseResponse[ContractTypeData],
    summary="合同分类",
    description="识别合同所属类型，例如采购合同、销售合同、劳动合同、保密协议等。"
)
def classify(request: ContractRequest):
    """
    合同分类接口

    参数：
        text：合同全文

    返回：
        合同类型及置信度
    """

    start_time = time.time()

    try:

        logger.info(
            f"收到合同分类请求，文本长度：{len(request.text)}"
        )

        # 构造 Prompt
        prompt = CLASSIFY_PROMPT.format(
            text=request.text
        )

        # 调用 AI
        result = chat(prompt)

        # 使用统一 JSON 清洗工具
        result = clean_json(result)

        # 去掉首尾空白及可能存在的单双引号
        result = result.strip().strip('"').strip("'")

        # ✅ 检查结果是否为空
        if not result:
            raise AIException("AI返回结果为空")

        cost = time.time() - start_time

        logger.info(
            f"合同分类完成，耗时：{cost:.2f}s，结果：{result}"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=ContractTypeData(
                contractType=result,
                confidence=None
            )
        )

    # ✅ 使用自定义异常
    except AIException:
        raise
    
    except Exception as e:

        logger.exception("合同分类失败")

        raise AIException(
            message=f"合同分类失败：{str(e)}"
        )