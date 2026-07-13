from fastapi import APIRouter
import json

from app.schemas.request import ContractRequest
from app.services.qwen_service import chat
from app.prompts.risk_prompt import RISK_PROMPT

router = APIRouter()


@router.post("/risk")
def risk(request: ContractRequest):
    """
    合同风险识别
    """

    prompt = RISK_PROMPT.format(
        text=request.text
    )

    result = chat(prompt)

    # 尝试把大模型返回的 JSON 字符串解析成 Python 对象
    try:
        risks = json.loads(result)
    except Exception:
        risks = [
            {
                "riskType": "解析失败",
                "riskLevel": "未知",
                "description": result,
                "suggestion": "检查 Prompt 或模型输出格式"
            }
        ]

    return {
        "riskList": risks
    }