"""文本处理工具"""
import re
from typing import List, Dict, Any, Optional, Tuple


def clean_text(text: str) -> str:
    """清洗文本"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\.,;:!?()（）《》""\'\-]', ' ', text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    """分句"""
    if not text:
        return []
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_paragraphs(text: str) -> List[str]:
    """分段"""
    if not text:
        return []
    paragraphs = text.split('\n')
    return [p.strip() for p in paragraphs if p.strip()]


def truncate_text(text: str, max_length: int = 4000) -> str:
    """截断文本"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_dates(text: str) -> List[str]:
    """提取日期"""
    if not text:
        return []
    patterns = [
        r'\d{4}[-年]\d{1,2}[-月]\d{1,2}日?',
        r'\d{4}/\d{1,2}/\d{1,2}',
        r'\d{4}\.\d{1,2}\.\d{1,2}'
    ]
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    return list(set(dates))


def extract_amounts(text: str) -> List[str]:
    """提取金额"""
    if not text:
        return []
    patterns = [
        r'[¥￥]?[\d,，.]+\.?\d*\s*元',
        r'[\d,，.]+\.?\d*\s*万元',
        r'[\d,，.]+\.?\d*\s*亿元'
    ]
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        amounts.extend(matches)
    return list(set(amounts))


def locate_text_position(text: str, keyword: str) -> Tuple[Optional[int], Optional[int]]:
    """定位文本位置"""
    if not text or not keyword:
        return None, None

    lines = text.split('\n')
    for line_idx, line in enumerate(lines):
        if keyword in line:
            char_idx = line.find(keyword)
            return line_idx, char_idx
    return None, None
