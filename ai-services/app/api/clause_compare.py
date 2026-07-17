# app/api/clause_compare.py
"""
标准条款比对接口
将合同内容与企业标准条款库比对，发现偏离条款和缺失条款
"""

import json
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.schemas.response import BaseResponse, ClauseCompareData, ClauseDeviation
from app.prompts.clause_compare_prompt import CLAUSE_COMPARE_PROMPT, DEFAULT_STANDARD_CLAUSES
from app.services.qwen_service import chat
from app.utils.json_cleaner import clean_json
from app.utils.exceptions import AIException, JSONParseException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["标准条款比对"])


class ClauseCompareRequest(BaseModel):
    """标准条款比对请求"""
    text: str = Field(..., description="合同文本", min_length=1)
    standardClauses: Optional[str] = Field(
        default=None,
        description="自定义标准条款库（不传则使用系统默认）"
    )


@router.post(
    "/clause-compare",
    response_model=BaseResponse[ClauseCompareData],
    summary="标准条款比对",
    description="""
将合同内容与标准条款库进行比对，发现三类问题：

- **missing**: 合同缺失的标准条款
- **deviation**: 合同中有但偏离标准的条款
- **matched**: 与标准条款匹配的合同条款

支持使用系统默认标准条款库或自定义条款库。
    """
)
async def clause_compare(request: ClauseCompareRequest):
    """
    标准条款比对接口

    参数：
        text: 合同全文
        standardClauses: 自定义标准条款（可选，默认使用内置13类标准条款）

    返回：
        偏离条款列表、缺失条款清单、匹配统计
    """
    start_time = time.time()

    try:
        # 使用自定义标准条款或系统默认
        standard_clauses = request.standardClauses or DEFAULT_STANDARD_CLAUSES

        logger.info(
            f"收到标准条款比对请求 - 文本长度: {len(request.text)}, "
            f"使用{'自定义' if request.standardClauses else '默认'}标准条款库"
        )

        # 构造 Prompt
        prompt = CLAUSE_COMPARE_PROMPT.format(
            text=request.text,
            standard_clauses=standard_clauses
        )

        # 调用 AI
        result = chat(prompt)
        cleaned = clean_json(result)

        if not cleaned:
            raise AIException("AI返回内容为空")

        data = json.loads(cleaned)

        # 解析偏离列表
        deviations = []
        missing_clauses = []

        for item in data.get("deviations", []):
            dev = ClauseDeviation(
                clauseName=item.get("clauseName", ""),
                standardContent=item.get("standardContent", ""),
                actualContent=item.get("actualContent", ""),
                deviationType=item.get("deviationType", "deviation"),
                severity=item.get("severity", "中"),
                suggestion=item.get("suggestion", "")
            )
            deviations.append(dev)

            if dev.deviationType == "missing":
                missing_clauses.append(dev.clauseName)

        elapsed = time.time() - start_time

        logger.info(
            f"标准条款比对完成 - 耗时: {elapsed:.2f}s, "
            f"偏离: {len(deviations)}, 缺失: {len(missing_clauses)}, "
            f"匹配: {data.get('matchedCount', 0)}"
        )

        return BaseResponse(
            code=0,
            message="success",
            data=ClauseCompareData(
                deviations=deviations,
                missingClauses=missing_clauses,
                matchedCount=data.get("matchedCount", 0),
                totalStandardClauses=data.get("totalStandardClauses", len(deviations))
            )
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        raise JSONParseException(
            message=f"AI返回JSON解析失败: {str(e)}",
            raw_content=result if 'result' in locals() else None
        )
    except AIException:
        raise
    except Exception as e:
        logger.exception("标准条款比对失败")
        raise AIException(message=f"标准条款比对失败: {str(e)}")

