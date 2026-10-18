from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

from core.task import Task

logger = logging.getLogger(__name__)


@dataclass
class TaskReport:
    name: str
    success: bool
    duration_seconds: float
    error: str | None = None


class Scheduler:
    """串行调度任务；逐任务捕获异常，保证失败不阻断后续任务。"""

    def run_all(self, tasks: Iterable[Task]) -> list[TaskReport]:
        reports: list[TaskReport] = []
        for task in tasks:
            started = time.monotonic()
            try:
                result = bool(task.run())
                report = TaskReport(
                    name=task.name,
                    success=result,
                    duration_seconds=time.monotonic() - started,
                )
                logger.info(
                    "任务结束 name=%s success=%s duration=%.2fs",
                    report.name, report.success, report.duration_seconds,
                )
            except Exception as exc:
                report = TaskReport(
                    name=getattr(task, "name", task.__class__.__name__),
                    success=False,
                    duration_seconds=time.monotonic() - started,
                    error=f"{type(exc).__name__}: {exc}",
                )
                logger.exception("任务异常，继续执行后续任务：%s", report.name)
            reports.append(report)
        return reports
