GAME_NAME = "demo"

# region: (x1, y1, x2, y2)，以整张截图为坐标系，x2/y2 不包含在区域内。
TEMPLATES = {
    "start": {
        "path": "games/demo/templates/start.png",
        "threshold": 0.88,
        "region": None,
    },
    "reward": {
        "path": "games/demo/templates/reward.png",
        "threshold": 0.90,
        "region": None,
    },
    "confirm": {
        "path": "games/demo/templates/confirm.png",
        "threshold": 0.86,
        "region": None,
    },
}

# 示例任务顺序。任务具体实现由 games/demo/tasks.py 提供。
TASKS = ("start_game", "claim_reward")
