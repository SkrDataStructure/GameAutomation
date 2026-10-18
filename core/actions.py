from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np

from core.device import DeviceManager
from core.matcher import MatchResult, TemplateMatcher

logger = logging.getLogger(__name__)


class Actions:
    """供业务任务调用的原子动作封装。"""

    def __init__(
        self,
        device: DeviceManager,
        matcher: TemplateMatcher,
        dry_run: bool = False,
        poll_interval: float = 0.25,
    ):
        self.device = device
        self.matcher = matcher
        self.dry_run = dry_run
        self.poll_interval = max(0.05, poll_interval)

    def screenshot(self) -> np.ndarray:
        return self.device.screenshot()

    def find_image(self, name: str, image: Optional[np.ndarray] = None) -> MatchResult:
        return self.matcher.find(name, image=image)

    def click_image(self, name: str, timeout: float = 5.0) -> bool:
        """在超时时间内反复截图找图；命中后点击并返回 True，否则 False。"""
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            frame = self.device.screenshot()
            result = self.matcher.find(name, image=frame)
            if result.found:
                logger.info(
                    "命中模板=%s score=%.3f center=(%d,%d)%s",
                    name, result.score, result.x, result.y,
                    " [DRY RUN: 未点击]" if self.dry_run else "",
                )
                if not self.dry_run:
                    self.device.click(result.x, result.y)
                return True
            if time.monotonic() >= deadline:
                logger.info("找图超时：template=%s timeout=%.2fs", name, timeout)
                return False
            time.sleep(self.poll_interval)
