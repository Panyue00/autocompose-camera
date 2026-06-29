"""构图规则注册表"""

from .base import CompositionRule
from .rule_of_thirds import RuleOfThirds
from .golden_ratio import GoldenRatio
from .composition_rules_1 import LeadingLines, Symmetry, NaturalFraming
from .composition_rules_2 import NegativeSpace, VisualBalance, DepthLayering, Diagonals
from .composition_rules_3 import PatternRhythm, ColorHarmony, GestaltClosure


ALL_RULES: list[CompositionRule] = [
    RuleOfThirds(),
    GoldenRatio(),
    LeadingLines(),
    Symmetry(),
    NaturalFraming(),
    NegativeSpace(),
    VisualBalance(),
    DepthLayering(),
    Diagonals(),
    PatternRhythm(),
    ColorHarmony(),
    GestaltClosure(),
]


def get_rule_by_name(name: str) -> CompositionRule | None:
    for rule in ALL_RULES:
        if rule.name == name:
            return rule
    return None
