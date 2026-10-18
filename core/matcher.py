from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

import cv2
import numpy as np

from config.settings import PROJECT_ROOT
from core.device import DeviceManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    path: str
    threshold: float = 0.88
    region: Optional[tuple[int, int, int, int]] = None


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
                threshold=float(value.get("threshold", 0.88)),
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
        h, w = image_shape[:2]
        x1, y1, x2, y2 = region
        if not (0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h):
            raise ValueError(
                f"ROI {region} 超出截图范围（宽={w}, 高={h}）；格式应为 (x1,y1,x2,y2)。"
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

    def clear_cache(self, name: Optional[str] = None) -> None:
        """模板文件更新后可显式清缓存；不传 name 清除全部。"""
        with self._cache_lock:
            if name is None:
                self._cache.clear()
            elif name in self.specs:
                key = str(self._resolve_path(self.specs[name].path).resolve())
                self._cache.pop(key, None)
