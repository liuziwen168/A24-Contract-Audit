from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.domain import CONTRACT_TYPES, RISK_LEVELS, RISK_TYPES, ROLES, USER_STATUSES
from app.schemas.api import Schema

Role = Literal["user", "legalReviewer", "riskReviewer", "admin"]
UserStatus = Literal["active", "disabled"]
ContractType = Literal["purchase", "sales", "nda", "outsourcing", "labor", "other"]
RiskLevel = Literal["high", "medium", "low"]
RiskType = Literal[
    "unlimitedLiability",
    "excessiveLiquidatedDamages",
    "unilateralTermination",
    "unfairPaymentTerms",
    "unfavorableJurisdiction",
    "missingDisputeResolution",
    "overbroadConfidentiality",
    "missingConfidentiality",
    "missingPerformanceTerm",
    "ambiguousAcceptance",
    "intellectualPropertyUnclear",
    "forceMajeureMissing",
]


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class UserUpdateIn(Schema):
    username: str | None = Field(default=None, min_length=1, max_length=64)
    role: Role | None = None
    user_status: UserStatus | None = None

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value: object) -> object:
        return _trim(value)

    @field_validator("role")
    @classmethod
    def known_role(cls, value: str | None) -> str | None:
        if value is not None and value not in ROLES:
            raise ValueError("invalid role")
        return value

    @field_validator("user_status")
    @classmethod
    def known_status(cls, value: str | None) -> str | None:
        if value is not None and value not in USER_STATUSES:
            raise ValueError("invalid userStatus")
        return value

    @model_validator(mode="after")
    def has_change(self):
        if not self.model_fields_set:
            raise ValueError("one editable field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("editable fields cannot be null")
        return self


class UserCreateIn(Schema):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=4, max_length=256)
    role: Role = "user"

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value: object) -> object:
        return _trim(value)

    @field_validator("role")
    @classmethod
    def known_role(cls, value: str) -> str:
        if value not in ROLES:
            raise ValueError("invalid role")
        return value


class StandardClauseCreateIn(Schema):
    name: str = Field(min_length=1, max_length=100)
    contract_type: ContractType
    clause_type: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1)
    config_status: UserStatus = "active"

    @field_validator("name", "clause_type", "content", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return _trim(value)

    @field_validator("contract_type")
    @classmethod
    def known_contract_type(cls, value: str) -> str:
        if value not in CONTRACT_TYPES:
            raise ValueError("invalid contractType")
        return value

    @field_validator("config_status")
    @classmethod
    def known_status(cls, value: str) -> str:
        if value not in USER_STATUSES:
            raise ValueError("invalid configStatus")
        return value


class StandardClauseUpdateIn(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    contract_type: ContractType | None = None
    clause_type: str | None = Field(default=None, min_length=1, max_length=40)
    content: str | None = Field(default=None, min_length=1)
    config_status: UserStatus | None = None

    @field_validator("name", "clause_type", "content", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return _trim(value)

    @field_validator("contract_type")
    @classmethod
    def known_contract_type(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTRACT_TYPES:
            raise ValueError("invalid contractType")
        return value

    @field_validator("config_status")
    @classmethod
    def known_status(cls, value: str | None) -> str | None:
        if value is not None and value not in USER_STATUSES:
            raise ValueError("invalid configStatus")
        return value

    @model_validator(mode="after")
    def has_change(self):
        if not self.model_fields_set:
            raise ValueError("one editable field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("editable fields cannot be null")
        return self


class RiskRuleCreateIn(Schema):
    rule_code: str = Field(min_length=1, max_length=40)
    risk_type: RiskType
    name: str = Field(min_length=1, max_length=100)
    risk_level: RiskLevel
    rule_content: str = Field(min_length=1)
    standard_clause_id: int | None = Field(default=None, gt=0)
    config_status: UserStatus = "active"
    warning_enabled: bool = False
    warning_due_hours: int | None = Field(default=None, gt=0)

    @field_validator("rule_code", "name", "rule_content", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return _trim(value)

    @field_validator("risk_type")
    @classmethod
    def known_risk_type(cls, value: str) -> str:
        if value not in RISK_TYPES:
            raise ValueError("invalid riskType")
        return value

    @field_validator("risk_level")
    @classmethod
    def known_level(cls, value: str) -> str:
        if value not in RISK_LEVELS:
            raise ValueError("invalid riskLevel")
        return value

    @field_validator("config_status")
    @classmethod
    def known_status(cls, value: str) -> str:
        if value not in USER_STATUSES:
            raise ValueError("invalid configStatus")
        return value


class RiskRuleUpdateIn(Schema):
    rule_code: str | None = Field(default=None, min_length=1, max_length=40)
    risk_type: RiskType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    risk_level: RiskLevel | None = None
    rule_content: str | None = Field(default=None, min_length=1)
    standard_clause_id: int | None = Field(default=None, gt=0)
    config_status: UserStatus | None = None
    warning_enabled: bool | None = None
    warning_due_hours: int | None = Field(default=None, gt=0)

    @field_validator("rule_code", "name", "rule_content", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return _trim(value)

    @field_validator("risk_type")
    @classmethod
    def known_risk_type(cls, value: str | None) -> str | None:
        if value is not None and value not in RISK_TYPES:
            raise ValueError("invalid riskType")
        return value

    @field_validator("risk_level")
    @classmethod
    def known_level(cls, value: str | None) -> str | None:
        if value is not None and value not in RISK_LEVELS:
            raise ValueError("invalid riskLevel")
        return value

    @field_validator("config_status")
    @classmethod
    def known_status(cls, value: str | None) -> str | None:
        if value is not None and value not in USER_STATUSES:
            raise ValueError("invalid configStatus")
        return value

    @model_validator(mode="after")
    def has_change(self):
        if not self.model_fields_set:
            raise ValueError("one editable field is required")
        required = self.model_fields_set - {"standard_clause_id", "warning_due_hours"}
        if any(getattr(self, field) is None for field in required):
            raise ValueError("editable fields cannot be null")
        return self
