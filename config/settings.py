from pathlib import Path

# 项目根目录。路径统一基于此目录解析，避免依赖启动时的工作目录。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"

DEVICE_CONNECT_TIMEOUT = 15.0
DEFAULT_MATCH_TIMEOUT = 5.0
MATCH_POLL_INTERVAL = 0.25
SCREENSHOT_FORMAT = "opencv"  # BGR uint8 ndarray
LOG_LEVEL = "INFO"
