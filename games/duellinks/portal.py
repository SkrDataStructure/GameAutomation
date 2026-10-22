import logging
from time import sleep

from core.actions import Actions
from core.task import Task
from games.demo.tasks import logger

wait_click = sleep
wait_time = 1


class Portal(Task):
    """决斗链接 - 传送门决斗"""

    name = "portal"

    def __init__(self, actions: Actions):
        super().__init__()
        self.actions = actions

    # ------------------------------------------------------------------ #
    # 主流程
    # ------------------------------------------------------------------ #
    def run(self) -> bool:
        index = self.actions.find_image("email", self.actions.screenshot())
        # 进入传送门页面
        self._entry_portal()

        while index.found:
            # 单局循环：准备开始 -> 对局 -> 对局结束
            # 游戏准备开始
            if not self._game_ready_start():
                continue

            while True:
                # 游戏中（返回 False 表示对局结束）
                result = self._duel()
                if not result:
                    index = self.actions.find_image("email", self.actions.screenshot())
                    break

            # 对局结束/无法开始后，切回传送门页面
            if not self.actions.click_image("portal", 2):
                logger.warning("未找到 portal 按钮，可能已离开传送门页面")
                break
            wait_click(3)

        return True

    # ------------------------------------------------------------------ #
    # 进入传送门页面
    # ------------------------------------------------------------------ #
    def _entry_portal(self):
        self.actions.find_image("email", self.actions.screenshot())
        logger.info("识别到游戏首页，正在尝试切换ui")

        if self.actions.click_image("lobby", 2):
            wait_click(1)

        # 点击进入传送门
        self.actions.click_image("portal", 2)
        wait_click(3)

        # 切换传送门
        self.actions.click_image("switch_portal", 2)
        wait_click(wait_time)
        self.actions.swipe(360, 710, 360, 1200)
        wait_click(wait_time)
        self.actions.device.click(360, 820)

    # ------------------------------------------------------------------ #
    # 准备开始（返回 False 表示无法开始）
    # ------------------------------------------------------------------ #
    def _game_ready_start(self) -> bool:
        # 设置10级传送门
        self.actions.click_image("ten_level", 2)

        # 设置三倍奖励
        image = self.actions.find_image("award", self.actions.screenshot())
        # 设置三倍前提条件为 钥匙必须充足
        if not image.found: # 未开启三倍奖励
            if not self.actions.find_image("insufficient", self.actions.screenshot()):
                wait_click(2)
                self.actions.device.click(570, 1234)
                wait_click(wait_time)
                self.actions.swipe(360, 710, 360, 1200)
                wait_click(wait_time)
                self.actions.device.click(360, 1030)    # 三倍按钮位置
                wait_click(wait_time)
                frame = self.actions.screenshot()
                insufficient = self.actions.find_image("insufficient", frame).found
                game_ready = self.actions.find_image("game_ready", frame).found

                if insufficient or not game_ready:
                    logger.info("钥匙不足或未找到开始键，返回上一页")
                    self.actions.device.press("back")
                    wait_click(wait_time)

        # 准备开始
        game_ready = self.actions.click_image("game_ready", 2)
        if not game_ready:  # 未找到开始键
            # 判断钥匙是否不足
            insufficient = self.actions.find_image(
                "insufficient", self.actions.screenshot()
            )
            if insufficient.found:  # 钥匙不足切换下一个传送门
                self.actions.click_image("next_portal", 5)
                return False
            raise RuntimeError("未找到开始游戏，且无法判断钥匙是否充足")

        # 跳过旁白并开始游戏
        for _ in range(10):
            if self.actions.click_image("start", 1):
                break
            self.actions.device.click(360, 580)
        else:
            raise RuntimeError("点击 决斗 失败，已尝试 10 轮")

        return True

    # ------------------------------------------------------------------ #
    # 对局（返回 False 表示对局结束）
    # ------------------------------------------------------------------ #
    def _duel(self) -> bool:
        """返回 False 表示对局结束，True 表示继续。"""
        self._duel_main()

        # 战斗阶段返回 False = 对局结束
        if not self._duel_battle():
            return False

        # 战斗结束但未结算，尝试结算；True=已结束 → 返回 False
        return not self._duel_end()

    # ------------------------------------------------------------------ #
    # 主要阶段
    # ------------------------------------------------------------------ #
    def _duel_main(self) -> bool:
        """返回 True 表示继续下一步。"""
        frame = self.actions.screenshot()
        if not self.actions.find_image("main1", frame).found:
            return True

        logger.info("主要阶段")
        monsters = self.actions.matcher.find_all_in_image(
            frame, "monster", (0, 0.5, 1.0, 1.0)
        )
        # 场上怪兽不超过3只 进行通召
        if len(monsters) < 3:
            self.actions.swipe(360, 1200, 360, 580)  # 从手牌滑到场上
            self.actions.click_image("summon", 2)
            wait_click(2)

        # 切换阶段
        self.actions.device.click(650, 820)
        wait_click(0.5)
        self.actions.device.click(650, 820)
        wait_click(wait_time)

        return True

    # ------------------------------------------------------------------ #
    # 战斗阶段（返回 False 表示对局结束）
    # ------------------------------------------------------------------ #
    def _duel_battle(self) -> bool:
        """返回 True 表示对局继续，False 表示对局结束。"""
        frame = self.actions.screenshot()
        if not self.actions.find_image("battle", frame).found:
            return True

        logger.info("战斗阶段")
        monster_list = self.actions.matcher.find_all_in_image(
            frame, "monster", (0, 0.5, 1.0, 1.0)
        )
        if not monster_list:
            logger.info("当前场上不存在怪兽")
            return True

        logger.info("场上怪兽：%s", monster_list)

        for monster in monster_list:  # 遍历怪兽攻击
            wait_click(wait_time)
            self.actions.swipe(monster.x, monster.y, monster.x, monster.y - 200)
            if self._duel_end():  # True = 对局结束
                return False

        # 切换阶段
        self.actions.device.click(650, 820)
        wait_click(0.5)
        self.actions.device.click(650, 820)
        wait_click(wait_time)
        return True

    # ------------------------------------------------------------------ #
    # 结算（返回 True 表示对局已结束）
    # ------------------------------------------------------------------ #
    def _duel_end(self) -> bool:
        """返回 True 表示对局已结束（点到结算页）。"""
        if self.actions.click_until_image(
            name="duel_end", skip_xy=(150, 240), timeout=2
        ):

            # 轮询主页
            while not self.actions.find_image("email", self.actions.screenshot()).found:
                self.actions.click_until_image(
                    name="end_next", skip_xy=(150, 240), timeout=2
                )
                self.actions.click_until_image(
                    name="lobby", skip_xy=(150, 240), timeout=2
                )

            wait_click(wait_time)
            return True
        return False