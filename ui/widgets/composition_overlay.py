"""取景器叠加层 — 在相机预览上绘制构图引导线"""

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, ListProperty


class CompositionOverlay(Widget):
    """Canvas 叠加层 — 绘制构图参考线"""

    score = NumericProperty(0)
    mode = StringProperty("thirds")  # thirds / golden / all / off
    rule_lines = ListProperty([])    # [(x1, y1, x2, y2, r, g, b, a), ...]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update, size=self._update,
                  score=self._update, mode=self._update)

    def _update(self, *args):
        self.canvas.clear()
        if self.mode == "off":
            return
        self._draw_grid()
        self._draw_rule_lines()
        self._draw_score()

    def _draw_grid(self):
        """绘制三分线网格"""
        w, h = self.width, self.height
        with self.canvas:
            # 三分线
            Color(1, 1, 1, 0.3)
            for i in [1/3, 2/3]:
                Line(points=[w * i, 0, w * i, h], width=1, dash_length=8, dash_offset=4)
                Line(points=[0, h * i, w, h * i], width=1, dash_length=8, dash_offset=4)

            # 三分交点高亮
            if self.score >= 75:
                Color(1.0, 0.84, 0.0, 0.5)  # 金色
                r = min(w, h) * 0.02
                for ix in [1/3, 2/3]:
                    for iy in [1/3, 2/3]:
                        Ellipse(pos=(w * ix - r, h * iy - r), size=(2 * r, 2 * r))

    def _draw_rule_lines(self):
        """绘制检测到的引导线"""
        if not self.rule_lines:
            return
        with self.canvas:
            for (x1, y1, x2, y2, r, g, b, a) in self.rule_lines:
                Color(r, g, b, a)
                Line(points=[x1, y1, x2, y2], width=2, dash_length=4, dash_offset=2)

    def _draw_score(self):
        """右上角构图评分"""
        w, h = self.width, self.height
        if self.score > 0:
            from kivy.graphics import Label as GLabel
            # 用 Rectangle + 文字 (Kivy 需要在 kv 中定义 Label)
            pass  # 评分通过 kv 文件中的 Label 显示


def update_overlay_lines(overlay: CompositionOverlay,
                         geom_structure,
                         image_w: int, image_h: int,
                         overlay_w: float, overlay_h: float):
    """更新叠加层上的引导线坐标 (将图像坐标映射到 overlay 坐标)"""
    lines = []
    scale_x = overlay_w / image_w
    scale_y = overlay_h / image_h

    for line in geom_structure.leading_lines:
        lines.append((
            line.x1 * scale_x, line.y1 * scale_y,
            line.x2 * scale_x, line.y2 * scale_y,
            0.3, 0.7, 1.0, line.saliency * 0.6  # 蓝色半透明
        ))

    overlay.rule_lines = lines
