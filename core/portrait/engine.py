"""人像虚化引擎 — 深度估计 + CoC 渲染 + Matting"""

import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class PortraitEngine:
    """人像虚化 — 模拟光学弥散圆 (CoC) 虚化"""

    def __init__(self):
        self.f_number = 1.4  # 模拟光圈 f/1.4 ~ f/16
        self.blades = 0      # 0=圆形光斑, 6/8/9=多边形
        self._depth_model = None
        self._seg_model = None

    def set_models(self, depth_model, seg_model):
        self._depth_model = depth_model
        self._seg_model = seg_model

    def apply(self, image: np.ndarray, depth_map: np.ndarray | None = None,
              person_mask: np.ndarray | None = None) -> np.ndarray:
        """对人像照片应用虚化"""
        if not HAS_CV2:
            return image

        h, w = image.shape[:2]

        # 获取深度图
        if depth_map is None and self._depth_model is not None:
            depth_map = self._depth_model.predict(image)
        if depth_map is None:
            return image

        # 确保深度图尺寸匹配
        if depth_map.shape[:2] != (h, w):
            depth_map = cv2.resize(depth_map, (w, h))

        # 获取人物 mask
        if person_mask is None and self._seg_model is not None:
            seg = self._seg_model.predict(image)
            person_mask = np.isin(seg, [15])  # person class = 15 in COCO

        # 对焦在人物中心深度
        if person_mask is not None and person_mask.any():
            focus_depth = np.median(depth_map[person_mask])
        else:
            focus_depth = np.median(depth_map)

        # 计算 CoC 半径
        k = 12.0 / self.f_number  # f/1.4 → 12px max
        depth_diff = np.abs(depth_map - focus_depth)
        coc_radius = depth_diff * k * min(w, h) / 1000

        # 对每个像素采样
        result = image.copy().astype(np.float32)
        sample_count = 16

        for y in range(0, h, 2):  # 隔行处理 (性能)
            for x in range(0, w, 2):
                r = coc_radius[y, x]
                if r < 1.0:
                    continue

                # 泊松圆盘采样 (简化: 随机圆形采样)
                samples = []
                for _ in range(sample_count):
                    angle = np.random.uniform(0, 2 * np.pi)
                    dist = np.random.uniform(0, r)
                    sx = int(x + dist * np.cos(angle))
                    sy = int(y + dist * np.sin(angle))
                    sx = np.clip(sx, 0, w - 1)
                    sy = np.clip(sy, 0, h - 1)
                    samples.append(image[sy, sx])

                if samples:
                    # 光斑检测: 原像素亮度 > 200
                    px_brightness = np.mean(image[y, x])
                    if px_brightness > 200:
                        blend = self._render_bokeh(image[y, x], np.mean(samples, axis=0), r)
                    else:
                        blend = np.mean(samples, axis=0)

                    result[y, x] = blend

        return result.clip(0, 255).astype(np.uint8)

    def _render_bokeh(self, original: np.ndarray, blurred: np.ndarray,
                      radius: float) -> np.ndarray:
        """光斑渲染 — 扩大模糊 + 边缘高亮"""
        bokeh_radius = radius * 2.5
        edge = np.cos(np.pi * min(1.0, bokeh_radius / 30)) * 0.5 + 0.5
        return original * (1 - edge) + blurred * edge * 1.2
