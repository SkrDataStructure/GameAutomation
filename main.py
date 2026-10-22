from __future__ import annotations

import argparse
import logging
import sys

from config.settings import LOG_DIR, LOG_LEVEL
from config.games import demo as demo_config
from core.actions import Actions
from core.device import DeviceManager
from core.matcher import TemplateMatcher
from core.scheduler import Scheduler
from games.demo.tasks import ClaimRewardTask, StartGameTask


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / "android-game-bot.log", encoding="utf-8"),
        ],
    )


def build_tasks(game: str, actions: Actions):
    # TODO 任务构建入口
    if game == "demo":
        return [StartGameTask(actions), ClaimRewardTask(actions)]
    raise ValueError(f"未知游戏 {game!r}；当前支持：demo")


def main() -> int:
    parser = argparse.ArgumentParser(description="Android 游戏自动化框架")
    parser.add_argument("--game", default="demo", help="游戏目录/配置名称，当前示例：demo")
    parser.add_argument("--serial", default=None, help="可选 ADB 设备序列号")
    parser.add_argument("--dry-run", action="store_true", help="只识别不点击")
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("main")

    if args.game != demo_config.GAME_NAME:
        logger.error("当前示例只注册了 demo 游戏。请参考 README 添加新游戏。")
        return 2

    try:
        device = DeviceManager.get(serial=args.serial)
        d = device.connect()
        logger.info("设备连接成功：%s", args.serial or "ADB 默认设备")
        info = d.info
        logger.info("设备信息：%s", {
            "productName": info.get("productName"),
            "sdkInt": info.get("sdkInt"),
            "displayWidth": info.get("displayWidth"),
            "displayHeight": info.get("displayHeight"),
        })
        frame = device.screenshot()
        logger.info("截图成功，分辨率：%d x %d", frame.shape[1], frame.shape[0])

        matcher = TemplateMatcher(device, demo_config.TEMPLATES)
        actions = Actions(device, matcher, dry_run=args.dry_run)
        tasks = build_tasks(args.game, actions)
        reports = Scheduler().run_all(tasks)

        failed = [r for r in reports if not r.success]
        logger.info("执行完成：总数=%d 成功=%d 失败/未完成=%d",
                    len(reports), len(reports) - len(failed), len(failed))
        return 0 if not failed else 1
    except Exception:
        logger.exception("框架启动失败，请检查 ADB、USB 调试授权与 uiautomator2 初始化。")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
