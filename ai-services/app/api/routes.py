"""API路由定义"""
import logging
import time
from fastapi import APIRouter, Depends

from app.api.dependencies import verify_internal_token, get_request_id
from app.core.config import settings
from app.core.exceptions import AIException
from app.schemas.request import (
    ClassifyRequest, ElementExtractRequest, RiskAnalyzeRequest,
    ClauseCompareRequest, FullReviewRequest, ParseRequest
)
from app.schemas.response import (
    ParseResponse, OCRResponse, ClassifyResponse,
    ElementExtractResponse, RiskAnalyzeResponse,
    ClauseCompareResponse, FullReviewResponse,
    APIResponse, ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/v1", tags=["AI Service"])


@router.post("/documents/parse", response_model=APIResponse)
async def parse_document(
    request: ParseRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """文档解析接口"""
    try:
        from app.parser.document_parser import DocumentParser
        parser = DocumentParser()
        result = parser.parse(
            file_path=request.file_path,
            file_type=request.file_type
        )
        return APIResponse(
            code="OK",
            message="success",
            data=ParseResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                file_sha256=request.file_sha256,
                text=result["text"],
                segments=result["segments"],
                warnings=result["warnings"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/documents/ocr", response_model=APIResponse)
async def ocr_document(
    request: ParseRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """OCR识别接口"""
    try:
        from app.parser.ocr_processor import OCRProcessor
        ocr = OCRProcessor()
        result = ocr.process(file_path=request.file_path)
        return APIResponse(
            code="OK",
            message="success",
            data=OCRResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                file_sha256=request.file_sha256,
                text=result["text"],
                segments=result["segments"],
                warnings=result["warnings"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/contracts/classify", response_model=APIResponse)
async def classify_contract(
    request: ClassifyRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """合同分类接口"""
    try:
        from app.pipeline.classifier import Classifier
        classifier = Classifier()
        result = await classifier.classify(
            text=request.text,
            contract_type=request.contract_type
        )
        return APIResponse(
            code="OK",
            message="success",
            data=ClassifyResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                contract_type=result["contract_type"],
                type_confidence=result["type_confidence"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/contracts/elements", response_model=APIResponse)
async def extract_elements(
    request: ElementExtractRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """要素抽取接口"""
    try:
        from app.pipeline.element_extractor import ElementExtractor
        extractor = ElementExtractor()
        result = await extractor.extract(
            text=request.text,
            contract_type=request.contract_type
        )
        return APIResponse(
            code="OK",
            message="success",
            data=ElementExtractResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                elements=result["elements"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/contracts/risks", response_model=APIResponse)
async def analyze_risks(
    request: RiskAnalyzeRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """风险审核接口"""
    try:
        from app.pipeline.risk_analyzer import RiskAnalyzer
        analyzer = RiskAnalyzer()
        risk_rules_dicts = [r.model_dump() for r in request.risk_rules] if request.risk_rules else []
        result = await analyzer.analyze(
            text=request.text,
            contract_type=request.contract_type,
            risk_rules=risk_rules_dicts
        )
        return APIResponse(
            code="OK",
            message="success",
            data=RiskAnalyzeResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                risks=result["risks"],
                overall_risk_level=result["overall_risk_level"],
                overall_score=result["overall_score"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/contracts/compare-clauses", response_model=APIResponse)
async def compare_clauses(
    request: ClauseCompareRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """标准条款比对接口"""
    try:
        from app.pipeline.clause_comparator import ClauseComparator
        comparator = ClauseComparator()
        clauses_dicts = [c.model_dump() for c in request.standard_clauses] if request.standard_clauses else []
        result = await comparator.compare(
            text=request.text,
            standard_clauses=clauses_dicts
        )
        return APIResponse(
            code="OK",
            message="success",
            data=ClauseCompareResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_file_id=request.contract_file_id,
                missing_clauses=result["missing_clauses"],
                deviations=result["deviations"]
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )


@router.post("/reviews/full", response_model=APIResponse)
async def full_review(
    request: FullReviewRequest,
    x_internal_token: str = Depends(verify_internal_token),
    x_request_id: str = Depends(get_request_id)
):
    """完整审核接口"""
    start_time = time.time()

    try:
        from app.parser.document_parser import DocumentParser
        from app.pipeline.classifier import Classifier
        from app.pipeline.element_extractor import ElementExtractor
        from app.pipeline.risk_analyzer import RiskAnalyzer
        from app.pipeline.clause_comparator import ClauseComparator

        # 1. 文档解析
        parser = DocumentParser()
        parse_result = parser.parse(
            file_path=request.file_path,
            file_type=request.file_type
        )
        text = parse_result["text"]
        warnings = parse_result["warnings"]

        # 2. 合同分类
        classifier = Classifier()
        classify_result = await classifier.classify(text=text)
        contract_type = classify_result["contract_type"]
        type_confidence = classify_result["type_confidence"]

        # 3. 要素抽取
        extractor = ElementExtractor()
        elements_result = await extractor.extract(
            text=text,
            contract_type=contract_type
        )
        elements = elements_result["elements"]

        # 4. 风险审核
        analyzer = RiskAnalyzer()
        risk_rules_dicts = [r.model_dump() for r in request.risk_rules] if request.risk_rules else []
        risks_result = await analyzer.analyze(
            text=text,
            contract_type=contract_type,
            risk_rules=risk_rules_dicts
        )

        # 5. 标准条款比对
        comparator = ClauseComparator()
        clauses_dicts = [c.model_dump() for c in request.standard_clauses] if request.standard_clauses else []
        compare_result = await comparator.compare(
            text=text,
            standard_clauses=clauses_dicts
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return APIResponse(
            code="OK",
            message="success",
            data=FullReviewResponse(
                request_id=x_request_id,
                contract_id=request.contract_id,
                contract_type=contract_type,
                type_confidence=type_confidence,
                elements=elements,
                risks=risks_result["risks"],
                missing_clauses=compare_result["missing_clauses"],
                overall_risk_level=risks_result["overall_risk_level"],
                overall_score=risks_result["overall_score"],
                model_name=settings.QWEN_MODEL,
                model_version=settings.QWEN_MODEL,
                prompt_version=settings.PROMPT_VERSION,
                processing_time_ms=processing_time_ms,
                warnings=warnings,
                error=None
            ).model_dump()
        )
    except AIException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=ErrorResponse(
                code=e.code,
                message=e.message,
                detail=e.detail
            ).model_dump()
        )
