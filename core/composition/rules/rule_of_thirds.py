"""三分法构图规则"""

import numpy as np
from .base import CompositionRule
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class RuleOfThirds(CompositionRule):
    name = "rule_of_thirds"

    def score(self, candidate, scene, geom, image):
        h, w = candidate.height, candidate.width
        max_dim = max(w, h)

        # 三分交点 (相对于裁剪框, 4个)
        third_x = [w / 3, 2 * w / 3]
        third_y = [h / 3, 2 * h / 3]
        intersections = [(tx, ty) for tx in third_x for ty in third_y]

        # 主体得分: 主体中心距最近三分交点
        subject_score = 0.0
        if scene.subject_boxes:
            for (sx, sy, sw, sh, label, conf) in scene.subject_boxes:
                cx = sx + sw / 2 - candidate.x  # 转为裁剪框内坐标
                cy = sy + sh / 2 - candidate.y
                min_dist = min(np.hypot(cx - ix, cy - iy) for (ix, iy) in intersections)
                subject_score = max(subject_score, self._distance_decay(min_dist, sigma=0.15 * max_dim))

        # 水平线得分
        horizon_score = 0.0
        if geom.horizon_y is not None:
            h_line = geom.horizon_y - candidate.y
            min_h_dist = min(abs(h_line - ty) for ty in third_y)
            horizon_score = self._distance_decay(min_h_dist, sigma=0.08 * h)

        # 垂直线得分 (显著性最高的垂直线)
        vertical_score = 0.0
        verticals = [l for l in geom.leading_lines if abs(np.sin(l.angle)) > 0.85]
        if verticals:
            best_v = max(verticals, key=lambda l: l.saliency)
            vx = (best_v.x1 + best_v.x2) / 2 - candidate.x
            min_v_dist = min(abs(vx - tx) for tx in third_x)
            vertical_score = best_v.saliency * self._distance_decay(min_v_dist, sigma=0.1 * w)

        return 0.6 * subject_score + 0.2 * horizon_score + 0.2 * vertical_score
