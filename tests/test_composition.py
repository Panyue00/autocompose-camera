"""构图规则单元测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.composition.models import (
    CompositionCandidate, SceneUnderstanding, GeomStructure,
    Line2D, VanishingPoint, SymmetryAxis, SceneType
)
from core.composition.rules import ALL_RULES


def make_candidate(x=0, y=0, w=800, h=600):
    return CompositionCandidate(x=x, y=y, width=w, height=h, aspect_ratio=w/h)


def make_basic_scene():
    scene = SceneUnderstanding()
    scene.scene_type = SceneType.LANDSCAPE
    scene.subject_boxes = [(300, 200, 200, 200, "subject", 0.9)]
    scene.saliency_map = np.ones((600, 800), dtype=np.float32) * 0.1
    # 主体区域高显著性
    scene.saliency_map[200:400, 300:500] = 0.8
    return scene


def make_basic_geom():
    geom = GeomStructure()
    # 添加一条从右下到主体的引导线
    geom.leading_lines = [
        Line2D(x1=700, y1=500, x2=400, y2=300, saliency=0.7)
    ]
    geom.horizon_y = 300
    return geom


def test_rule_of_thirds():
    rule = next(r for r in ALL_RULES if r.name == "rule_of_thirds")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  rule_of_thirds: {score:.3f}")


def test_golden_ratio():
    rule = next(r for r in ALL_RULES if r.name == "golden_ratio")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  golden_ratio: {score:.3f}")


def test_leading_lines():
    rule = next(r for r in ALL_RULES if r.name == "leading_lines")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  leading_lines: {score:.3f}")


def test_symmetry():
    rule = next(r for r in ALL_RULES if r.name == "symmetry")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = GeomStructure()
    geom.symmetry_axes = [
        SymmetryAxis(x1=400, y1=0, x2=400, y2=600, strength=0.8, axis_type="vertical")
    ]
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  symmetry: {score:.3f}")


def test_negative_space():
    rule = next(r for r in ALL_RULES if r.name == "negative_space")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  negative_space: {score:.3f}")


def test_visual_balance():
    rule = next(r for r in ALL_RULES if r.name == "visual_balance")
    candidate = make_candidate()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    score = rule.score(candidate, scene, geom, image)
    assert 0 <= score <= 1, f"Score {score} out of range"
    print(f"  visual_balance: {score:.3f}")


def test_candidate_generator():
    from core.composition.candidate_generator import CandidateGenerator
    gen = CandidateGenerator()
    scene = make_basic_scene()

    candidates = gen.generate(800, 600, scene)
    assert len(candidates) > 0, "No candidates generated"
    assert len(candidates) <= 400, f"Too many candidates: {len(candidates)}"
    print(f"  candidates: {len(candidates)} generated")

    # 检查边界
    for c in candidates:
        assert c.x >= 0, f"c.x={c.x} < 0"
        assert c.y >= 0, f"c.y={c.y} < 0"
        assert c.x + c.width <= 800, f"crop extends beyond image width"
        assert c.y + c.height <= 600, f"crop extends beyond image height"


def test_scorer():
    from core.composition.candidate_generator import CandidateGenerator
    from core.composition.scorer import Scorer

    gen = CandidateGenerator()
    scorer = Scorer()
    scene = make_basic_scene()
    geom = make_basic_geom()
    image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    candidates = gen.generate(800, 600, scene)
    results = scorer.score_candidates(candidates, scene, geom, image, top_k=3)

    assert len(results) <= 3, f"Expected <=3 results, got {len(results)}"
    assert all(0 <= r.total_score <= 1 for r in results), "Scores out of range"

    # Top-1 应该比 Top-3 分高
    if len(results) >= 3:
        assert results[0].total_score >= results[-1].total_score

    print(f"  scorer: {len(results)} results, top score={results[0].total_score:.3f}")


if __name__ == "__main__":
    print("Testing composition rules...")
    test_rule_of_thirds()
    test_golden_ratio()
    test_leading_lines()
    test_symmetry()
    test_negative_space()
    test_visual_balance()
    test_candidate_generator()
    test_scorer()
    print("\n✓ All tests passed!")
