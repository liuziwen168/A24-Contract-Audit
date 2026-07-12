from fastapi import APIRouter
from app.schemas.request import ContractRequest
from app.prompts.extract_prompt import EXTRACT_PROMPT
from app.services.qwen_service import chat

import json

router = APIRouter()


@router.post("/extract")
def extract(request: ContractRequest):

    # 生成 Prompt
    prompt = EXTRACT_PROMPT.format(
        text=request.text
    )

    # 调用大模型
    result = chat(prompt)

    print("====== AI返回结果 ======")
    print(result)
    print("=======================")

    # 去掉 Markdown 代码块
    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    try:
        data = json.loads(result)
        return data

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ai_result": result
        }