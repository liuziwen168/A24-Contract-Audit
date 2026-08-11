from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.api import Schema


class ContractTypeIn(Schema):
    contract_type: Literal["purchase", "sales", "nda", "outsourcing", "labor", "other"]
    comment: str | None = Field(default=None, max_length=2000)


class ElementIn(Schema):
    value: str = Field(min_length=1)
    comment: str | None = Field(default=None, max_length=2000)


class RiskIn(Schema):
    risk_level: Literal["high", "medium", "low"] | None = None
    suggestion: str | None = None
    risk_status: Literal["active", "modified", "dismissed"] | None = None
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def has_change(self):
        if self.risk_level is None and self.suggestion is None and self.risk_status is None:
            raise ValueError("one risk field is required")
        return self


class OverallRiskIn(Schema):
    overall_risk_level: Literal["high", "medium", "low"]
    overall_score: Decimal = Field(ge=0, le=100)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackIn(Schema):
    target_type: Literal["contractType", "element", "risk", "overallRisk"]
    target_id: int | None = None
    judgment: Literal["correct", "incorrect", "modified"]
    corrected_value: str | None = None
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def valid_target(self):
        if (self.target_type in {"element", "risk"}) != (self.target_id is not None):
            raise ValueError("invalid targetId")
        if self.judgment == "modified" and not self.corrected_value:
            raise ValueError("correctedValue is required")
        return self


class OpinionIn(Schema):
    opinion: str | None = Field(default=None, max_length=5000)
