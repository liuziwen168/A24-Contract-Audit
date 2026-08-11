"""要素抽取器 - 规则预提取 + LLM提取"""
import re
import logging
from typing import Dict, Any, List

from app.core.exceptions import LLMCallError
from app.llm.qwen_client import QwenClient

logger = logging.getLogger(__name__)


class ElementExtractor:
    """合同要素抽取器"""

    ELEMENT_TYPES = ["partyA", "partyB", "signingDate", "contractAmount", "performanceTerm", "disputeResolution"]

    PATTERNS = {
        "partyA": [
            r"甲方[:：]\s*([^\n\r，,、。；;]+)",
            r"委托方[:：]\s*([^\n\r，,、。；;]+)",
            r"采购方[:：]\s*([^\n\r，,、。；;]+)"
        ],
        "partyB": [
            r"乙方[:：]\s*([^\n\r，,、。；;]+)",
            r"受托方[:：]\s*([^\n\r，,、。；;]+)",
            r"供应方[:：]\s*([^\n\r，,、。；;]+)"
        ],
        "signingDate": [
            r"签署日期[:：]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)",
            r"签订日期[:：]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)",
            r"日期[:：]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)"
        ],
        "contractAmount": [
            r"合同金额[:：]\s*[¥￥]?([\d,，.]+)\s*元",
            r"金额[:：]\s*[¥￥]?([\d,，.]+)\s*元",
            r"总价[:：]\s*[¥￥]?([\d,，.]+)\s*元"
        ],
        "performanceTerm": [
            r"履行期限[:：]\s*([^\n\r，,、。；;]+)",
            r"合同期限[:：]\s*([^\n\r，,、。；;]+)"
        ],
        "disputeResolution": [
            r"争议解决[:：]\s*([^\n\r，,、。；;]+)",
            r"管辖[:：]\s*([^\n\r，,、。；;]+)"
        ]
    }

    def __init__(self):
        self.llm = QwenClient()

    async def extract(self, text: str, contract_type: str) -> Dict[str, Any]:
        """抽取合同要素"""
        if not text or len(text.strip()) < 10:
            return {"elements": self._get_empty_elements()}

        # 1. 规则预提取
        rule_elements = self._extract_by_rules(text)

        # 2. LLM提取（降级时使用规则结果）
        try:
            truncated = text[:3000]
            llm_elements = await self.llm.extract_elements(truncated, contract_type)
            merged = self._merge_elements(rule_elements, llm_elements)
            return {"elements": merged}
        except Exception as e:
            logger.warning(f"LLM要素抽取失败，使用规则结果: {str(e)}")
            return {"elements": rule_elements}

    def _extract_by_rules(self, text: str) -> List[Dict[str, Any]]:
        """基于规则提取要素"""
        elements = []

        for elem_type, patterns in self.PATTERNS.items():
            value = None
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    break

            if elem_type == "signingDate" and value:
                value = self._normalize_date(value)
            elif elem_type == "contractAmount" and value:
                value = self._normalize_amount(value)

            elements.append({
                "element_type": elem_type,
                "element_name": self._get_element_name(elem_type),
                "value": value or "未明确",
                "page": None,
                "paragraph_index": None,
                "confidence": 0.6 if value else 0.0
            })

        return elements

    def _merge_elements(self, rule_elements: List[Dict], llm_elements: List[Dict]) -> List[Dict]:
        """合并规则和LLM提取结果"""
        rule_map = {e["element_type"]: e for e in rule_elements}

        for llm_elem in llm_elements:
            elem_type = llm_elem.get("element_type")
            if elem_type in rule_map:
                if llm_elem.get("value") and llm_elem.get("value") != "未明确":
                    rule_map[elem_type] = llm_elem
                elif llm_elem.get("confidence", 0) > rule_map[elem_type].get("confidence", 0):
                    rule_map[elem_type]["confidence"] = llm_elem.get("confidence", 0.5)

        result = []
        for elem_type in self.ELEMENT_TYPES:
            if elem_type in rule_map:
                result.append(rule_map[elem_type])
            else:
                result.append({
                    "element_type": elem_type,
                    "element_name": self._get_element_name(elem_type),
                    "value": "未明确",
                    "page": None,
                    "paragraph_index": None,
                    "confidence": 0.0
                })

        return result

    def _normalize_date(self, date_str: str) -> str:
        """标准化日期"""
        import re
        match = re.search(r"(\d{4})[年-](\d{1,2})[月-](\d{1,2})", date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        return date_str

    def _normalize_amount(self, amount_str: str) -> str:
        """标准化金额"""
        import re
        match = re.search(r"([\d,，.]+)", amount_str)
        if match:
            return match.group(1).replace(",", "").replace("，", "")
        return amount_str

    def _get_element_name(self, elem_type: str) -> str:
        names = {
            "partyA": "合同甲方",
            "partyB": "合同乙方",
            "signingDate": "签署日期",
            "contractAmount": "合同金额",
            "performanceTerm": "履行期限",
            "disputeResolution": "争议解决方式"
        }
        return names.get(elem_type, elem_type)

    def _get_empty_elements(self) -> List[Dict]:
        return [
            {"element_type": t, "element_name": self._get_element_name(t),
             "value": "未明确", "page": None, "paragraph_index": None, "confidence": 0.0}
            for t in self.ELEMENT_TYPES
        ]