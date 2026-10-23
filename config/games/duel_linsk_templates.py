# 决斗链接配置模板
from pathlib import Path

from config.settings import DEFAULT_THRESHOLD


PORTAL_TEMPLATES_PATH = "games/duellinks/templates/portal"
PUBLIC_TEMPLATES_PATH = "games/duellinks/templates"

DAILY_TEMPLATES = {

}

# 决斗门模板
PORTAL_TEMPLATES = {
    "lobby": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "lobby.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.4722, 0.8656, 0.5278, 0.8797),
    },
    "world": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "world.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.4750, 0.8648, 0.5250, 0.8789),
    },
    "email": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "email.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.6500, 0.1094, 0.7319, 0.1430),
    },
    "portal": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "portal.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.0000, 0.9422, 0.1986, 1.0000)
    },
    "switch_portal": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "switch_portal.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.1361, 0.0938, 0.3722, 0.1258)
    },
    "ten_level": {  # 识别 10 级传送门按钮 未选中 9.4的阈值 有点高
        "path": Path(PORTAL_TEMPLATES_PATH) / "ten_level.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.1278, 0.6836, 0.2000, 0.7031)
    },
    "award": { # 默认三倍奖励
        "path": Path(PORTAL_TEMPLATES_PATH) / "award.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.7792, 0.9578, 0.7917, 0.9719)
    },
    "game_ready": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "game_ready.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.4278, 0.8516, 0.5694, 0.8836)
    },
    "next_portal": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "next_portal.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.9528, 0.4609, 0.9931, 0.5062)
    },
    "dialog": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "dialog.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.0000, 0.8484, 1.0000, 0.9234)
    },
        "start": { # 屏幕中心 x = 360, y = 580
        "path": Path(PORTAL_TEMPLATES_PATH) / "start.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.1958, 0.8539, 0.3056, 0.8852)
    },
    "main1": { # 主要阶段1
        "path": Path(PORTAL_TEMPLATES_PATH) / "main1.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.5528, 0.0500, 0.8097, 0.0703)
    },
    "summon": { # 通常召唤 点击后再做一次判断 是否成功
        # x = 650, y = 820  进战斗阶段
        "path": Path(PORTAL_TEMPLATES_PATH) / "summon.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.2944, 0.7578, 0.4667, 0.7836)
    },
    "draw": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "draw.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.5500, 0.0508, 0.8097, 0.0695)
    },
    "monster": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "monster.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": None
    },
    "battle": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "battle.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.5569, 0.0516, 0.8083, 0.0695)
    },
    "duel_end": { # 轮询时重复点击 x = 150, y = 240
        "path": Path(PORTAL_TEMPLATES_PATH) / "duel_end.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.3444, 0.9289, 0.6597, 0.9719)
    },
    "end_next": { # 要执行两次 一次奖励 一次评分 之后重复点击 x = 150, y = 240， 轮询到识别主页
        "path": Path(PORTAL_TEMPLATES_PATH) / "end_next.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.3222, 0.9258, 0.6792, 0.9695)
    },
    "insufficient": { # 钥匙不够
        "path": Path(PORTAL_TEMPLATES_PATH) / "insufficient.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": None
    },
    "back": { # 未添加
        "path": Path(PORTAL_TEMPLATES_PATH) / "back.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": None
    },
    "ack": {
        "path": Path(PORTAL_TEMPLATES_PATH) / "ack.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": None
    }
}

PUBLIC_TEMPLATES = {
    "lobby": {
        "path": Path(PUBLIC_TEMPLATES_PATH) / "lobby.png",
        "threshold": DEFAULT_THRESHOLD,
        "region": (0.4722, 0.8656, 0.5278, 0.8797),
    },
}


# 1. 每日签到       2. 传送门决斗
TaskS = ("daily", "portal")