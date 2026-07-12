EXTRACT_PROMPT = """
你是一名企业合同审核专家。

请阅读下面合同。

请提取以下信息：

1.甲方名称
2.乙方名称
3.合同金额
4.签订日期
5.合同期限

要求：

只能输出 JSON。

不要解释。

不要分析。

不要输出 Markdown。

不要输出 ```json。

返回格式必须严格如下：

{{
    "partyA":"",
    "partyB":"",
    "amount":"",
    "signDate":"",
    "contractPeriod":""
}}

如果没有找到对应字段，请填写空字符串。

合同内容：

{text}
"""