from __future__ import annotations

import threading
from typing import Optional

import cv2
import numpy as np
import uiautomator2 as u2

from config.settings import DEVICE_CONNECT_TIMEOUT


class DeviceManager:
    """进程内唯一的设备连接管理器，首次访问时才连接。"""

    _instance: Optional["DeviceManager"] = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, serial: Optional[str] = None, connect_timeout: float = DEVICE_CONNECT_TIMEOUT):
        if self._initialized:
            # 单例一旦初始化配置，不允许后续调用悄悄切换设备。
            if serial and self._serial and serial != self._serial:
                raise RuntimeError(
                    f"DeviceManager 已绑定设备 {self._serial!r}，不能切换到 {serial!r}。"
                )
            return
        self._serial = serial
        self._connect_timeout = connect_timeout
        self._device = None
        self._lock = threading.RLock()
        self._initialized = True

    @classmethod
    def get(cls, serial: Optional[str] = None) -> "DeviceManager":
        """取得全局单例；不在这里连接设备。"""
        return cls(serial=serial)

    @property
    def serial(self) -> Optional[str]:
        return self._serial

    def connect(self):
        """懒连接；连接成功后复用同一 uiautomator2 句柄。"""
        with self._lock:
            if self._device is not None:
                return self._device
            self._device = u2.connect(self._serial) if self._serial else u2.connect()
            # 触发一次轻量 RPC，尽早暴露连接失败。
            _ = self._device.info
            return self._device

    @property
    def device(self):
        return self.connect()

    def screenshot(self) -> np.ndarray:
        """统一截图入口，返回 OpenCV BGR uint8 图像。"""
        with self._lock:
            pil_image = self.connect().screenshot(format="pillow")
            rgb = np.asarray(pil_image.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def click(self, x: int, y: int) -> None:
        with self._lock:
            self.connect().click(int(x), int(y))

    def press(self, key: str) -> None:
        with self._lock:
            self.connect().press(key)

    def swipe(self, x: int, y: int, x1, y1) -> None:
        self.connect().swipe(int(x), int(y), int(x1), int(y1))