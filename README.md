# Android Game Bot

基于 Python + uiautomator2 + OpenCV 的 Android 游戏自动化示例框架。

## 功能

- `core/` 与 `games/` 分层：核心不导入任何游戏业务模块。
- 设备管理器进程内单例、懒连接；截图统一从 `DeviceManager.screenshot()` 获取。
- OpenCV 模板内存缓存，一张截图可匹配多个模板，支持 ROI 区域搜索并返回整屏绝对坐标。
- `click_image()` 封装找图、点击、超时等待，返回 `bool`。
- 任务调度逐任务隔离异常，单个任务失败不会阻断后续任务。
- 游戏模板名、路径、阈值、ROI 均集中在游戏配置文件。
- 默认包含示例游戏任务和无模板时可安全启动的诊断任务。

## 环境要求

- Python 3.10+
- Android 真机开启开发者选项与 USB 调试
- 已安装 Android Platform Tools（`adb`），且 `adb` 在 PATH 中
- 使用数据线连接手机并在手机上允许这台电脑进行 USB 调试

## 安装

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
adb devices
python -m uiautomator2 init
```

`adb devices` 应显示类似 `SERIAL    device`。如果显示 `unauthorized`，请在手机上确认授权。

## 快速开始

```bash
python main.py --game demo
```

先检查设备连接与截图；没有放入模板时，示例任务会提示找不到模板并安全返回，不会盲目点击。

## 添加自己的游戏

1. 在 `games/<game_name>/templates/` 放入按钮模板 PNG。建议从游戏当前截图裁剪按钮，避免包含动态背景。
2. 复制 `config/games/demo.py` 为 `config/games/<game_name>.py`，修改模板名、路径、阈值与区域。
3. 在 `games/<game_name>/tasks.py` 编写继承 `Task` 的业务任务。
4. 在 `main.py` 的 `build_tasks()` 注册该游戏的任务构造器，或按项目需要扩展为动态注册。

模板路径相对于项目根目录。`region` 格式为 `(x1, y1, x2, y2)`，右下角坐标不包含在 ROI 内。区域坐标以整张截图左上角为原点。

## 配置示例

```python
"start": {
    "path": "games/demo/templates/start.png",
    "threshold": 0.88,
    "region": None,
}
```

匹配分数是 OpenCV `TM_CCOEFF_NORMED` 的相关系数，不是概率。阈值需按游戏画面调试。

## 命令行选项

```bash
python main.py --game demo
python main.py --game demo --serial <adb-serial>
python main.py --game demo --dry-run
```

`--dry-run` 仍连接设备并截图、执行识别，但不实际点击，适合调试。

## 安全与稳定性说明

- 点击操作会作用于当前前台设备；运行前请确认游戏窗口正确。
- 游戏画面动画、分辨率或缩放变化可能影响匹配准确度，请先用 `--dry-run` 验证。
- 本框架不包含绕过反作弊、修改游戏客户端或规避服务条款的功能。
- 设备断连后不会无限重试；可在业务层根据实际情况加入受控重连。
