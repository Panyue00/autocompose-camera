"""负空间 / 视觉平衡 / 深度层次 / 对角线规则"""

import numpy as np
from .base import CompositionRule
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class NegativeSpace(CompositionRule):
    name = "negative_space"

    def score(self, candidate, scene, geom, image):
        if scene.saliency_map is None:
            return 0.4  # 中性分
        h, w = scene.saliency_map.shape
        # 显著性低于阈值的比例
        threshold = 0.15
        neg_ratio = np.mean(scene.saliency_map < threshold)

        # 钟形曲线: 30-50% 最优
        if 0.3 <= neg_ratio <= 0.7:
            score = np.cos(np.pi * (neg_ratio - 0.5) / 0.5)
        else:
            score = max(0, 1 - abs(neg_ratio - 0.5) * 2)

        # 负空间一致性加分
        consistency = 0.0
        if scene.segmentation_mask is not None:
            neg_mask = scene.saliency_map < threshold
            neg_labels = scene.segmentation_mask[neg_mask]
            if len(neg_labels) > 0:
                dominant = np.bincount(neg_labels.flatten()).argmax()
                consistency = np.mean(neg_labels == dominant) * 0.2

        return float(min(1.0, max(0.0, score + consistency)))


class VisualBalance(CompositionRule):
    name = "visual_balance"

    def score(self, candidate, scene, geom, image):
        if scene.saliency_map is None and image is None:
            return 0.5
        h, w = candidate.height, candidate.width

        # 用显著性 + 亮度计算每象限视觉质量
        if scene.saliency_map is not None:
            weight_map = scene.saliency_map
            hh, ww = weight_map.shape
        else:
            gray = np.mean(image, axis=2).astype(np.float32) / 255.0
            weight_map = 1 - gray  # 暗部更"重"

        h_mid, w_mid = weight_map.shape[0] // 2, weight_map.shape[1] // 2
        quads = [
            weight_map[:h_mid, :w_mid],      # 左上
            weight_map[:h_mid, w_mid:],      # 右上
            weight_map[h_mid:, :w_mid],      # 左下
            weight_map[h_mid:, w_mid:],      # 右下
        ]
        masses = [np.mean(q) for q in quads]
        masses_arr = np.array(masses)

        if np.mean(masses_arr) == 0:
            return 0.5

        balance = 1 - np.std(masses_arr) / np.mean(masses_arr)
        return float(np.clip(balance, 0, 1))


class DepthLayering(CompositionRule):
    name = "depth_layering"

    def score(self, candidate, scene, geom, image):
        if scene.depth_map is None:
            return 0.5
        depth = scene.depth_map.flatten()

        # K-means 3层聚类
        from sklearn.cluster import KMeans
        try:
            kmeans = KMeans(n_clusters=3, n_init=1, max_iter=10).fit(
                depth.reshape(-1, 1)
            )
            counts = np.bincount(kmeans.labels_, minlength=3) / len(depth)
            counts = np.sort(counts)[::-1]  # 降序

            # 理想分布: 前景15-25%, 中景30-50%, 背景25-40%
            ideal = np.array([0.35, 0.40, 0.25])
            # JS 散度
            m = (counts + ideal) / 2
            kl_count = np.sum(counts * np.log((counts + 1e-10) / (m + 1e-10)))
            kl_ideal = np.sum(ideal * np.log((ideal + 1e-10) / (m + 1e-10)))
            js = (kl_count + kl_ideal) / 2

            return float(np.clip(1 - js, 0, 1))
        except Exception:
            return 0.5


class Diagonals(CompositionRule):
    name = "diagonals"

    def score(self, candidate, scene, geom, image):
        w, h = candidate.width, candidate.height
        max_dim = max(w, h)
        diag_angles = [np.arctan2(h, w), np.arctan2(-h, w)]

        best = 0.0
        for line in geom.leading_lines:
            angle = abs(line.angle)
            if 0.35 < angle < 1.2 or 1.95 < angle < 2.8:  # 20°~70° 或 110°~160°
                for da in diag_angles:
                    match = abs(np.sin(angle - da))
                    if match > 0.85:
                        best = max(best, line.saliency * match)

        # 三角形检测: 3条线形成三角形
        triangle_bonus = 0.0
        lines = geom.leading_lines
        if len(lines) >= 3:
            for i in range(len(lines)):
                for j in range(i + 1, len(lines)):
                    for k in range(j + 1, len(lines)):
                        # 检查三线是否不共线
                        a1, a2, a3 = lines[i].angle, lines[j].angle, lines[k].angle
                        if (abs(a1 - a2) > 0.3 and abs(a2 - a3) > 0.3 and abs(a1 - a3) > 0.3):
                            triangle_bonus = 0.15
                            break

        return min(1.0, best + triangle_bonus)
