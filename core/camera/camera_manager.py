"""相机管理 — Kivy Camera 封装，拍照 + 保存"""

import os
import time
from PIL import Image
import numpy as np


class CameraManager:
    """封装 Kivy Camera，提供拍照、前后摄切换、闪光灯控制"""

    def __init__(self):
        self._widget = None        # Kivy Camera widget
        self._facing = "back"      # front / back
        self._flash_mode = "off"   # off / on / auto
        self._capture_callback = None
        self._last_photo_path = None

    def bind_widget(self, camera_widget):
        """绑定 Kivy Camera widget"""
        self._widget = camera_widget
        camera_widget.play = True

    def capture(self) -> str | None:
        """拍照并保存为 JPEG，返回文件路径"""
        if self._widget is None:
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"AC_{timestamp}.jpg"
        path = os.path.join(self._get_photo_dir(), filename)

        self._widget.export_to_png(path.replace(".jpg", ".png"))

        # 转 JPEG
        try:
            img = Image.open(path.replace(".jpg", ".png"))
            img = img.convert("RGB")
            img.save(path, "JPEG", quality=95)
            os.remove(path.replace(".jpg", ".png"))
            self._last_photo_path = path
            return path
        except Exception:
            return None

    def get_frame(self) -> np.ndarray | None:
        """获取当前取景器帧作为 numpy 数组 (RGB)"""
        if self._widget is None:
            return None
        try:
            tex = self._widget.texture
            if tex is None:
                return None
            pixels = tex.pixels
            if pixels is None:
                return None
            w, h = tex.size
            arr = np.frombuffer(pixels, dtype=np.uint8).reshape(h, w, 4)
            return arr[:, :, :3]  # RGBA → RGB
        except Exception:
            return None

    def switch_camera(self):
        """切换前后摄像头"""
        if self._widget is None:
            return
        self._facing = "front" if self._facing == "back" else "back"
        self._widget.index = 0 if self._facing == "back" else 1

    def set_flash(self, mode: str):
        """设置闪光灯: off / on / auto"""
        self._flash_mode = mode

    def release(self):
        """释放相机"""
        if self._widget:
            self._widget.play = False

    def _get_photo_dir(self) -> str:
        """获取照片保存目录"""
        from kivy.app import App
        data_dir = App.get_running_app().user_data_dir
        photo_dir = os.path.join(data_dir, "photos")
        os.makedirs(photo_dir, exist_ok=True)
        return photo_dir

    @property
    def last_photo_path(self) -> str | None:
        return self._last_photo_path
