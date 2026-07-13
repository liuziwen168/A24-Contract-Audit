import json

from app.services.qwen_service import chat

from app.prompts.classify_prompt import CLASSIFY_PROMPT
from app.prompts.extract_prompt import EXTRACT_PROMPT
from app.prompts.risk_prompt import RISK_PROMPT


def classify(text: str) -> str:
    """
    合同分类
    """

    prompt = CLASSIFY_PROMPT.format(
        text=text
    )

    result = chat(prompt)

    return result.strip()


def extract(text: str) -> dict:
    """
    要素抽取
    """

    prompt = EXTRACT_PROMPT.format(
        text=text
    )

    result = chat(prompt)

    return json.loads(result)


def risk(text: str) -> dict:
    """
    风险识别
    """

    prompt = RISK_PROMPT.format(
        text=text
    )

    result = chat(prompt)

    return json.loads(result)


def review(text: str) -> dict:
    """
    完整合同审核
    """

    # 1. 合同分类
    contract_type = classify(text)

    # 2. 要素抽取
    elements = extract(text)

    # 3. 风险识别
    risk_result = risk(text)

    # 4. 合并结果
    return {
        "contractType": contract_type,

        "partyA": elements.get("partyA"),
        "partyB": elements.get("partyB"),
        "amount": elements.get("amount"),
        "signDate": elements.get("signDate"),
        "contractPeriod": elements.get("contractPeriod"),

        "riskLevel": risk_result.get("riskLevel"),
        "riskScore": risk_result.get("riskScore"),
        "risks": risk_result.get("risks")
    }