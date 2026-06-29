"""黄金比例/黄金螺旋规则"""

import numpy as np
from .base import CompositionRule
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class GoldenRatio(CompositionRule):
    name = "golden_ratio"
    PHI = 1.618033988749895

    # 4种黄金螺旋的收敛点 (归一化坐标)
    SPIRAL_ORIGINS = [
        (1.0, 0.0),   # 右下
        (0.0, 0.0),   # 左下
        (0.0, 1.0),   # 左上
        (1.0, 1.0),   # 右上
    ]

    def score(self, candidate, scene, geom, image):
        w, h = candidate.width, candidate.height
        max_dim = max(w, h)

        best = 0.0
        for (ox, oy) in self.SPIRAL_ORIGINS:
            # 收敛点在画面中的实际位置
            spx = ox * w
            spy = oy * h

            if not scene.subject_boxes:
                continue

            # 找最近的主体
            for (sx, sy, sw, sh, label, conf) in scene.subject_boxes:
                cx = sx + sw / 2 - candidate.x
                cy = sy + sh / 2 - candidate.y
                d = np.hypot(cx - spx, cy - spy)
                score = conf * self._distance_decay(d, sigma=0.12 * max_dim)
                best = max(best, score)

        # 额外: 引导线方向匹配螺旋切线
        tangent_bonus = 0.0
        if geom.leading_lines:
            for orig_idx, (ox, oy) in enumerate(self.SPIRAL_ORIGINS):
                spx, spy = ox * w, oy * h
                # 螺旋在收敛点的切线方向 (简化为4个方向)
                tangent_angles = [np.pi / 4, -np.pi / 4, 3 * np.pi / 4, -3 * np.pi / 4]
                target = tangent_angles[orig_idx]
                for line in geom.leading_lines:
                    # 线方向与切线方向对齐
                    angle_diff = abs(np.sin(line.angle - target))
                    if angle_diff > 0.9:  # 接近平行
                        tangent_bonus = max(tangent_bonus, line.saliency * 0.1)

        return min(1.0, best + tangent_bonus)
