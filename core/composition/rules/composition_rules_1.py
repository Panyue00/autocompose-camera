"""引导线规则 / 对称规则 / 框景规则"""

import numpy as np
from .base import CompositionRule
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class LeadingLines(CompositionRule):
    name = "leading_lines"

    def score(self, candidate, scene, geom, image):
        if not geom.leading_lines:
            return 0.0
        w, h = candidate.width, candidate.height
        max_dim = max(w, h)
        scores = []

        for line in geom.leading_lines:
            # 线是否指向主体
            points_to = 0.0
            if scene.subject_boxes:
                for (sx, sy, sw, sh, label, conf) in scene.subject_boxes:
                    cx = sx + sw / 2 - candidate.x
                    cy = sy + sh / 2 - candidate.y
                    d = line.direction_to_point(cx, cy)
                    points_to = max(points_to, conf * self._distance_decay(d, sigma=0.1 * max_dim))

            # 线与构图线(三分线)对齐度
            third_positions = [w/3, 2*w/3, h/3, 2*h/3]
            alignment = 0.0
            for tp in third_positions:
                d1 = abs(line.x1 - tp) if tp < w else abs(line.y1 - tp)
                alignment = max(alignment, self._distance_decay(d1, sigma=0.03 * max_dim))

            # 消失点在画面内加分
            vp_bonus = 0.0
            if geom.vanishing_points:
                for vp in geom.vanishing_points:
                    if vp.is_interior:
                        vp_bonus = max(vp_bonus, vp.confidence * 0.15)

            scores.append(line.saliency * (0.5 * points_to + 0.3 * alignment + vp_bonus))

        return float(np.mean(scores)) if scores else 0.0


class Symmetry(CompositionRule):
    name = "symmetry"

    def score(self, candidate, scene, geom, image):
        if not geom.symmetry_axes:
            return 0.0
        w, h = candidate.width, candidate.height
        best = 0.0

        for axis in geom.symmetry_axes:
            # 对称轴距画面中轴的偏离
            mid_x, mid_y = w / 2, h / 2
            ax_mid_x = (axis.x1 + axis.x2) / 2
            ax_mid_y = (axis.y1 + axis.y2) / 2

            if axis.axis_type == "vertical":
                dev = abs(ax_mid_x - mid_x) / (w / 2)
            elif axis.axis_type == "horizontal":
                dev = abs(ax_mid_y - mid_y) / (h / 2)
            else:
                dev = 0.0

            # 场景类型加权
            type_mult = 1.0
            if axis.axis_type == "vertical" and scene.scene_type.value == "architecture":
                type_mult = 1.5
            elif axis.axis_type == "horizontal" and scene.scene_type.value == "landscape":
                type_mult = 1.5

            score = axis.strength * (1 - dev) * type_mult
            best = max(best, score)

        return min(1.0, best)


class NaturalFraming(CompositionRule):
    name = "natural_framing"

    def score(self, candidate, scene, geom, image):
        if scene.segmentation_mask is None:
            return 0.0
        h, w = candidate.height, candidate.width

        # 简化检测: 查找画面边缘的前景物体
        mask = scene.segmentation_mask
        frame_classes = {2, 3, 4, 5, 8, 10}  # 树/建筑/墙/山脉/拱门等

        # 统计四边缘的前景像素比例
        edge_pixels = np.concatenate([
            mask[0:5, :].flatten(),         # 上
            mask[-5:, :].flatten(),         # 下
            mask[:, 0:5].flatten(),         # 左
            mask[:, -5:].flatten()          # 右
        ])
        frame_pixels = np.sum(np.isin(edge_pixels, list(frame_classes)))
        total_edge = len(edge_pixels)
        frame_ratio = frame_pixels / total_edge if total_edge > 0 else 0

        # 主体在框内
        subject_inside = 0.0
        if scene.subject_boxes:
            for (sx, sy, sw, sh, _, _) in scene.subject_boxes:
                # 检查主体是否在画面中间区域
                cx, cy = sx + sw/2 - candidate.x, sy + sh/2 - candidate.y
                if 0.25 * w < cx < 0.75 * w and 0.25 * h < cy < 0.75 * h:
                    subject_inside = max(subject_inside, 1.0)

        return frame_ratio * 0.6 + subject_inside * 0.4
