from __future__ import annotations

import hashlib
import os
import tempfile
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path, PurePosixPath, PureWindowsPath
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.manual_review import effective
from app.core.config import settings
from app.core.errors import fail
from app.models.entities import Contract, Report, ReviewRecord, User, utcnow

MISSING = "未识别"
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates"
FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansSC-VF.ttf"
HTML_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_ROOT),
    autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=True),
)


def decimal_text(value: object) -> str:
    if value in (None, ""):
        return MISSING
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    return format(number, "f")


def display(value: object) -> str:
    if value is None or value == "":
        return MISSING
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _reviewers(db: Session, review: ReviewRecord) -> dict[int, str]:
    ids = {value for value in (review.legal_reviewer_id, review.risk_reviewer_id) if value}
    if not ids:
        return {}
    return {row.id: row.username for row in db.scalars(select(User).where(User.id.in_(ids)))}


def build_report_context(
    db: Session, report: Report, generated_at: datetime | None = None
) -> dict[str, object]:
    review = db.get(ReviewRecord, report.review_id)
    if review is None:
        raise fail("REPORT_NOT_FOUND")
    contract = db.get(Contract, review.contract_id)
    if (
        contract is None
        or contract.deleted_at is not None
        or review.status != "completed"
        or review.review_stage != "completed"
        or review.ai_result_json is None
        or review.legal_reviewer_id is None
        or review.risk_reviewer_id is None
        or review.legal_reviewed_at is None
        or review.risk_reviewed_at is None
    ):
        raise fail("REPORT_NOT_READY")
    current = effective(db, review)
    elements = {item.get("elementType"): item.get("value") for item in current.get("elements", [])}
    all_risks = list(current.get("risks", []))
    risks = [item for item in all_risks if item.get("riskStatus", "active") != "dismissed"]
    counts = Counter(item.get("riskLevel") for item in risks)
    reviewers = _reviewers(db, review)
    generated_at = generated_at or utcnow()
    normalized_risks = [
        {
            **item,
            "riskType": display(item.get("riskType")),
            "riskName": display(item.get("riskName")),
            "riskLevel": display(item.get("riskLevel")),
            "clauseText": display(item.get("clauseText")),
            "page": display(item.get("page")),
            "paragraphIndex": display(item.get("paragraphIndex")),
            "basis": display(item.get("basis")),
            "suggestion": display(item.get("suggestion")),
        }
        for item in risks
    ]
    return {
        "reportTitle": "企业合同智能审核报告",
        "reportNumber": f"A24-RPT-{report.id:08d}",
        "generatedAt": generated_at.isoformat(),
        "contract": {
            "contractId": contract.id,
            "name": display(contract.name),
            "contractType": display(current.get("contractType")),
            "partyA": display(elements.get("partyA")),
            "partyB": display(elements.get("partyB")),
            "signingDate": display(elements.get("signingDate")),
            "contractAmount": decimal_text(elements.get("contractAmount")),
            "performanceTerm": display(elements.get("performanceTerm")),
            "disputeResolution": display(elements.get("disputeResolution")),
        },
        "review": {
            "reviewId": review.id,
            "reviewStatus": review.status,
            "reviewStage": review.review_stage,
            "legalReviewer": display(reviewers.get(review.legal_reviewer_id)),
            "legalReviewedAt": display(review.legal_reviewed_at),
            "riskReviewer": display(reviewers.get(review.risk_reviewer_id)),
            "riskReviewedAt": display(review.risk_reviewed_at),
            "overallRiskLevel": display(current.get("overallRiskLevel")),
            "overallScore": decimal_text(current.get("overallScore")),
        },
        "riskSummary": {
            "total": len(risks),
            "high": counts.get("high", 0),
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "dismissed": len(all_risks) - len(risks),
        },
        "risks": normalized_risks,
        "missingClauses": [display(item) for item in current.get("missingClauses", [])],
        "deviations": current.get("deviations") or [],
        "reviewNote": "本报告以不可变AI初审快照为基础，并按时间和ID顺序应用全部法务、风控人工修订。",
    }


def render_html(context: dict[str, object]) -> bytes:
    return HTML_ENV.get_template("report.html").render(**context).encode("utf-8")


def _p(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(display(value)).replace("\n", "<br/>"), style)


