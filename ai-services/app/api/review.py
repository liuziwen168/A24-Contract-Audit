from fastapi import APIRouter
import json

from app.schemas.request import ContractRequest
from app.services.qwen_service import chat
from app.prompts.full_review_prompt import FULL_REVIEW_PROMPT

router = APIRouter()


@router.post("/review")
def review(request: ContractRequest):
    """
    AI合同完整审核
    """

    prompt = FULL_REVIEW_PROMPT.format(
        text=request.text
    )

    result = chat(prompt)

    try:
        return json.loads(result)

    except Exception:

        return {
            "raw": result
        }