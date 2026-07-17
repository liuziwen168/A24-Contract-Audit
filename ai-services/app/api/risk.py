# app/api/risk.py

import json
import logging
import time

from fastapi import APIRouter

from app.schemas.request import ContractRequest
from app.schemas.response import BaseResponse, RiskData, RiskItem
from app.prompts.risk_prompt import RISK_PROMPT
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合同风险评估"])


@router.post(
    "/risk",
    response_model=BaseResponse[RiskData],
    summary="合同风险评估",
    description="识别合同中的风险点，输出等级、原文位置、依据和修改建议（≥10类风险）"
)
async def risk(request: ContractRequest):
    """
    合同风险评估接口

    参数：
        text: 合同全文

    返回：
        总体风险等级(riskLevel)、风险评分(riskScore: 0~100)、风险列表
        每条风险包含：类型、等级、描述、原文、位置、依据、建议
    """
    start_time = time.time()

    try:
        logger.info(f"收到风险识别请求，文本长度：{len(request.text)}")

        prompt = RISK_PROMPT.format(text=request.text)
        result = chat(prompt)

        cleaned = clean_json(result)

        if not cleaned:
            raise AIException("AI返回内容为空，无法解析")

        data = json.loads(cleaned)

        risk_list = []
        overall_level = "低"
        overall_score = 0

        # 新格式：包含 riskLevel 和 riskScore
        if isinstance(data, dict):
            overall_level_raw = data.get("riskLevel", "")
            overall_level = ContractValidator.validate_risk_level(overall_level_raw)
            overall_score = ContractValidator.validate_risk_score(data.get("riskScore", 0))

            risk_items = data.get("risks", data.get("riskList", []))

            for item in risk_items:
                risk_list.append(RiskItem(
                    riskType=item.get("riskType", ""),
                    riskLevel=ContractValidator.validate_risk_level(item.get("riskLevel", "")),
                    description=item.get("description", item.get("content", "")),
                    suggestion=item.get("suggestion", ""),
                    originalText=item.get("originalText", item.get("originText")),
                    position=item.get("position"),
                    basis=item.get("basis")
                ))

        # 兼容旧格式：直接数组
        elif isinstance(data, list):
            for item in data:
                risk_list.append(RiskItem(
                    riskType=item.get("riskType", ""),
                    riskLevel=ContractValidator.validate_risk_level(item.get("riskLevel", "")),
                    description=item.get("description", ""),
                    suggestion=item.get("suggestion", ""),
                    originalText=item.get("originalText"),
                    position=item.get("position"),
                    basis=item.get("basis")
                ))
        else:
            raise AIException("AI返回格式错误：既不是数组也不是对象")

        elapsed = time.time() - start_time

        logger.info(
            f"风险识别完成 - 耗时: {elapsed:.2f}s, "
            f"总数: {len(risk_list)}, "
            f"总体等级: {overall_level}, 评分: {overall_score}"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=RiskData(
                riskLevel=overall_level,
                riskScore=overall_score,
                riskList=risk_list
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
        logger.exception("风险识别失败")
        raise AIException(f"风险识别失败：{str(e)}")
