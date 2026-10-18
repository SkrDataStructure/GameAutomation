from __future__ import annotations

import logging

from core.actions import Actions
from core.task import Task

logger = logging.getLogger(__name__)


class StartGameTask(Task):
    name = "start_game"

    def __init__(self, actions: Actions):
        self.actions = actions

    def run(self) -> bool:
        if not self.actions.click_image("start", timeout=2.0):
            logger.info("未发现开始按钮；请检查模板与当前游戏画面。")
            return False
        return True


class ClaimRewardTask(Task):
    name = "claim_reward"

    def __init__(self, actions: Actions):
        self.actions = actions

    def run(self) -> bool:
        if not self.actions.click_image("reward", timeout=2.0):
            logger.info("当前没有可领取奖励。")
            return False
        # 点击奖励后再等待确认按钮；实际游戏可能需要按业务调整等待时长。
        if not self.actions.click_image("confirm", timeout=3.0):
            logger.info("已点击奖励，但未找到确认按钮。")
            return False
        return True
