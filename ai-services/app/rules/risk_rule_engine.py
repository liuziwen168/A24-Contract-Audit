"""风险规则引擎 - 12类内置规则 + 外部规则配置"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# 12类内置风险规则
BUILTIN_RULES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "rule_code": "R001",
        "risk_type": "unlimitedLiability",
        "name": "无限责任",
        "risk_level": "high",
        "rule_content": "合同中出现'无限责任'、'全部责任'、'一切损失'等无限扩大责任的表述",
        "patterns": [r"无限责任", r"全部责任", r"一切责任", r"任何损失", r"承担.*?全部"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 2,
        "rule_code": "R002",
        "risk_type": "excessiveLiquidatedDamages",
        "name": "违约金过高",
        "risk_level": "high",
        "rule_content": "违约金比例超过合同总额的30%，可能被法院认定为过高",
        "patterns": [r"违约金.*?(\d+)[%％]", r"罚息.*?(\d+)[%％]", r"滞纳金.*?(\d+)[%％]"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 3,
        "rule_code": "R003",
        "risk_type": "unilateralTermination",
        "name": "单方解除权",
        "risk_level": "high",
        "rule_content": "合同赋予一方随时、任意或无需理由的单方解除权",
        "patterns": [r"随时.*?解除", r"任意.*?解除", r"无需.*?理由.*?解除", r"单方.*?解除"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 4,
        "rule_code": "R004",
        "risk_type": "unfairPaymentTerms",
        "name": "不合理付款条件",
        "risk_level": "medium",
        "rule_content": "付款条件过于苛刻，如预付款比例过低、验收后付款周期过长",
        "patterns": [r"预付.*?(\d+)[%％]", r"质保金.*?(\d+)[%％]", r"验收.*?(\d+).*?日内"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 5,
        "rule_code": "R005",
        "risk_type": "unfavorableJurisdiction",
        "name": "管辖/争议解决不利",
        "risk_level": "medium",
        "rule_content": "争议管辖法院约定在对己方不利的地点",
        "patterns": [r"管辖.*?法院", r"争议.*?提交.*?仲裁", r"诉讼.*?所在地"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 6,
        "rule_code": "R006",
        "risk_type": "missingDisputeResolution",
        "name": "缺失争议解决条款",
        "risk_level": "medium",
        "rule_content": "合同中未约定争议解决方式（诉讼或仲裁）",
        "patterns": [],
        "required_keywords": ["争议", "管辖", "仲裁", "诉讼", "法院"],
        "is_missing_check": True
    },
    {
        "id": 7,
        "rule_code": "R007",
        "risk_type": "overbroadConfidentiality",
        "name": "保密义务过宽",
        "risk_level": "medium",
        "rule_content": "保密义务期限为永久或无限期，范围过于宽泛",
        "patterns": [r"永久.*?保密", r"无限期.*?保密", r"长期.*?保密", r"任何.*?信息.*?保密"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 8,
        "rule_code": "R008",
        "risk_type": "missingConfidentiality",
        "name": "缺失保密条款",
        "risk_level": "medium",
        "rule_content": "合同中未约定保密义务条款",
        "patterns": [],
        "required_keywords": ["保密", "机密", "商业秘密", "confidential"],
        "is_missing_check": True
    },
    {
        "id": 9,
        "rule_code": "R009",
        "risk_type": "missingPerformanceTerm",
        "name": "缺失履行期限",
        "risk_level": "medium",
        "rule_content": "合同中未约定履行期限",
        "patterns": [],
        "required_keywords": ["期限", "履行", "交付", "完成", "截止"],
        "is_missing_check": True
    },
    {
        "id": 10,
        "rule_code": "R010",
        "risk_type": "ambiguousAcceptance",
        "name": "验收标准不明确",
        "risk_level": "medium",
        "rule_content": "验收标准约定为'另行约定'或'甲方主观验收'，缺乏客观标准",
        "patterns": [r"另行.*?约定.*?验收", r"甲方.*?验收.*?为准", r"主观.*?验收"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 11,
        "rule_code": "R011",
        "risk_type": "intellectualPropertyUnclear",
        "name": "知识产权归属不清",
        "risk_level": "medium",
        "rule_content": "知识产权归属约定不明确，存在'共同所有'等模糊表述",
        "patterns": [r"归属.*?不明", r"共同.*?所有", r"知识产权.*?共有"],
        "required_keywords": [],
        "is_missing_check": False
    },
    {
        "id": 12,
        "rule_code": "R012",
        "risk_type": "forceMajeureMissing",
        "name": "缺失不可抗力条款",
        "risk_level": "low",
        "rule_content": "合同中未约定不可抗力条款",
        "patterns": [],
        "required_keywords": ["不可抗力", "force majeure", "免责"],
        "is_missing_check": True
    }
]


class RiskRuleEngine:
    """风险规则引擎"""

    def __init__(self, external_rules: List[Dict] = None):
        self.builtin_rules = BUILTIN_RULES
        self.external_rules = external_rules or []
        self._all_rules = self._merge_rules()

    def _merge_rules(self) -> List[Dict[str, Any]]:
        """合并内置规则和外部规则"""
        rule_map = {r["risk_type"]: r for r in self.builtin_rules}

        for ext_rule in self.external_rules:
            risk_type = ext_rule.get("risk_type")
            if risk_type and risk_type in rule_map:
                rule_map[risk_type] = ext_rule
            elif risk_type:
                rule_map[risk_type] = ext_rule

        return list(rule_map.values())

    def match_all(self, text: str) -> List[Dict[str, Any]]:
        """匹配所有规则"""
        if not text or len(text.strip()) < 10:
            return []

        matched_risks = []

        for rule in self._all_rules:
            matched = self._match_single_rule(text, rule)
            if matched:
                matched_risks.append(matched)

        return self._deduplicate_risks(matched_risks)

    def _match_single_rule(self, text: str, rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """匹配单条规则"""
        is_missing = rule.get("is_missing_check", False)
        patterns = rule.get("patterns", [])
        required_keywords = rule.get("required_keywords", [])

        if is_missing:
            return self._check_missing(text, rule, required_keywords)
        else:
            return self._check_pattern(text, rule, patterns)

    def _check_pattern(self, text: str, rule: Dict[str, Any], patterns: List[str]) -> Optional[Dict[str, Any]]:
        """检查正则模式匹配"""
        if not patterns:
            return None

        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._build_risk_result(rule, match.group(0))
            except re.error:
                continue

        return None

    def _check_missing(self, text: str, rule: Dict[str, Any], required_keywords: List[str]) -> Optional[Dict[str, Any]]:
        """检查缺失的必需条款"""
        if not required_keywords:
            return None

        found = False
        for keyword in required_keywords:
            if keyword.lower() in text.lower():
                found = True
                break

        if not found:
            return self._build_missing_result(rule)

        return None

    def _build_risk_result(self, rule: Dict[str, Any], matched_text: str) -> Dict[str, Any]:
        return {
            "risk_type": rule["risk_type"],
            "risk_name": rule["name"],
            "risk_level": rule["risk_level"],
            "clause_text": matched_text,
            "page": None,
            "paragraph_index": None,
            "basis": f"命中规则: {rule['rule_code']} - {rule['name']}",
            "suggestion": self._get_suggestion(rule["risk_type"]),
            "confidence": 0.85,
            "rule_id": rule["id"],
            "rule_snapshot": {
                "rule_id": rule["id"],
                "rule_code": rule["rule_code"],
                "rule_name": rule["name"],
                "rule_version": "v0.1",
                "rule_content": rule["rule_content"],
                "risk_type": rule["risk_type"],
                "risk_level": rule["risk_level"]
            }
        }

    def _build_missing_result(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "risk_type": rule["risk_type"],
            "risk_name": rule["name"],
            "risk_level": rule["risk_level"],
            "clause_text": f"【缺失】合同未包含{rule['name']}相关条款",
            "page": None,
            "paragraph_index": None,
            "basis": f"未检测到必需关键词: {', '.join(rule.get('required_keywords', []))}",
            "suggestion": f"建议补充{rule['name']}条款",
            "confidence": 0.75,
            "rule_id": rule["id"],
            "rule_snapshot": {
                "rule_id": rule["id"],
                "rule_code": rule["rule_code"],
                "rule_name": rule["name"],
                "rule_version": "v0.1",
                "rule_content": rule["rule_content"],
                "risk_type": rule["risk_type"],
                "risk_level": rule["risk_level"]
            }
        }

    def _get_suggestion(self, risk_type: str) -> str:
        suggestions = {
            "unlimitedLiability": "建议明确责任上限，避免无限责任表述",
            "excessiveLiquidatedDamages": "建议将违约金比例控制在合理范围内（不超过30%）",
            "unilateralTermination": "建议增加双方协商一致解除条款，而非单方任意解除",
            "unfairPaymentTerms": "建议调整付款条件，确保双方权利义务对等",
            "unfavorableJurisdiction": "建议争取在己方所在地法院管辖",
            "missingDisputeResolution": "建议补充争议解决条款",
            "overbroadConfidentiality": "建议明确保密期限和保密范围",
            "missingConfidentiality": "建议补充保密条款",
            "missingPerformanceTerm": "建议明确履行期限",
            "ambiguousAcceptance": "建议明确验收标准和验收程序",
            "intellectualPropertyUnclear": "建议明确知识产权归属",
            "forceMajeureMissing": "建议补充不可抗力条款"
        }
        return suggestions.get(risk_type, f"建议审查{risk_type}相关条款")

    def _deduplicate_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        risk_map = {}
        for risk in risks:
            risk_type = risk.get("risk_type")
            if risk_type and risk_type not in risk_map:
                risk_map[risk_type] = risk
        return list(risk_map.values())