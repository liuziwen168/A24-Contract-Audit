from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.schemas.api import Schema, camel

ContractType = Literal["purchase", "sales", "nda", "outsourcing", "labor", "service", "other"]
RiskLevel = Literal["high", "medium", "low", "critical"]
ElementType = Literal[
    "partyA", "partyB", "signingDate", "contractAmount", "performanceTerm", "disputeResolution"
]


class AISchema(Schema):
    model_config = ConfigDict(alias_generator=camel, populate_by_name=True, extra="ignore")

    @field_validator("page", "paragraph_index", mode="before", check_fields=False)
    @classmethod
    def coerce_int(cls, v: object) -> object:
        """AI 可能返回浮点数或负数（表示无），规整为整数或 None"""
        if v is None:
            return None
        if isinstance(v, float):
            v = int(v)
        if isinstance(v, int) and v < 0:
            return None
        return v


class AIElement(AISchema):
    element_type: ElementType
    element_name: str = Field(min_length=1, max_length=80)
    value: str
    page: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    confidence: Decimal | None = Field(default=None, ge=0, le=1)

    @field_validator("element_type", mode="before")
    @classmethod
    def normalize_element_type(cls, v: str) -> str:
        """将 AI 返回的中文要素类型映射为枚举值"""
        mapping = {
            "甲方": "partyA", 
            "乙方": "partyB",
            "签署日期": "signingDate", 
            "合同金额": "contractAmount",
            "履行期限": "performanceTerm", 
            "争议解决": "disputeResolution",
        }
        return mapping.get(v, v)


class AIRisk(AISchema):
    """风险模型 - 允许额外字段以兼容AI服务返回的 rule_snapshot"""
    model_config = ConfigDict(extra="allow")  # ← 关键修改：允许额外字段

    risk_type: str = Field(min_length=1, max_length=40)
    risk_name: str = Field(min_length=1, max_length=100)
    risk_level: RiskLevel
    clause_text: str
    page: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    basis: str
    suggestion: str
    confidence: Decimal | None = Field(default=None, ge=0, le=1)
    rule_id: int | None = Field(default=None, ge=1)

    @field_validator("risk_level", mode="before")
    @classmethod
    def normalize_level(cls, v: str) -> str:
        """中文风险等级 → 英文"""
        mapping = {
            "高": "high", 
            "高风险": "high", 
            "中": "medium", 
            "中风险": "medium", 
            "低": "low", 
            "低风险": "low", 
            "严重": "critical"
        }
        return mapping.get(v, v)


class AIError(AISchema):
    code: str | None = Field(default=None, max_length=32)
    message: str | None = Field(default=None, max_length=500)


class AIReviewResult(AISchema):
    """AI审核结果 - 允许额外字段以兼容"""
    model_config = ConfigDict(extra="allow")  # ← 关键修改：允许额外字段

    request_id: str = Field(min_length=1, max_length=64)
    contract_id: int = Field(gt=0)
    contract_type: ContractType
    type_confidence: Decimal = Field(ge=0, le=1)
    elements: list[AIElement]
    risks: list[AIRisk]
    missing_clauses: list[str]
    overall_risk_level: RiskLevel
    overall_score: Decimal = Field(ge=0, le=100)
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)
    prompt_version: str = Field(min_length=1, max_length=32)
    processing_time_ms: int = Field(ge=0)
    warnings: list[str]
    error: AIError | None

    @field_validator("missing_clauses", "warnings")
    @classmethod
    def string_arrays(cls, value: list[str]) -> list[str]:
        if any(not item for item in value):
            raise ValueError("array values must not be empty")
        return value

    @model_validator(mode="after")
    def failed_response_is_not_success(self) -> AIReviewResult:
        if self.error is not None and (self.elements or self.risks):
            raise ValueError("AI error responses must not include audit results")
        return self