def render_pdf(context: dict[str, object]) -> bytes:
    if "NotoSansSC" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("NotoSansSC", FONT_PATH))
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "CJKBody", parent=styles["BodyText"], fontName="NotoSansSC", fontSize=9, leading=14
    )
    title = ParagraphStyle(
        "CJKTitle",
        parent=styles["Title"],
        fontName="NotoSansSC",
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365d"),
    )
    heading = ParagraphStyle(
        "CJKHeading",
        parent=styles["Heading2"],
        fontName="NotoSansSC",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#17365d"),
        spaceBefore=10,
        spaceAfter=6,
    )
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=str(context["reportTitle"]),
    )
    contract = context["contract"]
    review = context["review"]
    summary = context["riskSummary"]
    story = [
        _p(context["reportTitle"], title),
        _p(f"报告编号：{context['reportNumber']}　生成时间：{context['generatedAt']}", body),
        Spacer(1, 6),
        _p("合同与审核概览", heading),
    ]
    overview = [
        ["合同名称", contract["name"], "合同类型", contract["contractType"]],
        ["甲方", contract["partyA"], "乙方", contract["partyB"]],
        ["签署日期", contract["signingDate"], "合同金额", contract["contractAmount"]],
        ["履行期限", contract["performanceTerm"], "争议解决", contract["disputeResolution"]],
        ["审核状态", f"{review['reviewStatus']}/{review['reviewStage']}", "总体风险", f"{review['overallRiskLevel']} / {review['overallScore']}"],
        ["法务复核", f"{review['legalReviewer']} · {review['legalReviewedAt']}", "风控复核", f"{review['riskReviewer']} · {review['riskReviewedAt']}"],
    ]
    table = Table(
        [[_p(cell, body) for cell in row] for row in overview],
        colWidths=[24 * mm, 58 * mm, 24 * mm, 58 * mm],
        repeatRows=0,
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cdd6e1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f6fa")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f3f6fa")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            _p("当前有效风险", heading),
            _p(
                f"共 {summary['total']} 项：高 {summary['high']}、中 {summary['medium']}、低 {summary['low']}。已忽略 {summary['dismissed']} 项，不计入当前有效风险。",
                body,
            ),
        ]
    )
    for index, risk in enumerate(context["risks"], 1):
        story.extend(
            [
                _p(f"{index}. {risk['riskName']}（{risk['riskLevel']}）", heading),
                _p(f"风险类型：{risk['riskType']}", body),
                _p(f"风险条款：{risk['clauseText']}", body),
                _p(f"原文位置：第 {risk['page']} 页 / 段落 {risk['paragraphIndex']}", body),
                _p(f"风险依据：{risk['basis']}", body),
                _p(f"修改建议：{risk['suggestion']}", body),
                Spacer(1, 4),
            ]
        )
    story.append(
        KeepTogether(
            [
            _p("标准条款比对", heading),
            _p(
                "缺失条款："
                + ("、".join(context["missingClauses"]) if context["missingClauses"] else "无"),
                body,
            ),
            _p("审核说明", heading),
            _p(context["reviewNote"], body),
            _p(
                "免责声明：本报告由智能审核与人工复核结果汇总生成，仅供企业内部风险识别与决策参考，不构成正式法律意见。",
                body,
            ),
            ]
        )
    )

    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("NotoSansSC", 8)
        canvas.setFillColor(colors.HexColor("#687385"))
        canvas.drawString(16 * mm, 10 * mm, str(context["reportNumber"]))
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"第 {doc.page} 页")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def render_report(context: dict[str, object], report_format: str) -> bytes:
    if report_format == "html":
        return render_html(context)
    if report_format == "pdf":
        return render_pdf(context)
    raise fail("REPORT_FORMAT_UNSUPPORTED")


def report_path(relative: str) -> Path:
    if (
        not relative
        or PurePosixPath(relative).is_absolute()
        or PureWindowsPath(relative).is_absolute()
    ):
        raise fail("REPORT_FILE_NOT_FOUND")
    root = settings.report_root.resolve()
    path = (root / relative).resolve()
    if root not in path.parents:
        raise fail("REPORT_FILE_NOT_FOUND")
    return path


def write_report_file(report: Report, content: bytes) -> tuple[str, Path, int, str]:
    root = settings.report_root.resolve()
    directory = root / str(report.id // 1000)
    directory.mkdir(parents=True, exist_ok=True)
    relative = f"{report.id // 1000}/{report.id}_{os.urandom(8).hex()}.{report.format}"
    target = report_path(relative)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix=".report-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        temporary = None
        return relative, target, len(content), hashlib.sha256(content).hexdigest()
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def safe_download_name(contract_name: str, report_format: str) -> str:
    unsafe = '\r\n"/\\'
    cleaned = "".join("_" if char in unsafe or ord(char) < 32 else char for char in contract_name)
    return f"{cleaned.strip()[:120] or 'contract'}_审核报告.{report_format}"
