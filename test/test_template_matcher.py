from pathlib import Path

import cv2
import pytest

from core.device import DeviceManager
from core.matcher import TemplateMatcher, logger
from core.actions import Actions

FILE_PATH = Path(__file__).parent
FILE_NAME = "ten_level"

@pytest.fixture
def templateSpec():
    return  {
    FILE_NAME: {
        "path": FILE_PATH / f"templates/{FILE_NAME}.png"  ,
        "threshold": 0.88,
        "region": (0.3097, 0.8500, 0.6861, 0.8859),
    }
}

@pytest.fixture
def device():
    return DeviceManager.get()

@pytest.fixture
def matcher(device, templateSpec):
    logger.info(templateSpec.get(FILE_NAME).get("path"))
    return TemplateMatcher(device, templateSpec)

@pytest.fixture
def action(device, matcher):
    return Actions(device=device, matcher =matcher, dry_run=False)

@pytest.mark.find
def test_find_in_image(templateSpec, device):
    matcher = TemplateMatcher(device, templateSpec)
    image = device.screenshot()
    assert matcher.find_in_image(image, FILE_NAME).found is True

@pytest.mark.screenshot
def test_screenshot(tmp_path):
    device = DeviceManager.get()
    grap = device.screenshot()
    save_path = FILE_PATH / f"image.png"
    ok = cv2.imwrite(str(save_path), grap)
    assert ok

@pytest.mark.click
def test_action_click(action):
    assert action.click_image(FILE_NAME)


@pytest.mark.find_all
def test_find_all_in_image(templateSpec, device):
    image = device.screenshot()
    # 裁剪下半屏幕
    crop_region = None
    crop_region = (0.0, 0.5, 1.0, 1.0) # 下半屏幕
    # crop_region = (0.0, 0.0, 1.0, 0.5) # 上半屏幕
    matcher = TemplateMatcher(device, templateSpec)
    list = matcher.find_all_in_image(image, FILE_NAME, crop_region=crop_region)
    logger.info(f"找到{len(list)}个怪兽")
    if len(list) > 0:
        for r in list:
            logger.info(f"x = {r.x}, y = {r.y}")
    assert len(list) > 0,"未找到怪兽"

@pytest.mark.region
def test_get_region_ratio(action):
    """输入完整图片，用模板在全图中查找，找到后返回相对比例。"""
    name = FILE_NAME  # 例如 "lobby"

    # 1. 拿完整截图（也可以用 cv2.imread 读本地图片）
    frame = action.device.screenshot()

    # 2. 全图匹配：临时把该模板的 region 置空，确保不裁剪
    matcher = action.matcher
    spec = matcher.specs.get(name)
    assert spec is not None, f"未配置模板: {name}"

    # 用 find_in_image 直接匹配整图（不经过 region）
    result = matcher.find_in_image(frame, name)
    logger.info(f"整图中未找到模板 {name}，score={result.score:.3f}")
    assert result.found

    # 3. 像素 box -> 相对比例
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = result.box
    ratio = (x1 / w, y1 / h, x2 / w, y2 / h)

    # 4. 打印结果
    logger.info(f"\n模板: {name}")
    logger.info(f"图像尺寸: 宽={w}, 高={h}")
    logger.info(f"匹配像素: ({x1}, {y1}, {x2}, {y2})")
    logger.info(f"匹配得分: {result.score:.3f}")
    logger.info(f"相对比例: ({ratio[0]:.4f}, {ratio[1]:.4f}, {ratio[2]:.4f}, {ratio[3]:.4f})")

    # 5. 验证：比例乘回去应等于原像素
    back = (round(ratio[0] * w), round(ratio[1] * h),
            round(ratio[2] * w), round(ratio[3] * h))
    assert back == (x1, y1, x2, y2), f"比例还原不一致: {back} != {(x1, y1, x2, y2)}"

