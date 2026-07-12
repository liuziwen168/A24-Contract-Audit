from pydantic import BaseModel


class ClassifyResponse(BaseModel):
    contractType: str
    confidence: float