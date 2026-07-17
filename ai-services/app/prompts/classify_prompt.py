# app/prompts/classify_prompt.py

CLASSIFY_PROMPT = """
你是一名企业合同审核专家。

请阅读下面合同内容，判断合同属于哪种类型。

## 合同类型列表
1. 采购合同
2. 销售合同
3. 劳动合同
4. 保密协议
5. 服务外包合同
6. 其他合同

## 输出要求
请严格按以下JSON格式输出，只输出JSON，不要解释，不要Markdown：

{{
    "contractType": "合同类型名称",
    "confidence": 0.95
}}

- contractType: 必须是上述6种类型之一
- confidence: 0~1之间的数值，表示分类置信度

## 合同内容
{text}
"""
