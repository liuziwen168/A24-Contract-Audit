from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.api import Schema


class WarningCommentIn(Schema):
    comment: str | None = Field(default=None, max_length=5000)


class WarningActivateIn(WarningCommentIn):
    due_at: datetime | None = None


class WarningReopenIn(WarningCommentIn):
    due_at: datetime | None = None
