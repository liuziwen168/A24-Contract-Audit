import re


def clean_json(text: str) -> str:
    """
    清理 AI 返回内容，使其变成可 json.loads() 的字符串。

    支持以下情况：

    ① ```json ... ```
    ② ``` ... ```
    ③ AI 在 JSON 前后输出解释
    ④ 返回对象 {}
    ⑤ 返回数组 []
    """

    if not text:
        return ""

    text = text.strip()

    # 去掉 Markdown 标记
    text = text.replace("```json", "")
    text = text.replace("```JSON", "")
    text = text.replace("```", "")
    text = text.strip()

    # ---------- 找 JSON 对象 ----------
    obj_match = re.search(r"\{.*\}", text, re.S)

    # ---------- 找 JSON 数组 ----------
    arr_match = re.search(r"\[.*\]", text, re.S)

    # 同时存在对象和数组
    if obj_match and arr_match:

        if obj_match.start() < arr_match.start():
            return obj_match.group()

        return arr_match.group()

    # 只有对象
    if obj_match:
        return obj_match.group()

    # 只有数组
    if arr_match:
        return arr_match.group()

    # 没找到
    return text