"""请求模型定义"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _to_camel(name: str) -> str:
    """snake_case → camelCase"""
    head, *tail = name.split("_")
    return head + "".join(w.title() for w in tail)


class BaseRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    request_id: str = Field(..., description="请求追踪ID")
    contract_id: int = Field(..., description="合同ID")
    contract_file_id: int = Field(..., description="合同文件ID")
    file_sha256: str = Field(..., description="文件SHA256摘要")


class ParseRequest(BaseRequest):
    file_path: str = Field(..., description="文件路径")
    file_type: str = Field(..., description="文件类型: docx, pdf, image")


class ClassifyRequest(BaseRequest):
    text: str = Field(..., description="合同文本")
    contract_type: Optional[str] = Field(None, description="已有合同类型")


class ElementExtractRequest(BaseRequest):
    text: str = Field(..., description="合同文本")
    contract_type: str = Field(..., description="合同类型")


class RiskRule(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: int = Field(..., alias="ruleId", description="规则ID")
    rule_code: str = Field(..., description="规则编码")
    risk_type: str = Field(..., description="风险类型")
    name: str = Field(..., description="规则名称")
    risk_level: str = Field(..., description="建议风险等级")
    rule_content: str = Field(..., description="规则内容")
    standard_clause_id: Optional[int] = Field(None, description="关联标准条款ID")
    warning_enabled: bool = Field(False, description="是否启用预警")
    warning_due_hours: Optional[int] = Field(None, description="建议整改时限")
    version: str = Field("v0.1", description="规则版本")


class RiskAnalyzeRequest(BaseRequest):
    text: str = Field(..., description="合同文本")
    contract_type: str = Field(..., description="合同类型")
    risk_rules: List[RiskRule] = Field(default_factory=list, description="风险规则列表")


class StandardClause(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: int = Field(..., alias="clauseId", description="条款ID")
    name: str = Field(..., description="条款名称")
    contract_type: str = Field(..., description="适用合同类型")
    clause_type: str = Field(..., description="条款类别")
    content: str = Field(..., description="条款内容")
    version: str = Field("v0.1", description="条款版本")
    warning_enabled: bool = Field(False, description="是否启用预警")
    warning_due_hours: Optional[int] = Field(None, description="建议整改时限")


class ClauseCompareRequest(BaseRequest):
    text: str = Field(..., description="合同文本")
    standard_clauses: List[StandardClause] = Field([], description="标准条款列表")


class FullReviewRequest(BaseRequest):
    file_path: str = Field(..., description="文件路径")
    file_type: str = Field(..., description="文件类型")
    standard_clauses: List[StandardClause] = Field(default_factory=list, description="标准条款列表")
    risk_rules: List[RiskRule] = Field(default_factory=list, description="风险规则列表")
