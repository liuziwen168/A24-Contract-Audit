from fastapi import APIRouter

from app.schemas.request import ContractRequest
from app.services.qwen_service import chat
from app.prompts.classify_prompt import CLASSIFY_PROMPT

router = APIRouter()


@router.post("/classify")
def classify(request: ContractRequest):

    prompt = CLASSIFY_PROMPT.format(
        text=request.text
    )

    result = chat(prompt)

    return {
        "contractType": result
    }