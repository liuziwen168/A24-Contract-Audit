"""响应模型定义"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    code: str = Field(..., description="响应码")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    detail: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class ParseResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    file_sha256: str
    text: str
    segments: List[Dict[str, Any]]
    warnings: List[str]


class OCRResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    file_sha256: str
    text: str
    segments: List[Dict[str, Any]]
    warnings: List[str]


class ClassifyResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    contract_type: str
    type_confidence: float


class ElementExtractResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    elements: List[Dict[str, Any]]


class RiskAnalyzeResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    risks: List[Dict[str, Any]]
    overall_risk_level: str
    overall_score: float


class ClauseCompareResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_file_id: int
    missing_clauses: List[str]
    deviations: List[Dict[str, Any]]


class FullReviewResponse(BaseModel):
    request_id: str
    contract_id: int
    contract_type: str
    type_confidence: float
    elements: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    missing_clauses: List[str]
    overall_risk_level: str
    overall_score: float
    model_name: str
    model_version: str
    model_config = {
        "protected_namespaces": ()  
    }
    prompt_version: str
    processing_time_ms: int
    warnings: List[str]
    error: Optional[Dict[str, Any]] = None
