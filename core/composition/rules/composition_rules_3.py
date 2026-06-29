"""图案与节奏 / 色彩和谐 / 格式塔完形规则"""

import numpy as np
from .base import CompositionRule
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class PatternRhythm(CompositionRule):
    name = "pattern_rhythm"

    def score(self, candidate, scene, geom, image):
        if image is None:
            return 0.3
        # 自相关检测周期性
        gray = np.mean(image, axis=2).astype(np.float32) / 255.0
        h, w = gray.shape

        # 降采样以提高速度
        ds = max(1, min(h, w) // 256)
        small = gray[::ds, ::ds]

        # 1D 自相关 (沿水平方向)
        row_mean = np.mean(small, axis=0)
        row_mean -= np.mean(row_mean)
        autocorr = np.correlate(row_mean, row_mean, mode='full')
        autocorr = autocorr[len(autocorr)//2:]

        # 寻找第一个峰值 (除零滞后)
        if len(autocorr) > 1:
            peaks = (autocorr[1:-1] > autocorr[:-2]) & (autocorr[1:-1] > autocorr[2:])
            peak_indices = np.where(peaks)[0] + 1
            if len(peak_indices) > 0:
                first_peak = peak_indices[0]
                strength = autocorr[first_peak] / (autocorr[0] + 1e-10)
                # 奇数周期加分
                odd_bonus = 0.2 if first_peak % 2 == 1 else 0.0
                return float(min(1.0, strength + odd_bonus))
        return 0.2


class ColorHarmony(CompositionRule):
    name = "color_harmony"

    def score(self, candidate, scene, geom, image):
        if image is None:
            return 0.3
        # 转 LAB 计算色相分布
        try:
            import cv2
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            h, w = lab.shape[:2]
            # 采样以减少计算
            step = max(1, min(h, w) // 50)
            sampled = lab[::step, ::step].reshape(-1, 3)

            # 计算 a-b 平面上的色相角
            a, b = sampled[:, 1].astype(np.float32), sampled[:, 2].astype(np.float32)
            hues = np.arctan2(b, a)  # -pi..pi

            # 构建色相直方图 (12 bins)
            hist, _ = np.histogram(hues, bins=12, range=(-np.pi, np.pi))
            hist = hist / hist.sum()
            top3 = np.sort(hist)[-3:]

            # 检测色彩方案
            # 互补色: 两个 dominant peaks 相距约 180°
            if len(top3) >= 2 and top3[-1] > 0.15 and top3[-2] > 0.1:
                complementary = 0.9
            elif np.max(hist) > 0.3:
                complementary = 0.6  # 单色
            else:
                complementary = 0.3

            return float(min(1.0, complementary))
        except ImportError:
            return 0.3


class GestaltClosure(CompositionRule):
    name = "gestalt"

    def score(self, candidate, scene, geom, image):
        if image is None:
            return 0.3

        try:
            import cv2
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            # 连续性: 检测平滑曲线
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            continuity = 0.0
            closure = 0.0
            similarity = 0.0

            for contour in contours:
                if len(contour) < 20:
                    continue
                # 连续性: 弧长/点数的平滑度
                arc_len = cv2.arcLength(contour, False)
                if len(contour) > 1:
                    smoothness = arc_len / len(contour)
                    continuity = max(continuity, min(1.0, smoothness / 5.0))

                # 闭合力: 首尾距离 vs 弧长
                if len(contour) >= 4:
                    first = contour[0][0]
                    last = contour[-1][0]
                    gap = np.hypot(first[0] - last[0], first[1] - last[1])
                    closure_ratio = 1 - gap / (arc_len + 1e-10)
                    closure = max(closure, closure_ratio)

            # 相似性: 同类型元素间距一致性 (简化)
            if scene.subject_boxes and len(scene.subject_boxes) >= 2:
                centers = [(sx + sw/2, sy + sh/2) for (sx, sy, sw, sh, _, _) in scene.subject_boxes]
                if len(centers) >= 2:
                    dists = [np.hypot(centers[i][0] - centers[j][0],
                                      centers[i][1] - centers[j][1])
                             for i in range(len(centers))
                             for j in range(i + 1, len(centers))]
                    if len(dists) > 1 and np.mean(dists) > 0:
                        similarity = 1 - np.std(dists) / np.mean(dists)

            return float(np.clip((continuity + closure + similarity) / 3, 0, 1))
        except ImportError:
            return 0.3
