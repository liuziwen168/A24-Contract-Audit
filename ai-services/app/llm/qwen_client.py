"""Qwen API客户端"""
import json
import logging
from typing import Dict, Any, Optional, List

import httpx

from app.core.config import settings
from app.core.exceptions import LLMCallError

logger = logging.getLogger(__name__)


class QwenClient:
    def __init__(self):
        self.base_url = settings.QWEN_BASE_URL
        self.api_key = settings.QWEN_API_KEY
        self.model = settings.QWEN_MODEL
        self.max_tokens = settings.QWEN_MAX_TOKENS
        self.temperature = settings.QWEN_TEMPERATURE

        if self.api_key:
            key_preview = self.api_key[:8] + "..." if len(self.api_key) > 8 else "***"
            logger.info(f"Qwen API Key 已配置: {key_preview}")
            logger.info(f"Qwen 模型: {self.model}")
        else:
            logger.warning("QWEN_API_KEY 未配置，将使用模拟模式")

        self.timeout = httpx.Timeout(
            timeout=settings.READ_TIMEOUT,
            connect=settings.CONNECTION_TIMEOUT,
            read=settings.READ_TIMEOUT,
            write=settings.READ_TIMEOUT,
            pool=settings.READ_TIMEOUT
        )
        self.max_retries = 2

    async def chat(
        self,
        messages: list,
        response_format: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("QWEN_API_KEY未配置，使用模拟模式")
            return {
                "success": True,
                "content": '{"contract_type": "other", "type_confidence": 0.5}',
                "parsed": {"contract_type": "other", "type_confidence": 0.5},
                "raw": {}
            }

        url = f"{self.base_url}/chat/completions"
        logger.info(f"调用Qwen API: {self.model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature
        }

        if response_format and response_format.get("type") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    error_text = response.text[:500]
                    logger.error(f"Qwen API调用失败: {response.status_code}")
                    logger.error(f"错误详情: {error_text}")
                    raise LLMCallError(f"Qwen API调用失败: {error_text}")

                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"Qwen API返回成功，内容长度: {len(content)}")

                try:
                    parsed = json.loads(content)
                    logger.info(f"JSON解析成功")
                    return {
                        "success": True,
                        "content": content,
                        "parsed": parsed,
                        "raw": result
                    }
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败: {e}")
                    return {
                        "success": True,
                        "content": content,
                        "parsed": None,
                        "raw": result
                    }

        except httpx.TimeoutException:
            logger.error("Qwen API调用超时")
            raise LLMCallError("Qwen API调用超时")
        except Exception as e:
            logger.error(f"Qwen API调用异常: {str(e)}")
            raise LLMCallError(f"Qwen API调用异常: {str(e)}")

    async def classify_contract(self, text: str) -> Dict[str, Any]:
        """合同分类"""
        if not self.api_key:
            logger.warning("无API Key，返回模拟结果")
            return {"contract_type": "other", "type_confidence": 0.5}

        prompt = f"""请对以下合同文本进行分类，判断其属于以下哪种类型：
- purchase: 采购合同
- sales: 销售合同
- nda: 保密协议
- outsourcing: 服务外包合同
- labor: 劳动合同
- other: 其他

合同文本：
{text[:2000]}

请以JSON格式输出：
{{"contract_type": "类型代码", "type_confidence": 0.95, "reason": "判断依据"}}
"""
        messages = [
            {"role": "system", "content": "你是一个专业的合同审核AI助手，请严格按照JSON格式输出。"},
            {"role": "user", "content": prompt}
        ]

        logger.info("开始调用Qwen API进行合同分类...")
        result = await self.chat(messages, response_format={"type": "json_object"})

        if result.get("parsed"):
            return result["parsed"]
        else:
            logger.warning("LLM返回结果解析失败，使用默认值")
            return {"contract_type": "other", "type_confidence": 0.5}

    async def extract_elements(self, text: str, contract_type: str) -> List[Dict[str, Any]]:
        """要素抽取"""
        if not self.api_key:
            logger.warning("无API Key，返回空结果")
            return []

        prompt = f"""请从以下合同中提取关键要素：

需要提取的要素：
1. partyA - 合同甲方
2. partyB - 合同乙方
3. signingDate - 签署日期 (格式: YYYY-MM-DD)
4. contractAmount - 合同金额 (数字，单位: 元)
5. performanceTerm - 履行期限
6. disputeResolution - 争议解决方式

合同类型：{contract_type}
合同文本：
{text[:3000]}

请以JSON格式输出：
{{
    "elements": [
        {{"element_type": "partyA", "element_name": "合同甲方", "value": "提取值", "page": 1, "paragraph_index": 5, "confidence": 0.95}}
    ]
}}
如果没有找到，value为"未明确"，confidence为0。
"""
        messages = [
            {"role": "system", "content": "你是一个专业的合同审核AI助手，请严格按照JSON格式输出。"},
            {"role": "user", "content": prompt}
        ]

        logger.info("开始调用Qwen API进行要素抽取...")
        result = await self.chat(messages, response_format={"type": "json_object"})

        if result.get("parsed"):
            return result["parsed"].get("elements", [])
        else:
            logger.warning("LLM返回结果解析失败，使用默认值")
            return []

    async def analyze_risks_with_llm(self, text: str, contract_type: str, risk_rules: List[Dict] = None) -> Dict[str, Any]:
        """使用LLM分析风险"""
        if not self.api_key:
            logger.warning("无API Key，返回空结果")
            return {"risks": [], "overall_risk_level": "low", "overall_score": 0.0}

        risk_rules = risk_rules or []

        rules_text = "\n".join([
            f"- {r.get('risk_type', '')}({r.get('risk_level', 'medium')}): {r.get('name', '')} - {r.get('rule_content', '')}"
            for r in risk_rules
        ]) if risk_rules else "（未提供预定义规则，请基于专业知识判断）"

        risk_types = [
            "unlimitedLiability: 无限责任",
            "excessiveLiquidatedDamages: 违约金过高",
            "unilateralTermination: 单方解除权",
            "unfairPaymentTerms: 不合理付款条件",
            "unfavorableJurisdiction: 管辖/争议解决不利",
            "missingDisputeResolution: 缺失争议解决条款",
            "overbroadConfidentiality: 保密义务过宽",
            "missingConfidentiality: 缺失保密条款",
            "missingPerformanceTerm: 缺失履行期限",
            "ambiguousAcceptance: 验收标准不明确",
            "intellectualPropertyUnclear: 知识产权归属不清",
            "forceMajeureMissing: 缺失不可抗力条款"
        ]

        prompt = f"""请分析以下{contract_type}合同的风险条款。

可能的风险类型：
{chr(10).join(risk_types)}

预定义规则参考：
{rules_text}

合同文本：
{text[:5000]}

请以JSON格式输出风险列表：
{{
    "risks": [
        {{
            "risk_type": "unlimitedLiability",
            "risk_name": "无限责任",
            "risk_level": "high",
            "clause_text": "风险条款原文",
            "page": 1,
            "paragraph_index": 10,
            "basis": "风险判断依据",
            "suggestion": "修改建议",
            "confidence": 0.85
        }}
    ],
    "overall_risk_level": "high/medium/low",
    "overall_score": 75.0
}}
评分规则：高风险30分，中风险15分，低风险5分，总分最高100分。
"""
        messages = [
            {"role": "system", "content": "你是一个专业的合同审核AI助手，请严格按照JSON格式输出。"},
            {"role": "user", "content": prompt}
        ]

        logger.info("开始调用Qwen API进行风险分析...")
        result = await self.chat(messages, response_format={"type": "json_object"})

        if result.get("parsed"):
            parsed = result["parsed"]
            return {
                "risks": parsed.get("risks", []),
                "overall_risk_level": parsed.get("overall_risk_level", "low"),
                "overall_score": parsed.get("overall_score", 0.0)
            }
        else:
            logger.warning("LLM返回结果解析失败，使用默认值")
            return {"risks": [], "overall_risk_level": "low", "overall_score": 0.0}

    async def compare_clauses(self, text: str, standard_clauses: List[Dict]) -> Dict[str, Any]:
        """标准条款比对"""
        if not self.api_key:
            logger.warning("无API Key，返回空结果")
            return {"missing_clauses": [], "deviations": []}

        if not standard_clauses:
            return {"missing_clauses": [], "deviations": []}

        clauses_text = "\n".join([
            f"- [{c.get('clause_type', '')}] {c.get('name', '')}: {c.get('content', '')[:200]}..."
            for c in standard_clauses
        ])

        prompt = f"""请将以下合同文本与标准条款进行比对，找出缺失或偏离的条款。

标准条款：
{clauses_text}

合同文本：
{text[:5000]}

请以JSON格式输出：
{{
    "missing_clauses": ["disputeResolution", "confidentiality"],
    "deviations": [
        {{"clause_type": "confidentiality", "expected": "标准条款内容", "actual": "合同实际内容", "severity": "medium"}}
    ]
}}
"""
        messages = [
            {"role": "system", "content": "你是一个专业的合同审核AI助手，请严格按照JSON格式输出。"},
            {"role": "user", "content": prompt}
        ]

        logger.info("开始调用Qwen API进行条款比对...")
        result = await self.chat(messages, response_format={"type": "json_object"})

        if result.get("parsed"):
            parsed = result["parsed"]
            return {
                "missing_clauses": parsed.get("missing_clauses", []),
                "deviations": parsed.get("deviations", [])
            }
        else:
            logger.warning("LLM返回结果解析失败，使用默认值")
            return {"missing_clauses": [], "deviations": []}