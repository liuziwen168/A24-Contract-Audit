"""风险审核 - 规则引擎 + LLM双层识别"""
import logging
from typing import Dict, Any, List, Optional

from app.core.exceptions import LLMCallError
from app.llm.qwen_client import QwenClient
from app.rules.risk_rule_engine import RiskRuleEngine

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """风险分析器"""

    LEVEL_SCORES = {"high": 30, "medium": 15, "low": 5}
    RISK_TYPES = [
        "unlimitedLiability", "excessiveLiquidatedDamages", "unilateralTermination",
        "unfairPaymentTerms", "unfavorableJurisdiction", "missingDisputeResolution",
        "overbroadConfidentiality", "missingConfidentiality", "missingPerformanceTerm",
        "ambiguousAcceptance", "intellectualPropertyUnclear", "forceMajeureMissing"
    ]

    def __init__(self):
        self.llm = QwenClient()

    async def analyze(
        self,
        text: str,
        contract_type: str,
        risk_rules: List[Dict] = None
    ) -> Dict[str, Any]:
        if not text or len(text.strip()) < 50:
            return self._get_empty_result()

        risk_rules = risk_rules or []

        try:
            # 1. 规则引擎匹配
            rule_engine = RiskRuleEngine(risk_rules)
            rule_risks = rule_engine.match_all(text)
            logger.info(f"规则引擎匹配到 {len(rule_risks)} 条风险")

            # 2. LLM语义分析
            try:
                llm_result = await self.llm.analyze_risks_with_llm(text, contract_type, risk_rules)
                llm_risks = llm_result.get("risks", [])
                logger.info(f"LLM识别到 {len(llm_risks)} 条风险")
            except Exception as e:
                logger.warning(f"LLM风险分析失败: {str(e)}")
                llm_risks = []

            # 3. 合并去重
            merged_risks = self._merge_risks(rule_risks, llm_risks)

            # 4. 计算总体评分
            overall_level, overall_score = self._calculate_overall(merged_risks)

            return {
                "risks": merged_risks,
                "overall_risk_level": overall_level,
                "overall_score": overall_score
            }

        except Exception as e:
            logger.error(f"风险分析失败: {str(e)}")
            return self._get_empty_result()

    def _merge_risks(self, rule_risks: List[Dict], llm_risks: List[Dict]) -> List[Dict]:
        """合并规则风险和LLM风险"""
        risk_map = {}

        # 添加规则风险
        for risk in rule_risks:
            risk_type = risk.get("risk_type")
            if risk_type:
                risk["source"] = "rule"
                risk_map[risk_type] = risk

        # 添加LLM风险
        for risk in llm_risks:
            risk_type = risk.get("risk_type")
            if not risk_type or risk_type not in self.RISK_TYPES:
                continue

            if risk_type in risk_map:
                existing = risk_map[risk_type]
                llm_conf = risk.get("confidence", 0.5)
                existing_conf = existing.get("confidence", 0.5)
                existing["confidence"] = min(0.95, max(existing_conf, llm_conf))
                if risk.get("suggestion") and len(risk.get("suggestion", "")) > len(existing.get("suggestion", "")):
                    existing["suggestion"] = risk.get("suggestion")
                existing["source"] = "rule+llm"
            else:
                risk["source"] = "llm"
                risk["rule_id"] = None
                risk["rule_snapshot"] = None
                risk_map[risk_type] = risk

        return list(risk_map.values())

    def _calculate_overall(self, risks: List[Dict]) -> tuple:
        if not risks:
            return "low", 0.0

        total_score = 0
        for risk in risks:
            level = risk.get("risk_level", "low")
            total_score += self.LEVEL_SCORES.get(level, 5)

        total_score = min(100, total_score)

        if total_score >= 60:
            level = "high"
        elif total_score >= 30:
            level = "medium"
        else:
            level = "low"

        return level, float(total_score)

    def _get_empty_result(self) -> Dict[str, Any]:
        return {
            "risks": [],
            "overall_risk_level": "low",
            "overall_score": 0.0
        }