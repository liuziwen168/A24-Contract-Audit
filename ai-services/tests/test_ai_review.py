# tests/test_ai_review.py

import json
from app.services.ai_review_service import get_ai_review_service


def test_full_review():
    """测试完整审核"""
    service = get_ai_review_service()
    
    # 测试合同文本
    contract_text = """
    采购合同
    
    甲方：北京科技有限公司
    乙方：上海供应链有限公司
    
    合同金额：500万元
    
    签订日期：2024-01-15
    
    合同期限：2024-02-01至2024-12-31
    
    第一条 付款方式
    乙方应在合同签订后30日内支付全部款项。
    
    第二条 违约责任
    违约方应承担相应的法律责任。
    """
    
    result = service.full_review(contract_text)
    
    print("=" * 50)
    print("AI审核结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 50)


if __name__ == "__main__":
    test_full_review()