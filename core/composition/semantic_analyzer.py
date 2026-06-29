"""场景语义分析器 — 调度 ML 模型做语义/深度/显著性/主体检测"""

import numpy as np
from .models import SceneUnderstanding, SceneType


class SemanticAnalyzer:
    """场景语义分析器 — 组合各 ML 模型结果"""

    def __init__(self):
        self._seg_model = None    # DeepLabV3
        self._depth_model = None  # MiDaS
        self._saliency_model = None  # BASNet
        self._detector = None     # YOLO
        self._classifier = None   # EfficientNet scene classifier
        self._available = False

    def set_models(self, seg=None, depth=None, saliency=None, detector=None, classifier=None):
        """注入 ML 模型 (支持渐进式加载)"""
        self._seg_model = seg
        self._depth_model = depth
        self._saliency_model = saliency
        self._detector = detector
        self._classifier = classifier
        self._available = any([seg, depth, saliency, detector])

    @property
    def available(self) -> bool:
        return self._available

    def analyze(self, image: np.ndarray, fast_mode: bool = False) -> SceneUnderstanding:
        """分析图片，返回场景语义理解结果"""
        result = SceneUnderstanding()

        # 场景分类 (最快，总要先跑)
        if self._classifier is not None:
            result.scene_type = self._classifier.predict(image)
        else:
            result.scene_type = self._fallback_scene_classify(image)

        if fast_mode:
            # 实时预览模式: 仅主体检测
            if self._detector is not None:
                result.subject_boxes = self._detector.detect(image)
            return result

        # 全量分析模式
        if self._seg_model is not None:
            result.segmentation_mask = self._seg_model.predict(image)

        if self._depth_model is not None:
            result.depth_map = self._depth_model.predict(image)

        if self._saliency_model is not None:
            result.saliency_map = self._saliency_model.predict(image)

        if self._detector is not None:
            result.subject_boxes = self._detector.detect(image)
        else:
            result.subject_boxes = self._fallback_subject_detect(image)

        return result

    def _fallback_scene_classify(self, image: np.ndarray) -> SceneType:
        """无模型时的场景分类 fallback: 基于颜色/对比度启发式"""
        gray = np.mean(image, axis=2).astype(np.float32)
        h, w = gray.shape

        # 亮度分布
        brightness = np.mean(gray)
        contrast = np.std(gray)

        # 色温估计 (R vs B)
        r_mean = np.mean(image[:, :, 0])
        b_mean = np.mean(image[:, :, 2])
        warmth = r_mean - b_mean

        # 启发式判断
        if contrast < 30:
            return SceneType.MACRO  # 低对比度 → 可能是微距/柔焦
        elif brightness > 180 and warmth > 20:
            return SceneType.LANDSCAPE  # 亮+暖 → 风光
        elif 80 < brightness < 150 and contrast > 50:
            return SceneType.STREET
        elif warmth < -10:
            return SceneType.PORTRAIT  # 偏冷 → 可能人像
        else:
            return SceneType.UNKNOWN

    def _fallback_subject_detect(self, image: np.ndarray) -> list:
        """无 YOLO 时的简单主体检测: 基于显著性 + 中心偏置"""
        gray = np.mean(image, axis=2).astype(np.float32)
        h, w = gray.shape
        # 中心偏置高斯权重
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        gauss = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * (min(w, h) / 4) ** 2))
        weighted = gray * gauss
        cy, cx = np.unravel_index(weighted.argmax(), weighted.shape)
        # 简单估一个 1/3 画面大小的框
        bw, bh = int(w * 0.25), int(h * 0.25)
        return [(cx - bw, cy - bh, bw * 2, bh * 2, "subject", 0.5)]
