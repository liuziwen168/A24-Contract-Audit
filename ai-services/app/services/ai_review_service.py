# app/services/ai_review_service.py
"""
AI审核服务编排层
将文档解析、合同分类、要素提取、风险审核、条款比对组合成完整的审核流程
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.qwen_service import chat
from app.services.document_parser import parse_document, ParseResult
from app.prompts.classify_prompt import CLASSIFY_PROMPT
from app.prompts.extract_prompt import EXTRACT_PROMPT
from app.prompts.risk_prompt import RISK_PROMPT
from app.prompts.full_review_prompt import FULL_REVIEW_PROMPT
from app.prompts.clause_compare_prompt import CLAUSE_COMPARE_PROMPT, DEFAULT_STANDARD_CLAUSES
from app.utils.json_cleaner import clean_json
from app.utils.validators import ContractValidator

logger = logging.getLogger(__name__)


class AIReviewOrchestrator:
    """
    AI审核编排器

    支持两种审核模式：
    1. 分步审核（step-by-step）：依次调用分类→提取→风险→条款比对
    2. 一键审核（one-shot）：使用统一Prompt一次完成全部任务
    """

    def __init__(self, mode: str = "one-shot"):
        """
        Args:
            mode: "step-by-step" 或 "one-shot"
        """
        self.mode = mode
        self.validator = ContractValidator()

    # ============================================================
    # 1. 文档解析
    # ============================================================

    def parse(self, file_path: str) -> ParseResult:
        """解析合同文档"""
        logger.info(f"开始解析文档: {file_path}")
        result = parse_document(file_path)
        logger.info(
            f"文档解析完成 - 格式: {result.format_type}, "
            f"页数: {result.page_count}, "
            f"段落: {len(result.paragraphs)}"
        )
        return result

    # ============================================================
    # 2. 合同分类
    # ============================================================

    def classify(self, text: str) -> Dict[str, Any]:
        """合同分类"""
        prompt = CLASSIFY_PROMPT.format(text=text)
        result = chat(prompt)
        cleaned = clean_json(result)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # 降级：返回纯文本结果
            return {
                "contractType": self.validator.validate_contract_type(cleaned.strip()),
                "confidence": None
            }

        return {
            "contractType": self.validator.validate_contract_type(
                data.get("contractType", "")
            ),
            "confidence": data.get("confidence")
        }

    # ============================================================
    # 3. 要素提取
    # ============================================================

    def extract(self, text: str) -> Dict[str, Any]:
        """要素提取"""
        prompt = EXTRACT_PROMPT.format(text=text)
        result = chat(prompt)
        cleaned = clean_json(result)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return self._empty_extract_result()

        return {
            "partyA": self._parse_element(data, "partyA"),
            "partyB": self._parse_element(data, "partyB"),
            "amount": self._parse_element(data, "amount"),
            "signDate": self._parse_element(data, "signDate"),
            "contractPeriod": self._parse_element(data, "contractPeriod"),
            "disputeResolution": self._parse_element(data, "disputeResolution")
        }

    def _parse_element(self, data: dict, key: str) -> Dict[str, Any]:
        """解析单个要素"""
        item = data.get(key, {})
        if isinstance(item, str):
            return {"value": item, "confidence": None, "position": None}
        if isinstance(item, dict):
            return {
                "value": item.get("value", ""),
                "confidence": item.get("confidence"),
                "position": item.get("position")
            }
        return {"value": "", "confidence": None, "position": None}

    def _empty_extract_result(self) -> Dict[str, Any]:
        return {
            "partyA": {"value": "", "confidence": None, "position": None},
            "partyB": {"value": "", "confidence": None, "position": None},
            "amount": {"value": "", "confidence": None, "position": None},
            "signDate": {"value": "", "confidence": None, "position": None},
            "contractPeriod": {"value": "", "confidence": None, "position": None},
            "disputeResolution": {"value": "", "confidence": None, "position": None}
        }

    # ============================================================
    # 4. 风险评估
    # ============================================================

    def assess_risk(self, text: str) -> Dict[str, Any]:
        """风险评估"""
        prompt = RISK_PROMPT.format(text=text)
        result = chat(prompt)
        cleaned = clean_json(result)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"riskLevel": "低", "riskScore": 0, "risks": []}

        risks = []
        raw_risks = data.get("risks", data.get("riskList", []))
        if isinstance(data, list):
            raw_risks = data

        for item in raw_risks:
            risks.append({
                "type": item.get("riskType", item.get("type", "")),
                "level": self.validator.validate_risk_level(
                    item.get("riskLevel", item.get("level", ""))
                ),
                "content": item.get("description", item.get("content", "")),
                "basis": item.get("basis", ""),
                "suggestion": item.get("suggestion", ""),
                "originalText": item.get("originalText"),
                "position": item.get("position")
            })

        return {
            "riskLevel": self.validator.validate_risk_level(data.get("riskLevel", "")) if isinstance(data, dict) else "低",
            "riskScore": self.validator.validate_risk_score(data.get("riskScore", 0)) if isinstance(data, dict) else 0,
            "risks": risks
        }

    # ============================================================
    # 5. 条款比对
    # ============================================================

    def compare_clauses(
        self,
        text: str,
        standard_clauses: Optional[str] = None
    ) -> Dict[str, Any]:
        """标准条款比对"""
        clauses = standard_clauses or DEFAULT_STANDARD_CLAUSES
        prompt = CLAUSE_COMPARE_PROMPT.format(text=text, standard_clauses=clauses)
        result = chat(prompt)
        cleaned = clean_json(result)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"deviations": [], "missingClauses": [], "matchedCount": 0, "totalStandardClauses": 0}

        missing = [
            d.get("clauseName", "")
            for d in data.get("deviations", [])
            if d.get("deviationType") == "missing"
        ]

        return {
            "deviations": data.get("deviations", []),
            "missingClauses": missing,
            "matchedCount": data.get("matchedCount", 0),
            "totalStandardClauses": data.get("totalStandardClauses", 0)
        }

    # ============================================================
    # 6. 分步审核（step-by-step）
    # ============================================================

    def review_step_by_step(
        self,
        text: str,
        standard_clauses: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分步执行完整审核流程

        依次调用：分类 → 提取 → 风险 → 条款比对
        优点：每步独立，便于调试和追踪
        缺点：需要4次API调用，耗时较长
        """
        logger.info("开始分步审核...")

        # Step 1: 分类
        classify_result = self.classify(text)
        logger.info(f"Step 1/4 分类完成: {classify_result['contractType']}")

        # Step 2: 提取
        extract_result = self.extract(text)
        logger.info(f"Step 2/4 提取完成")

        # Step 3: 风险
        risk_result = self.assess_risk(text)
        logger.info(f"Step 3/4 风险评估完成: {len(risk_result['risks'])} 个风险")

        # Step 4: 条款比对
        clause_result = self.compare_clauses(text, standard_clauses)
        logger.info(f"Step 4/4 条款比对完成: {len(clause_result['missingClauses'])} 个缺失")

        # 合并结果
        return {
            "contractType": classify_result["contractType"],
            "contractTypeConfidence": classify_result.get("confidence"),
            **extract_result,
            "riskLevel": risk_result["riskLevel"],
            "riskScore": risk_result["riskScore"],
            "risks": risk_result["risks"],
            "missingClauses": clause_result["missingClauses"],
            "clauseDeviations": clause_result["deviations"],
            "snapshotVersion": "1.0",
            "snapshotCreatedAt": datetime.now().isoformat(),
            "reviewMode": "step-by-step"
        }

    # ============================================================
    # 7. 一键审核（one-shot）
    # ============================================================

    def review_one_shot(self, text: str) -> Dict[str, Any]:
        """
        使用统一Prompt一次完成全部审核

        优点：只需1次API调用，速度快
        缺点：单次Prompt较长，对模型输出格式要求高
        """
        logger.info("开始一键审核...")

        prompt = FULL_REVIEW_PROMPT.format(text=text)
        result = chat(prompt)
        cleaned = clean_json(result)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("一键审核JSON解析失败，返回原始内容")
            return {
                "raw": cleaned,
                "snapshotVersion": "1.0",
                "snapshotCreatedAt": datetime.now().isoformat(),
                "reviewMode": "one-shot",
                "warning": "AI输出格式异常"
            }

        # 验证和规范化
        normalized = {
            "contractType": self.validator.validate_contract_type(
                data.get("contractType", "")
            ),
            "contractTypeConfidence": data.get("contractTypeConfidence"),

            "partyA": self._parse_element(data, "partyA"),
            "partyB": self._parse_element(data, "partyB"),
            "amount": self._parse_element(data, "amount"),
            "signDate": self._parse_element(data, "signDate"),
            "contractPeriod": self._parse_element(data, "contractPeriod"),
            "disputeResolution": self._parse_element(data, "disputeResolution"),

            "riskLevel": self.validator.validate_risk_level(data.get("riskLevel", "")),
            "riskScore": self.validator.validate_risk_score(data.get("riskScore", 0)),
            "risks": [
                {
                    "type": r.get("type", r.get("riskType", "")),
                    "level": self.validator.validate_risk_level(
                        r.get("level", r.get("riskLevel", ""))
                    ),
                    "content": r.get("content", r.get("description", "")),
                    "basis": r.get("basis", ""),
                    "suggestion": r.get("suggestion", ""),
                    "originalText": r.get("originalText"),
                    "position": r.get("position")
                }
                for r in data.get("risks", [])
            ],
            "missingClauses": data.get("missingClauses", []),
            "parseWarnings": data.get("parseWarnings", []),
            "snapshotVersion": "1.0",
            "snapshotCreatedAt": datetime.now().isoformat(),
            "reviewMode": "one-shot"
        }

        logger.info(
            f"一键审核完成 - 类型: {normalized['contractType']}, "
            f"风险数: {len(normalized['risks'])}, "
            f"风险等级: {normalized['riskLevel']}({normalized['riskScore']})"
        )

        return normalized

    # ============================================================
    # 8. 自动模式选择
    # ============================================================

    def review(
        self,
        text: str,
        mode: Optional[str] = None,
        standard_clauses: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一审核入口

        Args:
            text: 合同文本
            mode: "step-by-step" / "one-shot" / None（自动选择）
            standard_clauses: 自定义标准条款

        Returns:
            审核结果字典
        """
        review_mode = mode or self.mode

        # 长文本（>8000字符）使用分步模式确保准确性
        if review_mode == "one-shot" and len(text) > 8000:
            logger.info(f"合同文本较长({len(text)}字符)，自动切换为分步审核模式")
            review_mode = "step-by-step"

        if review_mode == "step-by-step":
            return self.review_step_by_step(text, standard_clauses)
        else:
            return self.review_one_shot(text)


# ============================================================
# 便捷函数
# ============================================================

# 默认编排器（一键模式）
_default_orchestrator = AIReviewOrchestrator(mode="one-shot")


def review_contract(
    text: str,
    mode: str = "one-shot",
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：审核合同

    Args:
        text: 合同文本（如果提供file_path则忽略）
        mode: 审核模式
        file_path: 合同文件路径（可选，自动解析后审核）

    Returns:
        审核结果
    """
    orchestrator = AIReviewOrchestrator(mode=mode)

    if file_path:
        parse_result = orchestrator.parse(file_path)
        text = parse_result.full_text

    return orchestrator.review(text)
