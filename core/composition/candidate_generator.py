"""候选窗口生成器 — 多尺度滑动窗口搜索"""

import numpy as np
from .models import CompositionCandidate, SceneUnderstanding

ASPECT_RATIOS = [
    (4, 3, 4/3),
    (16, 9, 16/9),
    (1, 1, 1.0),
    (3, 2, 3/2),
]

SUBJECT_SIZES = [0.33, 0.5, 0.66]  # 主体占画面比例

GRID_POSITIONS = [
    (1/3, 1/3), (1/2, 1/3), (2/3, 1/3),
    (1/3, 1/2), (1/2, 1/2), (2/3, 1/2),
    (1/3, 2/3), (1/2, 2/3), (2/3, 2/3),
]


class CandidateGenerator:
    """生成候选裁剪窗口并进行剪枝"""

    def __init__(self, min_area_ratio: float = 0.4, iou_threshold: float = 0.85):
        self.min_area_ratio = min_area_ratio
        self.iou_threshold = iou_threshold

    def generate(self, image_width: int, image_height: int,
                 scene: SceneUnderstanding,
                 max_candidates: int = 400) -> list[CompositionCandidate]:
        """生成所有有效候选窗口"""
        anchors = self._find_anchors(image_width, image_height, scene)
        candidates = []

        for (ax, ay) in anchors:
            for (ar_w, ar_h, ar_val) in ASPECT_RATIOS:
                for subj_ratio in SUBJECT_SIZES:
                    for (gx, gy) in GRID_POSITIONS:
                        # 反推裁剪框大小
                        subject_area_w = image_width * subj_ratio * ar_val
                        subject_area_h = image_height * subj_ratio

                        crop_w = subject_area_w / (ar_val if ar_val >= 1 else 1)
                        crop_h = subject_area_h / (1 / ar_val if ar_val < 1 else 1)

                        # 裁剪框位置: 主体在 gx, gy 处
                        crop_x = ax - gx * crop_w
                        crop_y = ay - gy * crop_h

                        # 边界约束
                        if crop_x < 0 or crop_y < 0:
                            continue
                        if crop_x + crop_w > image_width or crop_y + crop_h > image_height:
                            continue

                        # 面积约束
                        if crop_w * crop_h < self.min_area_ratio * image_width * image_height:
                            continue

                        candidates.append(CompositionCandidate(
                            x=int(crop_x), y=int(crop_y),
                            width=int(crop_w), height=int(crop_h),
                            aspect_ratio=ar_val,
                            anchor_type="grid",
                            anchor_x=ax, anchor_y=ay
                        ))

        # IOU 去重
        candidates = self._deduplicate(candidates, max_candidates)
        return candidates

    def _find_anchors(self, w: int, h: int, scene: SceneUnderstanding) -> list[tuple[float, float]]:
        """查找主体锚点"""
        anchors = []

        # 显著性峰值 (top 5)
        if scene.saliency_map is not None:
            from scipy.ndimage import maximum_filter
            sal = scene.saliency_map
            local_max = maximum_filter(sal, size=min(w, h) // 10)
            peaks = np.argwhere((sal == local_max) & (sal > 0.3))
            if len(peaks) > 0:
                peak_vals = sal[peaks[:, 0], peaks[:, 1]]
                top_indices = np.argsort(peak_vals)[-5:]
                for idx in top_indices:
                    py, px = peaks[idx]
                    anchors.append((float(px) * w / sal.shape[1],
                                    float(py) * h / sal.shape[0]))

        # 主体包围框中心
        for (sx, sy, sw, sh, _, _) in scene.subject_boxes:
            anchors.append((sx + sw / 2, sy + sh / 2))

        # 如果没有任何锚点，用画面中心
        if not anchors:
            anchors = [(w / 2, h / 2)]

        return anchors[:20]  # 最多20个锚点

    def _deduplicate(self, candidates: list[CompositionCandidate],
                     max_count: int) -> list[CompositionCandidate]:
        """IOU 去重，保留面积最大的"""
        if len(candidates) <= max_count:
            return candidates

        # 按面积降序
        candidates.sort(key=lambda c: c.area, reverse=True)
        kept = []

        for c in candidates:
            if len(kept) >= max_count:
                break
            duplicate = False
            for k in kept:
                iou = self._compute_iou(c, k)
                if iou > self.iou_threshold:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(c)

        return kept

    def _compute_iou(self, a: CompositionCandidate, b: CompositionCandidate) -> float:
        """计算两个裁剪窗口的 IoU"""
        x1 = max(a.x, b.x)
        y1 = max(a.y, b.y)
        x2 = min(a.x + a.width, b.x + b.width)
        y2 = min(a.y + a.height, b.y + b.height)
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inter = (x2 - x1) * (y2 - y1)
        union = a.area + b.area - inter
        return inter / union if union > 0 else 0.0
