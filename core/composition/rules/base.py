"""构图规则基类"""

from abc import ABC, abstractmethod
import numpy as np
from ..models import CompositionCandidate, SceneUnderstanding, GeomStructure


class CompositionRule(ABC):
    """构图规则的抽象基类。每条规则对候选窗口打分，返回 0..1"""

    name: str = "base"

    @abstractmethod
    def score(
        self,
        candidate: CompositionCandidate,
        scene: SceneUnderstanding,
        geom: GeomStructure,
        image: np.ndarray
    ) -> float:
        """
        对候选窗口打分
        :param candidate: 裁剪窗口
        :param scene: 场景语义
        :param geom: 几何结构
        :param image: 原图 (H×W×3, uint8)
        :return: 得分 0..1
        """
        ...

    def _distance_decay(self, d: float, sigma: float) -> float:
        """距离 → 得分的高斯衰减: exp(-d²/(2σ²))"""
        return np.exp(-d * d / (2 * sigma * sigma))

    def _normalize_distance(self, d: float, max_dim: float) -> float:
        """归一化距离 (相对画面尺寸)"""
        return d / max_dim if max_dim > 0 else 0
