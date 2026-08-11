"""标准条款比对器"""
import logging
from typing import Dict, Any, List

from app.llm.qwen_client import QwenClient

logger = logging.getLogger(__name__)


class ClauseComparator:
    """标准条款比对器"""

    # 常见条款类型关键词
    CLAUSE_KEYWORDS = {
        "dispute_resolution": ["争议", "管辖", "仲裁", "诉讼", "法院"],
        "confidentiality": ["保密", "机密", "商业秘密", "confidential"],
        "force_majeure": ["不可抗力", "force majeure"],
        "termination": ["解除", "终止"],
        "liability": ["责任", "赔偿", "违约"],
        "payment": ["付款", "支付", "结算"],
        "delivery": ["交付", "交货", "验收"],
        "warranty": ["保证", "保修", "质保"],
        "intellectual_property": ["知识产权", "版权", "专利", "商标"],
        "indemnification": ["赔偿", "补偿", "indemnify"],
        "governing_law": ["适用法律", "管辖法律"],
        "assignment": ["转让", "分包", "assignment"]
    }

    def __init__(self):
        self.llm = QwenClient()

    async def compare(self, text: str, standard_clauses: List[Dict] = None) -> Dict[str, Any]:
        """比对标准条款"""
        standard_clauses = standard_clauses or []

        if not text or len(text.strip()) < 50:
            return {"missing_clauses": [], "deviations": []}

        if not standard_clauses:
            return {"missing_clauses": [], "deviations": []}

        # 1. 规则比对
        rule_result = self._compare_by_rules(text, standard_clauses)

        # 2. LLM比对（增强）
        try:
            truncated = text[:5000]
            llm_result = await self.llm.compare_clauses(truncated, standard_clauses)
            logger.info(f"LLM比对结果: missing={len(llm_result.get('missing_clauses', []))}, deviations={len(llm_result.get('deviations', []))}")
            return self._merge_results(rule_result, llm_result)
        except Exception as e:
            logger.warning(f"LLM条款比对失败，使用规则结果: {str(e)}")
            return rule_result

    def _compare_by_rules(self, text: str, standard_clauses: List[Dict]) -> Dict[str, Any]:
        """基于规则的条款比对"""
        missing_clauses = []
        deviations = []

        for clause in standard_clauses:
            clause_type = clause.get("clause_type", "")
            keywords = self.CLAUSE_KEYWORDS.get(clause_type, [clause.get("name", "")])

            # 检查条款是否存在
            found = False
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    found = True
                    break

            if not found:
                missing_clauses.append(clause_type)
            else:
                # 简单检查内容是否匹配（简化版）
                expected = clause.get("content", "").lower()
                actual = text.lower()
                # 检查是否包含关键内容
                if len(expected) > 20:
                    key_parts = expected[:50].split()
                    for part in key_parts[:5]:
                        if len(part) > 3 and part not in actual:
                            deviations.append({
                                "clause_type": clause_type,
                                "expected": expected[:200],
                                "actual": f"合同包含{clause.get('name', '')}条款但内容有差异",
                                "severity": "medium"
                            })
                            break

        return {
            "missing_clauses": list(set(missing_clauses)),
            "deviations": deviations[:10]  # 限制数量
        }

    def _merge_results(self, rule_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """合并规则和LLM比对结果"""
        missing = list(set(rule_result.get("missing_clauses", []) + llm_result.get("missing_clauses", [])))
        deviations = rule_result.get("deviations", []) + llm_result.get("deviations", [])

        # 去重
        unique_deviations = []
        seen = set()
        for d in deviations:
            key = f"{d.get('clause_type', '')}_{d.get('expected', '')[:50]}"
            if key not in seen:
                seen.add(key)
                unique_deviations.append(d)

        return {
            "missing_clauses": missing,
            "deviations": unique_deviations[:10]
        }