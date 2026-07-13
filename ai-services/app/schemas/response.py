from typing import Generic, Optional, TypeVar, List

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class BaseResponse(GenericModel, Generic[T]):
    """
    所有接口统一返回格式
    """

    code: int = Field(default=0, description="状态码，0表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="返回数据")


# =========================
# classify
# =========================

class ContractTypeData(BaseModel):
    contractType: str
    confidence: Optional[float] = None


# =========================
# extract
# =========================

class ExtractData(BaseModel):
    partyA: str = ""
    partyB: str = ""
    amount: str = ""
    signDate: str = ""
    contractPeriod: str = ""


# =========================
# risk
# =========================

class RiskItem(BaseModel):
    riskType: str
    riskLevel: str
    description: str
    suggestion: str


class RiskData(BaseModel):
    riskList: List[RiskItem]


# =========================
# review
# =========================

class ReviewRiskItem(BaseModel):
    type: str
    level: str
    content: str
    basis: str
    suggestion: str


class FullReviewData(BaseModel):
    contractType: str
    partyA: str
    partyB: str
    amount: str
    signDate: str
    contractPeriod: str

    riskLevel: str
    riskScore: int

    risks: List[ReviewRiskItem]