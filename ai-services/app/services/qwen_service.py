# app/services/qwen_service.py

import logging
import time
from typing import Optional
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from app.config import (
    DASHSCOPE_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def chat(
    prompt: str,
    system_prompt: str = "你是一名专业企业合同审核专家。",
    retry_count: int = 0
) -> str:
    """
    调用通义千问，支持重试
    """
    try:
        logger.debug(f"调用Qwen模型 - 重试次数: {retry_count}")
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=60
        )
        
        result = response.choices[0].message.content.strip()
        logger.debug(f"Qwen响应成功，长度: {len(result)}")
        return result
        
    except RateLimitError as e:
        logger.warning(f"Qwen限流错误: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return chat(prompt, system_prompt, retry_count + 1)
        raise
    
    except APIConnectionError as e:
        logger.warning(f"Qwen连接错误: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return chat(prompt, system_prompt, retry_count + 1)
        raise
    
    except APIError as e:
        logger.error(f"Qwen API错误: {e}")
        if e.code in ['400', '401', '403']:
            raise
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return chat(prompt, system_prompt, retry_count + 1)
        raise
    
    except Exception as e:
        logger.error(f"Qwen调用异常: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return chat(prompt, system_prompt, retry_count + 1)
        raise