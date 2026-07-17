# app/prompts/extract_prompt.py

EXTRACT_PROMPT = """
你是一名企业合同审核专家。

请阅读下面合同，提取以下关键要素。

## 需要提取的要素
1. 甲方名称 (partyA)
2. 乙方名称 (partyB)
3. 合同金额 (amount)
4. 签订日期 (signDate)
5. 合同期限 (contractPeriod)
6. 争议解决方式 (disputeResolution)

## 输出要求
请严格按以下JSON格式输出，每个要素包含值(value)、置信度(confidence)和原文位置(position)：

{{
    "partyA": {{
        "value": "北京科技有限公司",
        "confidence": 0.95,
        "position": "第1段"
    }},
    "partyB": {{
        "value": "上海商贸有限公司",
        "confidence": 0.95,
        "position": "第2段"
    }},
    "amount": {{
        "value": "100万元",
        "confidence": 0.90,
        "position": "第5段"
    }},
    "signDate": {{
        "value": "2024-01-15",
        "confidence": 0.98,
        "position": "第10段"
    }},
    "contractPeriod": {{
        "value": "2024-01-15至2025-01-14",
        "confidence": 0.92,
        "position": "第8段"
    }},
    "disputeResolution": {{
        "value": "向北京仲裁委员会申请仲裁",
        "confidence": 0.88,
        "position": "第15段"
    }}
}}

## 注意事项
- 只输出JSON，不要解释，不要Markdown，不要```json```
- 没有找到的字段，value 填空字符串，confidence 填0
- confidence 是0~1之间的数值，表示对该提取结果的置信度
- position 标注该信息在原文中的大致位置（如段落号、页码范围）
- 日期统一格式为 YYYY-MM-DD
- 金额格式为 "XXX万元" 或 "XXX元"

## 合同内容
{text}
"""
