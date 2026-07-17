# app/api/parse.py
"""
文档解析接口
支持 DOCX/PDF/图片上传并返回结构化解析结果
"""

import logging
import time
import os

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.schemas.response import BaseResponse, ParseData, ParagraphData
from app.services.document_parser import parse_document_bytes, ParseResult
from app.utils.exceptions import AIException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["文档解析"])

# 允许的文件格式
ALLOWED_EXTENSIONS = {'.docx', '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post(
    "/parse",
    response_model=BaseResponse[ParseData],
    summary="文档解析",
    description="上传合同文档（DOCX/PDF/图片/TXT），返回结构化解析结果，包含全文、段落索引和页码信息"
)
async def parse_document(
    file: UploadFile = File(..., description="合同文档文件"),
    use_ocr: bool = Form(True, description="是否使用OCR识别图片文本")
):
    """
    文档解析接口

    支持格式：
    - DOCX: Word文档
    - PDF: PDF文档（含扫描件OCR支持）
    - 图片: PNG/JPG/BMP/TIFF（OCR文字识别）
    - TXT: 纯文本

    返回：
    - 完整合同文本
    - 段落列表（含索引和页码）
    - 页数、格式类型
    - 解析告警信息
    """
    start_time = time.time()

    # 1. 校验文件扩展名
    original_filename = file.filename or "unknown"
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. 读取文件内容
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"文件读取失败: {e}")
        raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")

    # 3. 校验文件大小
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件为空")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大（{len(content)} bytes），最大允许 {MAX_FILE_SIZE} bytes"
        )

    logger.info(
        f"收到文档解析请求 - 文件名: {original_filename}, "
        f"大小: {len(content)} bytes, 格式: {ext}, OCR: {use_ocr}"
    )

    # 4. 调用解析服务
    try:
        result: ParseResult = parse_document_bytes(
            content=content,
            filename=original_filename,
            use_ocr=use_ocr
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"缺少解析依赖: {str(e)}"
        )
    except Exception as e:
        logger.exception("文档解析失败")
        raise AIException(message=f"文档解析失败: {str(e)}")

    # 5. 构建响应
    elapsed = time.time() - start_time

    paragraph_list = [
        ParagraphData(
            index=p.index,
            text=p.text,
            page=p.page
        )
        for p in result.paragraphs
    ]

    logger.info(
        f"文档解析完成 - 耗时: {elapsed:.2f}s, "
        f"格式: {result.format_type}, "
        f"页数: {result.page_count}, "
        f"段落数: {len(paragraph_list)}, "
        f"字符数: {len(result.full_text)}, "
        f"告警: {len(result.warnings)}"
    )

    return BaseResponse(
        code=0,
        message="success",
        data=ParseData(
            fullText=result.full_text,
            paragraphs=paragraph_list,
            pageCount=result.page_count,
            formatType=result.format_type,
            warnings=result.warnings,
            metadata=result.metadata
        )
    )


@router.post(
    "/parse/text",
    response_model=BaseResponse[ParseData],
    summary="文本解析（兼容旧接口）",
    description="直接提交合同文本，返回结构化的解析结果"
)
async def parse_text(request: dict):
    """
    文本解析接口（兼容纯文本提交）
    """
    start_time = time.time()

    text = request.get("text", "")
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="文本内容为空")

    # 简单段落分割
    raw_paragraphs = text.split('\n\n')
    paragraphs = []
    for i, para in enumerate(raw_paragraphs, start=1):
        para = para.strip()
        if para:
            paragraphs.append(ParagraphData(
                index=i,
                text=para,
                page=None
            ))

    elapsed = time.time() - start_time

    return BaseResponse(
        code=0,
        message="success",
        data=ParseData(
            fullText=text,
            paragraphs=paragraphs,
            pageCount=1,
            formatType="text",
            warnings=[],
            metadata={"paragraph_count": len(paragraphs)}
        )
    )
