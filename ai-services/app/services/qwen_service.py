from openai import OpenAI

from app.config import (
    DASHSCOPE_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE
)

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def chat(
    prompt: str,
    system_prompt: str = "你是一名专业企业合同审核专家。"
) -> str:
    """
    调用通义千问
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )

    return response.choices[0].message.content.strip()