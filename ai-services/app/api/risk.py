import json
import logging
import time

from fastapi import APIRouter, HTTPException

from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, RiskData, RiskItem
from app.prompts.risk_prompt import RISK_PROMPT
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
# ✅ 导入自定义异常
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同风险评估"])


@router.post(
    "/risk",
    response_model=BaseResponse[RiskData],
    summary="合同风险评估",
    description="识别合同中的风险点并给出修改建议"
)
async def risk(request: ContractRequest):

    start_time = time.time()

    try:
        logger.info(f"风险识别请求，文本长度：{len(request.text)}")

        prompt = RISK_PROMPT.format(text=request.text)

        result = chat(prompt)

        # 使用统一 JSON 清洗工具
        cleaned = clean_json(result)

        # 验证是否为有效的JSON
        if not cleaned:
            raise AIException("AI返回内容为空，无法解析")

        print("========== AI返回 ==========")
        print(cleaned)
        print("===========================")

        data = json.loads(cleaned)

        risk_list = []

        # AI 返回数组
        if isinstance(data, list):

            for item in data:

                risk_list.append(
                    RiskItem(
                        riskType=item.get("riskType", ""),
                        riskLevel=item.get("riskLevel", ""),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", "")
                    )
                )

        # AI 返回对象（兼容）
        elif isinstance(data, dict):

            for item in data.get("riskList", []):

                risk_list.append(
                    RiskItem(
                        riskType=item.get("riskType", ""),
                        riskLevel=item.get("riskLevel", ""),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", "")
                    )
                )

        else:
            raise AIException("AI返回格式错误：既不是数组也不是对象")

        cost = time.time() - start_time

        logger.info(f"风险识别完成，耗时：{cost:.2f}s，发现 {len(risk_list)} 个风险")

        return BaseResponse(
            code=0,
            message="success",
            data=RiskData(
                riskList=risk_list
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

        raise AIException(f"风险识别失败：{str(e)}")