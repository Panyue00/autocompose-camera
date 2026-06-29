"""构图引擎数据模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import numpy as np


class SceneType(Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    ARCHITECTURE = "architecture"
    STREET = "street"
    MACRO = "macro"
    UNKNOWN = "unknown"


@dataclass
class Line2D:
    """二维线段"""
    x1: float; y1: float; x2: float; y2: float
    saliency: float = 1.0  # 显著性 0..1

    @property
    def angle(self) -> float:
        return np.arctan2(self.y2 - self.y1, self.x2 - self.x1)

    @property
    def length(self) -> float:
        return np.hypot(self.x2 - self.x1, self.y2 - self.y1)

    def direction_to_point(self, px: float, py: float) -> float:
        """线段延长线到点的最近距离 (归一化)"""
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        if dx == 0 and dy == 0:
            return np.hypot(px - self.x1, py - self.y1)
        t = max(0, min(1, ((px - self.x1) * dx + (py - self.y1) * dy) / (dx * dx + dy * dy)))
        proj_x, proj_y = self.x1 + t * dx, self.y1 + t * dy
        return np.hypot(px - proj_x, py - proj_y)


@dataclass
class VanishingPoint:
    x: float; y: float
    confidence: float = 0.0
    line_count: int = 0
    is_interior: bool = False


@dataclass
class SymmetryAxis:
    x1: float; y1: float; x2: float; y2: float
    strength: float = 0.0  # 0..1
    axis_type: str = "vertical"  # vertical / horizontal / rotational


@dataclass
class GeomStructure:
    """几何结构提取结果"""
    leading_lines: list = field(default_factory=list)      # list[Line2D]
    vanishing_points: list = field(default_factory=list)    # list[VanishingPoint]
    symmetry_axes: list = field(default_factory=list)       # list[SymmetryAxis]
    horizon_y: Optional[float] = None
    tilt_angle: float = 0.0  # 透视倾斜角度 (度)
    perspective_matrix: Optional[np.ndarray] = None  # 3x3 单应性矩阵


@dataclass
class SceneUnderstanding:
    """场景语义理解结果"""
    scene_type: SceneType = SceneType.UNKNOWN
    segmentation_mask: Optional[np.ndarray] = None   # H×W int labels
    depth_map: Optional[np.ndarray] = None           # H×W float
    saliency_map: Optional[np.ndarray] = None        # H×W float 0..1
    subject_boxes: list = field(default_factory=list) # list of (x,y,w,h,label,conf)
    subject_mask: Optional[np.ndarray] = None         # H×W bool
    face_landmarks: list = field(default_factory=list) # list of face keypoints
    person_poses: list = field(default_factory=list)   # list of pose keypoints


@dataclass
class CompositionCandidate:
    """一个候选裁剪窗口"""
    x: int; y: int; width: int; height: int
    aspect_ratio: float = 0.0  # w/h
    anchor_type: str = ""      # 锚点类型: saliency_peak / subject_center / rule_grid
    anchor_x: float = 0.0; anchor_y: float = 0.0

    def to_rect(self):
        return (self.x, self.y, self.width, self.height)

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass
class CompositionResult:
    """构图评分结果"""
    candidate: CompositionCandidate
    total_score: float = 0.0
    rule_scores: dict = field(default_factory=dict)     # rule_name -> score
    weighted_sum: float = 0.0
    aesthetic_score: float = 0.0
    diversity_bonus: float = 0.0


@dataclass
class SceneWeights:
    """场景自适应的规则权重"""
    rule_of_thirds: float = 0.12
    golden_ratio: float = 0.08
    leading_lines: float = 0.10
    symmetry: float = 0.06
    natural_framing: float = 0.08
    negative_space: float = 0.10
    visual_balance: float = 0.08
    depth_layering: float = 0.08
    diagonals: float = 0.06
    pattern_rhythm: float = 0.05
    color_harmony: float = 0.07
    gestalt: float = 0.05

    @classmethod
    def for_scene(cls, scene_type: SceneType) -> "SceneWeights":
        weights = {
            SceneType.LANDSCAPE: cls(
                rule_of_thirds=0.12, golden_ratio=0.08, leading_lines=0.15,
                symmetry=0.06, natural_framing=0.08, negative_space=0.10,
                visual_balance=0.08, depth_layering=0.12, diagonals=0.06,
                pattern_rhythm=0.03, color_harmony=0.07, gestalt=0.05),
            SceneType.PORTRAIT: cls(
                rule_of_thirds=0.15, golden_ratio=0.05, leading_lines=0.08,
                symmetry=0.03, natural_framing=0.05, negative_space=0.06,
                visual_balance=0.10, depth_layering=0.08, diagonals=0.05,
                pattern_rhythm=0.02, color_harmony=0.08, gestalt=0.05),
            SceneType.ARCHITECTURE: cls(
                rule_of_thirds=0.08, golden_ratio=0.12, leading_lines=0.18,
                symmetry=0.15, natural_framing=0.06, negative_space=0.05,
                visual_balance=0.08, depth_layering=0.05, diagonals=0.10,
                pattern_rhythm=0.08, color_harmony=0.03, gestalt=0.02),
            SceneType.STREET: cls(
                rule_of_thirds=0.10, golden_ratio=0.06, leading_lines=0.12,
                symmetry=0.05, natural_framing=0.10, negative_space=0.08,
                visual_balance=0.10, depth_layering=0.08, diagonals=0.15,
                pattern_rhythm=0.05, color_harmony=0.06, gestalt=0.05),
            SceneType.MACRO: cls(
                rule_of_thirds=0.18, golden_ratio=0.10, leading_lines=0.05,
                symmetry=0.08, natural_framing=0.05, negative_space=0.12,
                visual_balance=0.08, depth_layering=0.08, diagonals=0.05,
                pattern_rhythm=0.10, color_harmony=0.08, gestalt=0.03),
            SceneType.UNKNOWN: cls()
        }
        return weights.get(scene_type, cls())
