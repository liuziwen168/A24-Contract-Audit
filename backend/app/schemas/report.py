from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.api import Schema


class ReportCreateIn(Schema):
    report_format: str = Field(
        min_length=1, max_length=10, json_schema_extra={"enum": ["html", "pdf"]}
    )

    @field_validator("report_format", mode="before")
    @classmethod
    def trim_format(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value
