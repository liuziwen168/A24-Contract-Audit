from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(default="user")
    content: str = Field(...)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] | None = None