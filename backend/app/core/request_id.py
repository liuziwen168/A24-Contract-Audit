from contextvars import ContextVar
from uuid import uuid4

request_id: ContextVar[str] = ContextVar("request_id", default="")
client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)


def new_request_id() -> str:
    return f"req_{uuid4().hex}"
