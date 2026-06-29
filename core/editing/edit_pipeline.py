"""后期编辑管线 — 裁剪 + 透视矫正 + 调色 + 滤镜 + undo/redo"""

from dataclasses import dataclass
import numpy as np
from ..cv.image_utils import crop_image, correct_horizon, correct_perspective, adjust_color


@dataclass
class EditStep:
    """单步编辑操作"""
    op_type: str  # crop / rotate / perspective / color / filter
    params: dict
    preview_before: np.ndarray | None = None  # 用于快速 undo


class EditPipeline:
    """非破坏性编辑管线 (Command Pattern + undo/redo)"""

    MAX_HISTORY = 20

    def __init__(self):
        self.original: np.ndarray | None = None
        self.current: np.ndarray | None = None
        self.undo_stack: list[EditStep] = []
        self.redo_stack: list[EditStep] = []

    def load(self, image: np.ndarray):
        """加载原始图片"""
        self.original = image.copy()
        self.current = image.copy()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def apply_crop(self, x: int, y: int, w: int, h: int):
        """应用裁剪"""
        self._push_undo("crop", {"x": x, "y": y, "w": w, "h": h})
        self.current = crop_image(self.current, x, y, w, h)

    def apply_rotate(self, degrees: float):
        """应用旋转 (水平校正)"""
        self._push_undo("rotate", {"degrees": degrees})
        self.current = correct_horizon(self.current, degrees)

    def apply_perspective(self, src_pts: np.ndarray, dst_pts: np.ndarray):
        """应用透视矫正"""
        self._push_undo("perspective", {"src": src_pts.tolist(), "dst": dst_pts.tolist()})
        self.current = correct_perspective(self.current, src_pts, dst_pts)

    def apply_color(self, brightness: float = 0.0, contrast: float = 1.0,
                    saturation: float = 1.0, warmth: float = 0.0):
        """应用调色"""
        self._push_undo("color", {
            "brightness": brightness, "contrast": contrast,
            "saturation": saturation, "warmth": warmth
        })
        self.current = adjust_color(self.current, brightness, contrast, saturation, warmth)

    def undo(self) -> bool:
        """撤销"""
        if not self.undo_stack:
            return False
        step = self.undo_stack.pop()
        self.redo_stack.append(step)
        # 从 original 重放 undo_stack 中的所有步骤
        self._replay_from_original()
        return True

    def redo(self) -> bool:
        """重做"""
        if not self.redo_stack:
            return False
        step = self.redo_stack.pop()
        self._apply_step(step)
        self.undo_stack.append(step)
        return True

    def save(self, path: str, quality: int = 95):
        """保存当前结果"""
        try:
            import cv2
            cv2.imwrite(path, cv2.cvtColor(self.current, cv2.COLOR_RGB2BGR),
                       [cv2.IMWRITE_JPEG_QUALITY, quality])
        except ImportError:
            from PIL import Image
            Image.fromarray(self.current).save(path, "JPEG", quality=quality)

    def _push_undo(self, op_type: str, params: dict):
        """压入撤销栈"""
        self.undo_stack.append(EditStep(
            op_type=op_type, params=params,
            preview_before=self.current.copy()
        ))
        if len(self.undo_stack) > self.MAX_HISTORY:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _apply_step(self, step: EditStep):
        """执行单步编辑"""
        if step.op_type == "crop":
            p = step.params
            self.current = crop_image(self.current, p["x"], p["y"], p["w"], p["h"])
        elif step.op_type == "rotate":
            self.current = correct_horizon(self.current, step.params["degrees"])
        elif step.op_type == "perspective":
            self.current = correct_perspective(
                self.current,
                np.array(step.params["src"]),
                np.array(step.params["dst"])
            )
        elif step.op_type == "color":
            self.current = adjust_color(self.current, **step.params)

    def _replay_from_original(self):
        """从原图重放 undo_stack 中的所有步骤"""
        self.current = self.original.copy()
        for step in self.undo_stack:
            self._apply_step(step)
