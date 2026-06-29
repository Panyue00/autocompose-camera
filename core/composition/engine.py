"""构图引擎 — 顶层调度器，串联全部分析 → 候选生成 → 评分管线"""

import numpy as np
from .models import CompositionResult, CompositionCandidate, SceneUnderstanding, GeomStructure
from .semantic_analyzer import SemanticAnalyzer
from .geometric_analyzer import GeometricAnalyzer
from .candidate_generator import CandidateGenerator
from .scorer import Scorer, FastScorer


class CompositionEngine:
    """构图引擎 — 拍照后全量分析"""

    def __init__(self):
        self.semantic = SemanticAnalyzer()
        self.geometric = GeometricAnalyzer()
        self.generator = CandidateGenerator()
        self.scorer = Scorer()
        self.fast_scorer = FastScorer()
        self._aesthetic_model = None

    def set_ml_models(self, seg=None, depth=None, saliency=None,
                      detector=None, classifier=None):
        """注入 ML 模型"""
        self.semantic.set_models(seg, depth, saliency, detector, classifier)

    def set_aesthetic_model(self, model):
        """注入美学评分模型 (NIMA/CPA)"""
        self._aesthetic_model = model

    def evaluate(self, image: np.ndarray) -> list[CompositionResult]:
        """
        对单张照片执行完整构图分析管线
        :param image: RGB uint8 图片 H×W×3
        :return: Top-3 构图方案
        """
        h, w = image.shape[:2]

        # 1. 场景语义分析 (全量)
        scene = self.semantic.analyze(image, fast_mode=False)

        # 2. 几何结构提取
        geom = self.geometric.analyze(image)

        # 3. 候选窗口生成
        candidates = self.generator.generate(w, h, scene)

        # 4. 快速预评分 → Top-50
        top_candidates = self.fast_scorer.pre_score(
            candidates, scene, geom, image, top_n=50
        )

        # 5. 精细评分 → Top-3 + 美学
        results = self.scorer.score_candidates(
            top_candidates, scene, geom, image,
            aesthetic_model=self._aesthetic_model, top_k=3
        )

        return results

    def evaluate_live(self, image: np.ndarray) -> CompositionResult | None:
        """
        实时预览模式 — 快速分析，仅返回最佳构图建议
        """
        h, w = image.shape[:2]

        # 快速语义 (仅主体检测)
        scene = self.semantic.analyze(image, fast_mode=True)

        # 几何分析
        geom = self.geometric.analyze(image)

        # 候选 + 快速评分
        candidates = self.generator.generate(w, h, scene)
        if not candidates:
            return None

        top_candidates = self.fast_scorer.pre_score(
            candidates, scene, geom, image, top_n=10
        )

        results = self.scorer.score_candidates(
            top_candidates, scene, geom, image,
            aesthetic_model=None, top_k=1
        )

        return results[0] if results else None
