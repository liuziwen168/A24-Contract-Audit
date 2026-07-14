from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.schemas.api import Schema, camel

ContractType = Literal["purchase", "sales", "nda", "outsourcing", "labor", "other"]
RiskLevel = Literal["high", "medium", "low"]
ElementType = Literal[
    "partyA", "partyB", "signingDate", "contractAmount", "performanceTerm", "disputeResolution"
]


class AISchema(Schema):
    model_config = ConfigDict(alias_generator=camel, populate_by_name=True, extra="forbid")


class AIElement(AISchema):
    element_type: ElementType
    element_name: str = Field(min_length=1, max_length=80)
    value: str
    page: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    confidence: Decimal | None = Field(default=None, ge=0, le=1)


class AIRisk(AISchema):
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


class AIError(AISchema):
    code: str | None = Field(default=None, max_length=32)
    message: str | None = Field(default=None, max_length=500)


class AIReviewResult(AISchema):
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
    def failed_response_is_not_success(self) -> "AIReviewResult":
        if self.error is not None and (self.elements or self.risks):
            raise ValueError("AI error responses must not include audit results")
        return self
