"""多维评分融合器 — 场景自适应权重 + 规则加权 + 美学评分 + 多样性奖励"""

import numpy as np
from .models import (
    CompositionCandidate, CompositionResult, SceneUnderstanding,
    GeomStructure, SceneWeights, SceneType
)
from .rules import ALL_RULES


class Scorer:
    """构图评分器"""

    def __init__(self):
        self._rules = {r.name: r for r in ALL_RULES}

    def score_candidates(
        self,
        candidates: list[CompositionCandidate],
        scene: SceneUnderstanding,
        geom: GeomStructure,
        image: np.ndarray,
        aesthetic_model=None,  # 可选美学网络
        top_k: int = 3
    ) -> list[CompositionResult]:
        """对候选列表评分，返回 Top-K"""

        weights = SceneWeights.for_scene(scene.scene_type)
        weight_dict = {
            "rule_of_thirds": weights.rule_of_thirds,
            "golden_ratio": weights.golden_ratio,
            "leading_lines": weights.leading_lines,
            "symmetry": weights.symmetry,
            "natural_framing": weights.natural_framing,
            "negative_space": weights.negative_space,
            "visual_balance": weights.visual_balance,
            "depth_layering": weights.depth_layering,
            "diagonals": weights.diagonals,
            "pattern_rhythm": weights.pattern_rhythm,
            "color_harmony": weights.color_harmony,
            "gestalt": weights.gestalt,
        }

        results = []
        for candidate in candidates:
            rule_scores = {}
            weighted_sum = 0.0

            for rule_name, rule in self._rules.items():
                s = rule.score(candidate, scene, geom, image)
                rule_scores[rule_name] = s
                weighted_sum += s * weight_dict.get(rule_name, 0.08)

            # 美学评分 (如果有模型)
            aesthetic = 0.0
            if aesthetic_model is not None:
                crop = image[candidate.y:candidate.y + candidate.height,
                             candidate.x:candidate.x + candidate.width]
                aesthetic = aesthetic_model.predict(crop)

            total = 0.55 * weighted_sum + 0.35 * aesthetic

            results.append(CompositionResult(
                candidate=candidate,
                total_score=total + 0.0,  # diversity bonus 在后面加
                rule_scores=rule_scores,
                weighted_sum=weighted_sum,
                aesthetic_score=aesthetic
            ))

        # 排序 + 多样性奖励
        results.sort(key=lambda r: r.weighted_sum + r.aesthetic_score, reverse=True)
        self._add_diversity_bonus(results, top_k)

        return results[:top_k]

    def _add_diversity_bonus(self, results: list[CompositionResult], top_k: int):
        """对不同构图方案的多样性加分，避免 Top-3 都类似"""
        if len(results) < 2:
            return
        diversity_weight = 0.10

        for i in range(min(len(results), top_k)):
            bonus = 0.0
            for j in range(i):
                # 计算与前 j 个方案的距离
                ri, rj = results[i], results[j]
                ci, cj = ri.candidate, rj.candidate
                # 中心点距离 + 尺寸差异
                cxi, cyi = ci.x + ci.width / 2, ci.y + ci.height / 2
                cxj, cyj = cj.x + cj.width / 2, cj.y + cj.height / 2
                d_center = np.hypot(cxi - cxj, cyi - cyj)
                max_dim = max(ci.width, ci.height)
                center_diff = min(1.0, d_center / (max_dim * 0.5))

                area_diff = abs(ci.area - cj.area) / max(ci.area, cj.area)
                diff = 0.5 * center_diff + 0.5 * area_diff
                bonus = max(bonus, diff)

            results[i].diversity_bonus = diversity_weight * bonus
            results[i].total_score += results[i].diversity_bonus

        # 按总分重排
        results.sort(key=lambda r: r.total_score, reverse=True)


class FastScorer:
    """快速预评分器 — 仅用 4 条速度最快的规则"""

    _FAST_RULES = ["rule_of_thirds", "leading_lines", "negative_space", "visual_balance"]

    def __init__(self):
        from .rules import get_rule_by_name
        self.rules = [(n, get_rule_by_name(n)) for n in self._FAST_RULES]
        self.rules = [(n, r) for n, r in self.rules if r is not None]

    def pre_score(self, candidates: list[CompositionCandidate],
                  scene: SceneUnderstanding, geom: GeomStructure,
                  image: np.ndarray, top_n: int = 50) -> list[CompositionCandidate]:
        """快速评分，返回 Top-N 候选"""
        scores = []
        for c in candidates:
            total = sum(r.score(c, scene, geom, image) for _, r in self.rules)
            scores.append((total, c))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scores[:top_n]]
