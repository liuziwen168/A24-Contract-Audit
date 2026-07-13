# app/utils/text_processor.py

import re


def clean_text(text: str) -> str:
    """清洗文本"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


def validate_contract_text(text: str) -> bool:
    """验证是否为合同文本"""
    if not text or len(text.strip()) < 10:
        return False
    keywords = ['合同', '协议', '甲方', '乙方', '条款', '约定', '签署']
    return any(kw in text for kw in keywords)


def truncate_text(text: str, max_length: int = 50000) -> str:
    """截断过长文本"""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_period = truncated.rfind('。')
    last_newline = truncated.rfind('\n')
    cut_pos = max(last_period, last_newline)
    if cut_pos > max_length * 0.8:
        return truncated[:cut_pos] + "\n\n[合同内容过长，已截断...]"
    return truncated + "\n\n[合同内容过长，已截断...]"