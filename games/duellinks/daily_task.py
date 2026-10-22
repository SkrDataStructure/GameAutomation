# 每日签到任务

from core.actions import Actions
from core.task import Task


class DailyTask(Task):
    """ 决斗链接 - 每日签到 """

    name = "daily"

    def __int__(self, actions: Actions):
        self.actions = actions

    def run(self) -> bool:
        pass