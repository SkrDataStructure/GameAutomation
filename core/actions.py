from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np

import config
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

    def wait_find_image(self, name: str, timeout: float, interval:float=0.3) -> MatchResult:
        """在超时时间内反复截图找图；命中后返回 True，否则 False。 interval 为每次找图的间隔时间"""
        return self.matcher.wait_find(name=name , timeout=timeout,  interval=interval)

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

    def click_until_image(
            self,
            name: str,
            skip_xy: tuple[int, int] = (360, 580),  # 加速动画的点击坐标
            timeout: float = 3.0,
    ) -> bool:
        """
        在 timeout 秒内反复点屏幕加速过场动画，同时找图；
        找到目标图后点击其中心坐标并返回 True，超时返回 False。
        """
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            # 1) 截图找目标按钮
            frame = self.screenshot()
            result = self.find_image(name, image=frame)

            if result.found:
                # 2) 找到目标：点它的中心，返回成功
                logger.info(
                    "命中模板=%s score=%.3f center=(%d,%d)%s",
                    name, result.score, result.x, result.y,
                    " [DRY RUN: 未点击]" if self.dry_run else "",
                )
                if not self.dry_run:
                    self.device.click(result.x, result.y)
                return True

            # 3) 没找到：点屏幕加速过场动画
            if not self.dry_run:
                self.device.click(*skip_xy)

            # 4) 超时退出
            if time.monotonic() >= deadline:
                logger.info("找图超时：template=%s timeout=%.2fs", name, timeout)
                return False

            # 5) 控制节奏
            time.sleep(self.poll_interval)

    def swipe(self, x: int, y: int, x1: int, y1: int) -> None:
        self.device.swipe(x, y, x1, y1)