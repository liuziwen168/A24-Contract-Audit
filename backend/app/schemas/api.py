from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from app.domain import REVIEW_MODES


def camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(item.title() for item in tail)


class Schema(BaseModel):
    model_config = ConfigDict(alias_generator=camel, populate_by_name=True)


class LoginIn(Schema):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def non_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value or len(value) > (64 if info.field_name == "username" else 256):
            raise ValueError("invalid credential")
        return value


class ReviewIn(Schema):
    contract_id: int
    contract_file_id: int
    review_mode: Literal["full", "rulesOnly"]
    source_warning_id: int | None = None

    @field_validator("review_mode")
    @classmethod
    def known_mode(cls, value: str) -> str:
        if value not in REVIEW_MODES:
            raise ValueError("unsupported reviewMode")
        return value

    @field_validator("contract_id", "contract_file_id", "source_warning_id")
    @classmethod
    def positive_id(cls, value: int) -> int:
        if value is not None and value <= 0:
            raise ValueError("identifier must be positive")
        return value
