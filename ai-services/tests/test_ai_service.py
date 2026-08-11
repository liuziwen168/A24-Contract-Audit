"""AI服务单元测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rules.risk_rule_engine import RiskRuleEngine
from app.utils.text_utils import (
    clean_text,
    split_paragraphs,
    truncate_text,
    extract_dates,
    extract_amounts,
    locate_text_position,
)
from app.core.exceptions import AIException, FileParseError, LLMCallError


class TestRiskRuleEngine:
    """风险规则引擎测试"""

    def setup_method(self):
        self.engine = RiskRuleEngine()

    def test_builtin_rules_count(self):
        """内置规则数量检查：至少12类"""
        assert len(self.engine.BUILTIN_RULES) >= 12

    def test_match_unlimited_liability(self):
        """测试无限责任检测"""
        text = "乙方对本合同项下所产生的全部损失承担无限赔偿责任，不设赔偿上限。"
        results = self.engine.match_all(text)
        types = [r["risk_type"] for r in results]
        assert "unlimitedLiability" in types

    def test_match_excessive_damages(self):
        """测试违约金过高检测"""
        text = "若乙方逾期交付，每逾期一日，应向甲方支付合同总额50%的违约金。"
        results = self.engine.match_all(text)
        types = [r["risk_type"] for r in results]
        assert "excessiveLiquidatedDamages" in types

    def test_match_unilateral_termination(self):
        """测试单方解除权检测"""
        text = "甲方有权随时单方面解除本合同，无需说明理由，无需提前通知。"
        results = self.engine.match_all(text)
        types = [r["risk_type"] for r in results]
        assert "unilateralTermination" in types

    def test_match_missing_clause(self):
        """测试缺失条款检测"""
        text = "本合同由甲乙双方协商一致订立。双方应诚信履行。特此立约。"
        results = self.engine.match_all(text)
        types = [r["risk_type"] for r in results]
        # 应检测到多个缺失条款
        assert len(results) >= 3
        assert "missingDisputeResolution" in types

    def test_no_false_positive(self):
        """测试不应有误报"""
        text = "双方应友好协商解决争议。如协商不成，任何一方可向合同签订地人民法院提起诉讼。"
        text += "本合同自双方签字盖章之日起生效，有效期三年。"
        text += "双方应对合作过程中知悉的对方商业秘密承担保密义务，保密期限为合同终止后五年。"
        results = self.engine.match_all(text)
        # 此文本应较少风险
        high_risks = [r for r in results if r["risk_level"] == "high"]
        high_types = {r["risk_type"] for r in high_risks}
        # 不应错误识别无限责任等高风险
        assert "unlimitedLiability" not in high_types

    def test_calculate_overall_score(self):
        """测试风险评分计算"""
        risks = [
            {"risk_level": "high", "risk_type": "t1"},
            {"risk_level": "high", "risk_type": "t2"},
            {"risk_level": "medium", "risk_type": "t3"},
            {"risk_level": "medium", "risk_type": "t4"},
            {"risk_level": "low", "risk_type": "t5"},
        ]
        level, score = self.engine.calculate_overall_score(risks)
        expected_score = min(100.0, 2 * 30 + 2 * 15 + 1 * 5)
        assert score == expected_score
        assert level == "high"

    def test_calculate_score_zero_risks(self):
        """测试无风险时评分"""
        level, score = self.engine.calculate_overall_score([])
        assert score == 0.0
        assert level == "low"

    def test_external_rule_matching(self):
        """测试外部规则匹配"""
        text = "甲方委托乙方开发合同管理系统。"
        external_rules = [
            {
                "id": 100,
                "rule_code": "EXT001",
                "risk_type": "scopeUnclear",
                "name": "工作范围不明确",
                "risk_level": "medium",
                "rule_content": "开发",
                "keywords": "开发",
                "version": "v0.1",
            }
        ]
        results = self.engine.match_all(text, external_rules)
        ext_matches = [r for r in results if r.get("rule_code") == "EXT001"]
        assert len(ext_matches) >= 1

    def test_rule_result_structure(self):
        """测试规则结果结构完整性"""
        text = "本合同为采购合同，甲方向乙方采购设备一批。违约金为合同总额的80%。"
        results = self.engine.match_all(text)
        for r in results:
            assert "risk_type" in r
            assert "risk_name" in r
            assert "risk_level" in r
            assert "basis" in r
            assert "suggestion" in r
            assert "confidence" in r
            assert "rule_code" in r
            assert "source" in r
            assert r["risk_level"] in ("high", "medium", "low")
            assert 0 <= r["confidence"] <= 1


class TestTextUtils:
    """文本工具测试"""

    def test_clean_text(self):
        text = "  合同编号：12345\r\n\r\n甲方：\x00测试公司  \r\n  "
        cleaned = clean_text(text)
        assert "\r" not in cleaned
        assert "\x00" not in cleaned
        assert "甲方" in cleaned

    def test_split_paragraphs(self):
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        paras = split_paragraphs(text)
        assert len(paras) == 3

    def test_truncate_text(self):
        text = "A" * 15000
        truncated = truncate_text(text, max_chars=1000)
        assert len(truncated) <= 1100  # 允许少量超出（前后拼接+提示语）
        assert "中间内容已省略" in truncated

    def test_extract_dates(self):
        text = "本合同于2024年1月15日签订，有效期至2025年12月31日。"
        dates = extract_dates(text)
        assert len(dates) >= 2

    def test_extract_amounts(self):
        text = "合同金额为人民币500,000.00元（大写：伍拾万元整）。"
        amounts = extract_amounts(text)
        assert len(amounts) >= 1

    def test_locate_text_position(self):
        full_text = "第一页内容\n" * 50 + "\n\n" + "第二页内容\n" * 50
        target = "第二页"
        page, para = locate_text_position(full_text, target)
        assert page is not None
        assert page >= 1


class TestExceptions:
    """异常类测试"""

    def test_file_parse_error(self):
        exc = FileParseError("文件损坏", detail={"file": "test.docx"})
        assert exc.code == "FILE_PARSE_FAILED"
        assert "文件损坏" in exc.message

    def test_llm_call_error(self):
        exc = LLMCallError("API超时")
        assert exc.code == "LLM_API_FAILED"


class TestPipelineIntegration:
    """流水线集成测试（需要mock LLM）"""

    def test_rule_engine_returns_valid_structure(self):
        """集成：规则引擎输出验证"""
        engine = RiskRuleEngine()
        sample_contract = """
采购合同

甲方：XX科技有限公司
乙方：YY供应链有限公司

第一条 合同标的
甲方向乙方采购服务器设备100台。

第二条 合同金额
合同总金额为人民币1,000,000.00元。

第三条 违约责任
若乙方逾期交付，每逾期一日，应向甲方支付合同总额30%的违约金。
甲方有权随时单方面解除本合同。

第四条 争议解决
双方协商解决争议。
        """.strip()

        results = engine.match_all(sample_contract)
        # 验证基本结构
        assert isinstance(results, list)
        for r in results:
            assert all(k in r for k in [
                "risk_type", "risk_name", "risk_level",
                "clause_text", "basis", "suggestion",
                "confidence", "rule_code", "source",
            ])
        # 至少检测到违约金过高和单方解除权
        risk_types = {r["risk_type"] for r in results}
        assert "excessiveLiquidatedDamages" in risk_types
        assert "unilateralTermination" in risk_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
