from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path

from sqlalchemy import or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.reports import (
    build_report_context,
    render_report,
    write_report_file,
)
from app.core.config import settings
from app.core.errors import AppError
from app.infrastructure.db import SessionLocal
from app.models.entities import Report, utcnow

SAFE_MESSAGES = {
    "REPORT_NOT_READY": "审核结果尚不满足报告生成条件",
    "REPORT_FORMAT_UNSUPPORTED": "报告格式不受支持",
    "REPORT_GENERATION_FAILED": "报告生成失败",
    "DATABASE_ERROR": "报告状态保存失败",
}


class ReportExecutor:
    def __init__(
        self,
        session_factory: sessionmaker[Session] = SessionLocal,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.session_factory = session_factory
        self.sleep = sleep
        self._stopped = False

    async def run_forever(self) -> None:
        while not self._stopped:
            handled = await self.run_once()
            if not handled:
                await self.sleep(settings.report_task_poll_seconds)

    def stop(self) -> None:
        self._stopped = True

    def _claim_one(self) -> int | None:
        db = self.session_factory()
        try:
            now = utcnow()
            candidate = db.scalar(
                select(Report.id)
                .where(
                    Report.status == "pending",
                    Report.attempt_count < settings.report_max_attempts,
                )
                .order_by(Report.created_at, Report.id)
                .limit(1)
            )
            recovering = False
            if candidate is None:
                stale_before = now - timedelta(seconds=settings.report_task_stale_seconds)
                candidate = db.scalar(
                    select(Report.id)
                    .where(
                        Report.status == "generating",
                        Report.attempt_count < settings.report_max_attempts,
                        or_(Report.started_at.is_(None), Report.started_at < stale_before),
                    )
                    .order_by(Report.started_at, Report.id)
                    .limit(1)
                )
                recovering = candidate is not None
            if candidate is None:
                return None
            conditions = [
                Report.id == candidate,
                Report.status == ("generating" if recovering else "pending"),
                Report.attempt_count < settings.report_max_attempts,
            ]
            if recovering:
                conditions.append(
                    or_(
                        Report.started_at.is_(None),
                        Report.started_at
                        < now - timedelta(seconds=settings.report_task_stale_seconds),
                    )
                )
            claimed = db.execute(
                update(Report)
                .where(*conditions)
                .values(
                    status="generating",
                    started_at=now,
                    attempt_count=Report.attempt_count + 1,
                    error_code=None,
                    error_message=None,
                )
            )
            db.commit()
            return candidate if claimed.rowcount == 1 else None
        except SQLAlchemyError:
            db.rollback()
            return None
        finally:
            db.close()

    async def run_once(self) -> bool:
        report_id = await asyncio.to_thread(self._claim_one)
        if report_id is None:
            return False
        await asyncio.to_thread(self._process, report_id)
        return True

    def _process(self, report_id: int) -> None:
        published: Path | None = None
        try:
            db = self.session_factory()
            try:
                report = db.get(Report, report_id)
                if report is None or report.status != "generating":
                    return
                context = build_report_context(db, report)
                content = render_report(context, report.format)
                relative, published, size, digest = write_report_file(report, content)
            finally:
                db.close()
            self._complete(report_id, relative, published, size, digest)
            published = None
        except AppError as error:
            self._mark_failed(report_id, error.code)
        except SQLAlchemyError:
            self._mark_failed(report_id, "DATABASE_ERROR")
        except Exception:
            self._mark_failed(report_id, "REPORT_GENERATION_FAILED")
        finally:
            if published is not None:
                published.unlink(missing_ok=True)

    def _complete(
        self, report_id: int, relative: str, path: Path, size: int, digest: str
    ) -> None:
        db = self.session_factory()
        try:
            report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
            if report is None or report.status != "generating":
                path.unlink(missing_ok=True)
                return
            report.status = "completed"
            report.storage_path = relative
            report.file_size = size
            report.sha256 = digest
            report.generated_at = utcnow()
            report.error_code = None
            report.error_message = None
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            path.unlink(missing_ok=True)
            raise
        finally:
            db.close()

    def _mark_failed(self, report_id: int, code: str) -> None:
        db = self.session_factory()
        try:
            report = db.scalar(select(Report).where(Report.id == report_id).with_for_update())
            if report is not None and report.status == "generating":
                report.status = "failed"
                report.storage_path = None
                report.file_size = None
                report.sha256 = None
                report.generated_at = None
                report.error_code = code if code in SAFE_MESSAGES else "REPORT_GENERATION_FAILED"
                report.error_message = SAFE_MESSAGES[report.error_code]
                db.commit()
        except SQLAlchemyError:
            db.rollback()
        finally:
            db.close()
