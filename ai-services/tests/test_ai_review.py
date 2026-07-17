# tests/test_json_cleaner.py

import json
from app.utils.json_cleaner import clean_json


def test_clean_json_markdown():
    """测试清理Markdown代码块"""
    
    # 测试1: 带 ```json
    text1 = '```json\n{"key": "value"}\n```'
    result1 = clean_json(text1)
    assert json.loads(result1) == {"key": "value"}
    print("✅ 测试1通过: 清理 ```json")
    
    # 测试2: 带 ``` 
    text2 = '```\n{"key": "value"}\n```'
    result2 = clean_json(text2)
    assert json.loads(result2) == {"key": "value"}
    print("✅ 测试2通过: 清理 ```")
    
    # 测试3: 前后有解释文字
    text3 = '这是AI返回的结果：\n{"key": "value"}\n请参考。'
    result3 = clean_json(text3)
    assert json.loads(result3) == {"key": "value"}
    print("✅ 测试3通过: 清理解释文字")
    
    # 测试4: 数组
    text4 = '```json\n[{"key": "value1"}, {"key": "value2"}]\n```'
    result4 = clean_json(text4)
    assert len(json.loads(result4)) == 2
    print("✅ 测试4通过: 清理数组")
    
    # 测试5: 空字符串
    text5 = ""
    result5 = clean_json(text5)
    assert result5 == ""
    print("✅ 测试5通过: 空字符串")
    
    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    test_clean_json_markdown()