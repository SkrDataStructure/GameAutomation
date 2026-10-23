from __future__ import annotations

import time
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

import cv2
import numpy as np

from config.settings import DEFAULT_THRESHOLD
from config.settings import PROJECT_ROOT
from core.device import DeviceManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    path: str
    threshold: float = DEFAULT_THRESHOLD
    region: Optional[tuple[float, float, float, float]] = None


@dataclass(frozen=True)
class MatchResult:
    found: bool
    x: Optional[int] = None
    y: Optional[int] = None
    score: float = 0.0
    template: Optional[str] = None
    box: Optional[tuple[int, int, int, int]] = None


class TemplateMatcher:
    """模板缓存 + 一张截图匹配多个模板的 OpenCV 引擎。"""

    def __init__(self, device: DeviceManager, specs: Mapping[str, dict]):
        self.device = device
        self.specs = {
            name: TemplateSpec(
                name=name,
                path=str(value["path"]),
                threshold=float(value.get("threshold", DEFAULT_THRESHOLD)),
                region=tuple(value["region"]) if value.get("region") is not None else None,
            )
            for name, value in specs.items()
        }
        self._cache: dict[str, np.ndarray] = {}
        self._cache_lock = threading.RLock()

    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate

    def _load_template(self, name: str) -> Optional[np.ndarray]:
        if name not in self.specs:
            raise KeyError(f"未配置模板: {name}")
        path = self._resolve_path(self.specs[name].path)
        cache_key = str(path.resolve())
        with self._cache_lock:
            if cache_key not in self._cache:
                image = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if image is None:
                    logger.warning("模板不可用（文件不存在或无法解码）: %s", path)
                    return None
                if image.size == 0:
                    logger.warning("模板为空: %s", path)
                    return None
                self._cache[cache_key] = image
            return self._cache[cache_key]

    @staticmethod
    def _validate_region(region, image_shape):
        """region 支持两种写法：
        - 相对比例：四个值都在 [0, 1]，如 (0.1, 0.2, 0.3, 0.4)
        - 绝对像素：如 (192, 216, 576, 432)
        返回绝对像素坐标 (x1, y1, x2, y2)，并 clamp 到图像范围内。
        """
        h, w = image_shape[:2]
        x1, y1, x2, y2 = region

        # 四个值都在 [0, 1] 视为相对比例
        if all(0.0 <= v <= 1.0 for v in region):
            x1, x2 = x1 * w, x2 * w
            y1, y2 = y1 * h, y2 * h

        x1, x2 = int(round(x1)), int(round(x2))
        y1, y2 = int(round(y1)), int(round(y2))

        # clamp 到图像范围内
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))

        if x1 >= x2 or y1 >= y2:
            raise ValueError(
                f"ROI {region} 无效（宽={w}, 高={h}）；"
                f"格式应为 (x1,y1,x2,y2)，或四个 [0,1] 内的比例值。"
            )
        return x1, y1, x2, y2

    def find_in_image(self, image: np.ndarray, name: str) -> MatchResult:
        spec = self.specs.get(name)
        if spec is None:
            raise KeyError(f"未配置模板: {name}")
        template = self._load_template(name)
        if template is None:
            return MatchResult(False, template=name)

        search = image
        offset_x = offset_y = 0
        if spec.region is not None:
            x1, y1, x2, y2 = self._validate_region(spec.region, image.shape)
            search = image[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1

        th, tw = template.shape[:2]
        sh, sw = search.shape[:2]
        if th > sh or tw > sw:
            logger.debug("模板 %s 大于搜索区域，跳过匹配", name)
            return MatchResult(False, template=name)

        # 低方差模板会令 TM_CCOEFF_NORMED 不稳定，明确拒绝近乎纯色模板。
        if float(np.std(template)) < 1e-6:
            logger.warning("模板 %s 方差过低，不适合 TM_CCOEFF_NORMED", name)
            return MatchResult(False, template=name)

        scores = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
        _, max_score, _, max_loc = cv2.minMaxLoc(scores)
        score = float(max_score)
        if not np.isfinite(score) or score < spec.threshold:
            return MatchResult(False, score=score if np.isfinite(score) else 0.0, template=name)

        x = offset_x + max_loc[0] + tw // 2
        y = offset_y + max_loc[1] + th // 2
        return MatchResult(
            found=True,
            x=int(x),
            y=int(y),
            score=score,
            template=name,
            box=(offset_x + max_loc[0], offset_y + max_loc[1],
                 offset_x + max_loc[0] + tw, offset_y + max_loc[1] + th),
        )

    def find(self, name: str, image: Optional[np.ndarray] = None) -> MatchResult:
        frame = image if image is not None else self.device.screenshot()
        return self.find_in_image(frame, name)

    def find_many(self, names: Sequence[str], image: Optional[np.ndarray] = None) -> dict[str, MatchResult]:
        """对多个模板复用同一张截图；每个模板仍使用自己的阈值与 ROI。"""
        frame = image if image is not None else self.device.screenshot()
        return {name: self.find_in_image(frame, name) for name in names}

    def wait_find(
            self,
            name: str,
            timeout: float,
            interval: float = 0.3,
    ) -> MatchResult:
        """在 timeout 秒内反复截图并查找模板 name，直到找到或超时。

        适用于页面加载 / 交互动画等导致目标延迟出现的场景。

        Args:
            name:     模板名，未配置会立即抛 KeyError（不进入等待）。
            timeout:  最长等待秒数，<=0 时只尝试一次。
            interval: 两次尝试之间的间隔秒数。

        Returns:
            找到时返回 found=True 的 MatchResult；
            超时返回最后一次的失败结果（score 为最后一次得分，便于排查）。
        """
        if interval < 0:
            raise ValueError("interval 不能为负数")

        # 先校验模板配置，配置错误应立即失败而非空等
        if self.specs.get(name) is None:
            raise KeyError(f"未配置模板: {name}")

        deadline = time.monotonic() + max(0.0, timeout)
        last_result = MatchResult(False, template=name)

        while True:
            image = self.device.screenshot()  # 每次都用新帧
            result = self.find_in_image(image, name)
            if result.found:
                return result
            last_result = result

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return last_result
            time.sleep(min(interval, remaining))

    def clear_cache(self, name: Optional[str] = None) -> None:
        """模板文件更新后可显式清缓存；不传 name 清除全部。"""
        with self._cache_lock:
            if name is None:
                self._cache.clear()
            elif name in self.specs:
                key = str(self._resolve_path(self.specs[name].path).resolve())
                self._cache.pop(key, None)

    def crop_by_ratio(image: np.ndarray, region: tuple[float, float, float, float]) -> np.ndarray:
        """按归一化比例 (x1, y1, x2, y2) 裁剪，比例范围 0~1。
            裁剪图片ROI
        region=(0.0, 0.0, 1.0, 1.0) 表示整图。
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = region
        px1, py1 = int(round(x1 * w)), int(round(y1 * h))
        px2, py2 = int(round(x2 * w)), int(round(y2 * h))
        # 防御：越界钳制 + 至少 1 像素
        px1, px2 = max(0, min(px1, w - 1)), max(1, min(px2, w))
        py1, py2 = max(0, min(py1, h - 1)), max(1, min(py2, h))
        if px2 <= px1 or py2 <= py1:
            raise ValueError(f"无效 region: {region} -> 像素 ({px1},{py1},{px2},{py2})")
        return image[py1:py2, px1:px2]

    def crop_by_pixels(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
        """按像素 (x1, y1, x2, y2) 裁剪。"""
        h, w = image.shape[:2]
        x1, y1, x2, y2 = box
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"无效 box: {box}")
        return image[y1:y2, x1:x2]

    def find_all_in_image(
            self,
            image: np.ndarray,
            name: str,
            crop_region: tuple[float, float, float, float] | None = None,
            threshold: float | None = None,
            max_results: int = 20,
            nms_iou: float = 0.3,
    ) -> list[MatchResult]:
        """在 image（可先按 crop_region 裁剪）中找出模板 name 的所有实例。

        crop_region: 归一化比例 (x1,y1,x2,y2)；None 表示全图。
        threshold: 覆盖 spec.threshold。
        返回按 score 降序、互不重叠的 MatchResult 列表。
        """
        spec = self.specs.get(name)
        if spec is None:
            raise KeyError(f"未配置模板: {name}")
        template = self._load_template(name)
        if template is None:
            return []

        # 1. 裁剪
        if crop_region is not None:
            h, w = image.shape[:2]
            x1, y1, x2, y2 = crop_region
            px1, py1 = int(round(x1 * w)), int(round(y1 * h))
            px2, py2 = int(round(x2 * w)), int(round(y2 * h))
            search = image[py1:py2, px1:px2]
            off_x, off_y = px1, py1
        else:
            search = image
            off_x = off_y = 0

        th, tw = template.shape[:2]
        sh, sw = search.shape[:2]
        if th > sh or tw > sw:
            logger.debug("模板 %s 大于搜索区域 %dx%d < 模板 %dx%d",
                         name, sw, sh, tw, th)
            return []
        if float(np.std(template)) < 1e-6:
            logger.warning("模板 %s 方差过低，跳过", name)
            return []

        thr = spec.threshold if threshold is None else threshold
        scores = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)

        # 2. 所有候选点
        ys, xs = np.where(scores >= thr)
        if len(xs) == 0:
            return []

        # 3. 按分数降序 + NMS
        order = np.argsort(scores[ys, xs])[::-1]
        boxes: list[tuple[int, int, int, int]] = []
        results: list[MatchResult] = []
        for i in order:
            x, y = int(xs[i]), int(ys[i])
            box = (x, y, x + tw, y + th)
            if any(self._iou(box, b) > nms_iou for b in boxes):
                continue
            boxes.append(box)
            results.append(MatchResult(
                found=True,
                x=int(off_x + x + tw // 2),
                y=int(off_y + y + th // 2),
                score=float(scores[y, x]),
                template=name,
                box=(off_x + x, off_y + y, off_x + x + tw, off_y + y + th),
            ))
            if len(results) >= max_results:
                break

        return results

    @staticmethod
    def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        if inter == 0:
            return 0.0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        return inter / (area_a + area_b - inter)
