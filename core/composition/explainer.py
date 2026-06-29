"""构图可解释性 — 将评分分解为人类可读的说明"""

from .models import CompositionResult


class Explainer:
    """生成构图评分的自然语言解释"""

    RULE_DESCRIPTIONS = {
        "rule_of_thirds": "主体放置在三分线交点，画面更平衡",
        "golden_ratio": "主体遵循黄金螺旋布局，视觉流动自然",
        "leading_lines": "引导线将视线引向主体，增强纵深感",
        "symmetry": "对称构图营造庄重、稳定的氛围",
        "natural_framing": "前景元素形成天然画框，突出主体",
        "negative_space": "留白给主体呼吸空间，画面简洁有力",
        "visual_balance": "画面视觉重量均衡，观感舒适",
        "depth_layering": "前中后景层次分明，空间感强",
        "diagonals": "对角线构图带来动感和张力",
        "pattern_rhythm": "重复元素形成节奏感，引人入胜",
        "color_harmony": "色彩搭配协调，视觉效果愉悦",
        "gestalt": "元素组织符合视觉完形，整体统一",
    }

    def explain(self, result: CompositionResult) -> str:
        """生成构图的自然语言解释"""
        lines = [f"总评分: {result.total_score:.0f}/100"]
        lines.append("")

        # 按贡献度排序
        sorted_rules = sorted(
            result.rule_scores.items(),
            key=lambda x: x[1], reverse=True
        )

        for rule_name, score in sorted_rules:
            contribution = score * 100
            if contribution < 5:
                continue
            desc = self.RULE_DESCRIPTIONS.get(rule_name, rule_name)
            lines.append(f"· {desc} (+{contribution:.0f})")

        if result.aesthetic_score > 0:
            lines.append(f"· 神经网络美学评分 (+{result.aesthetic_score * 100:.0f})")

        return "\n".join(lines)

    def explain_brief(self, result: CompositionResult) -> str:
        """简短解释 — 顶部规则"""
        sorted_rules = sorted(
            result.rule_scores.items(),
            key=lambda x: x[1], reverse=True
        )
        top = sorted_rules[0] if sorted_rules else ("", 0)
        return f"{result.total_score:.0f}分 · {self.RULE_DESCRIPTIONS.get(top[0], '')}"
