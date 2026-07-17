from typing import Generic, Optional, TypeVar, List, Dict, Any

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
# parse
# =========================

class ParagraphData(BaseModel):
    index: int = Field(description="段落序号（从1开始）")
    text: str = Field(description="段落文本")
    page: Optional[int] = Field(default=None, description="所在页码")


class ParseData(BaseModel):
    fullText: str = Field(description="完整合同文本")
    paragraphs: List[ParagraphData] = Field(default_factory=list, description="段落列表")
    pageCount: int = Field(default=0, description="总页数")
    formatType: str = Field(default="", description="原始格式类型")
    warnings: List[str] = Field(default_factory=list, description="解析告警信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# =========================
# classify
# =========================

class ContractTypeData(BaseModel):
    contractType: str = Field(description="合同类型")
    confidence: Optional[float] = Field(default=None, description="分类置信度(0~1)")


# =========================
# extract
# =========================

class ExtractItem(BaseModel):
    """单个要素项（含置信度和位置）"""
    value: str = Field(default="", description="要素值")
    confidence: Optional[float] = Field(default=None, description="置信度(0~1)")
    position: Optional[str] = Field(default=None, description="原文位置（段落索引或页码范围）")
    originalText: Optional[str] = Field(default=None, description="原文片段")


class ExtractData(BaseModel):
    partyA: ExtractItem = Field(default_factory=ExtractItem, description="甲方")
    partyB: ExtractItem = Field(default_factory=ExtractItem, description="乙方")
    amount: ExtractItem = Field(default_factory=ExtractItem, description="合同金额")
    signDate: ExtractItem = Field(default_factory=ExtractItem, description="签订日期")
    contractPeriod: ExtractItem = Field(default_factory=ExtractItem, description="合同期限")
    disputeResolution: ExtractItem = Field(default_factory=ExtractItem, description="争议解决方式")


# =========================
# risk
# =========================

class RiskItem(BaseModel):
    riskType: str = Field(description="风险类型")
    riskLevel: str = Field(description="风险等级：高/中/低")
    description: str = Field(description="风险描述")
    suggestion: str = Field(description="修改建议")
    originalText: Optional[str] = Field(default=None, description="风险涉及原文片段")
    position: Optional[str] = Field(default=None, description="原文位置（段落索引或页码范围）")
    basis: Optional[str] = Field(default=None, description="判断依据（法律法规或标准条款引用）")


class RiskData(BaseModel):
    riskLevel: Optional[str] = Field(default=None, description="总体风险等级")
    riskScore: Optional[int] = Field(default=None, description="风险评分(0~100)")
    riskList: List[RiskItem] = Field(default_factory=list, description="风险列表")


# =========================
# clause comparison
# =========================

class ClauseDeviation(BaseModel):
    """条款偏离"""
    clauseName: str = Field(description="条款名称")
    standardContent: str = Field(description="标准条款内容")
    actualContent: str = Field(default="", description="实际合同中的对应内容")
    deviationType: str = Field(description="偏离类型: missing(缺失)/deviation(偏离)/matched(匹配)")
    severity: str = Field(default="中", description="严重程度: 高/中/低")
    suggestion: str = Field(default="", description="修改建议")
    position: Optional[str] = Field(default=None, description="实际条款位置")


class ClauseCompareData(BaseModel):
    deviations: List[ClauseDeviation] = Field(default_factory=list, description="偏离条款列表")
    missingClauses: List[str] = Field(default_factory=list, description="缺失条款名称列表")
    matchedCount: int = Field(default=0, description="匹配条款数量")
    totalStandardClauses: int = Field(default=0, description="标准条款总数")


# =========================
# review
# =========================

class ReviewRiskItem(BaseModel):
    type: str = Field(description="风险类型")
    level: str = Field(description="风险等级")
    content: str = Field(description="风险描述")
    basis: str = Field(default="", description="风险依据")
    suggestion: str = Field(description="修改建议")
    originalText: Optional[str] = Field(default=None, description="风险涉及原文")
    position: Optional[str] = Field(default=None, description="原文位置")


class ReviewElementItem(BaseModel):
    value: str = Field(default="", description="要素值")
    confidence: Optional[float] = Field(default=None, description="置信度")
    position: Optional[str] = Field(default=None, description="原文位置")


class FullReviewData(BaseModel):
    contractType: str = Field(description="合同类型")
    contractTypeConfidence: Optional[float] = Field(default=None, description="分类置信度")

    partyA: ReviewElementItem = Field(default_factory=ReviewElementItem, description="甲方")
    partyB: ReviewElementItem = Field(default_factory=ReviewElementItem, description="乙方")
    amount: ReviewElementItem = Field(default_factory=ReviewElementItem, description="合同金额")
    signDate: ReviewElementItem = Field(default_factory=ReviewElementItem, description="签订日期")
    contractPeriod: ReviewElementItem = Field(default_factory=ReviewElementItem, description="合同期限")
    disputeResolution: ReviewElementItem = Field(default_factory=ReviewElementItem, description="争议解决方式")

    riskLevel: str = Field(default="", description="总体风险等级")
    riskScore: int = Field(default=0, description="风险评分(0~100)")
    risks: List[ReviewRiskItem] = Field(default_factory=list, description="风险列表")

    missingClauses: List[str] = Field(default_factory=list, description="缺失条款")
    parseWarnings: List[str] = Field(default_factory=list, description="解析告警")

    snapshotVersion: str = Field(default="1.0", description="AI初审快照版本号")
    snapshotCreatedAt: Optional[str] = Field(default=None, description="快照创建时间")