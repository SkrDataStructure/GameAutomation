from __future__ import annotations

from abc import ABC, abstractmethod


class Task(ABC):
    """所有游戏任务的统一接口。"""

    name = "unnamed"

    @abstractmethod
    def run(self) -> bool:
        """成功返回 True，业务未完成返回 False；异常由 Scheduler 隔离。"""
        raise NotImplementedError
