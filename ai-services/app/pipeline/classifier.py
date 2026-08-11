"""合同分类器"""
import logging
from typing import Dict, Any, Optional

from app.core.exceptions import LLMCallError
from app.llm.qwen_client import QwenClient

logger = logging.getLogger(__name__)


class Classifier:
    VALID_TYPES = ["purchase", "sales", "nda", "outsourcing", "labor", "other"]

    KEYWORDS = {
        "purchase": ["采购", "购买", "供应商", "供货", "采购订单", "purchase"],
        "sales": ["销售", "出售", "代理商", "经销商", "销售合同", "sales"],
        "nda": ["保密", "机密", "confidential", "保密协议", "非披露"],
        "outsourcing": ["外包", "服务外包", "技术服务", "it服务", "软件开发", "outsourcing"],
        "labor": ["劳动", "劳务", "劳动合同", "聘用", "雇佣", "labor"]
    }

    def __init__(self):
        self.client = QwenClient()

    async def classify(self, text: str, contract_type: Optional[str] = None) -> Dict[str, Any]:
        if not text or len(text.strip()) < 10:
            return {
                "contract_type": "other",
                "type_confidence": 0.0
            }

        rule_result = self._classify_by_keywords(text)
        rule_type = rule_result["contract_type"]
        rule_confidence = rule_result["type_confidence"]

        logger.info(f"规则分类结果: {rule_type} (置信度: {rule_confidence:.2f})")

        try:
            logger.info("调用 Qwen LLM 进行精细分类...")
            llm_result = await self.client.classify_contract(text)
            logger.info(f"LLM返回结果: {llm_result}")

            llm_type = llm_result.get("contract_type", "other")
            llm_confidence = llm_result.get("type_confidence", 0.5)

            if llm_type not in self.VALID_TYPES:
                llm_type = "other"

            logger.info(f"使用LLM结果: {llm_type} (置信度: {llm_confidence:.2f})")
            return {"contract_type": llm_type, "type_confidence": llm_confidence}

        except Exception as e:
            logger.error(f"LLM调用失败，使用规则结果: {str(e)}")
            return rule_result

    def _classify_by_keywords(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        scores = {}

        for contract_type, keywords in self.KEYWORDS.items():
            count = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    count += 1
            score = count / len(keywords) if keywords else 0
            scores[contract_type] = score

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score < 0.05:
            return {"contract_type": "other", "type_confidence": 0.3}

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) >= 2:
            diff = sorted_scores[0][1] - sorted_scores[1][1]
            confidence = best_score * 0.8 + min(diff * 2, 0.2)
        else:
            confidence = best_score * 0.8

        confidence = min(0.95, max(0.1, confidence))

        return {"contract_type": best_type, "type_confidence": confidence}