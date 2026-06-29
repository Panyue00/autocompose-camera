"""编辑界面 — 自动构图裁剪 + 透视矫正 + 调色"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock

from core.composition import CompositionEngine, Explainer
from core.editing.edit_pipeline import EditPipeline


class EditScreen(Screen):
    """照片编辑 — 构图裁剪 + 调色"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = CompositionEngine()
        self.explainer = Explainer()
        self.pipeline = EditPipeline()
        self.photo_path = None
        self.results = []
        self.current_result_idx = 0
        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        # 顶部
        top = BoxLayout(
            size_hint=(1, None), height=dp(50),
            pos_hint={"top": 1}, padding=(dp(10), dp(5)), spacing=dp(10)
        )
        back = Button(text="← 返回", size_hint=(None, 1), width=dp(80),
                     background_color=(0.2, 0.2, 0.2, 0.8))
        back.bind(on_release=lambda x: setattr(self.manager, "current", "gallery"))
        top.add_widget(back)
        self.title_label = Label(text="编辑", size_hint=(1, 1), color=(1, 1, 1, 0.9))
        top.add_widget(self.title_label)
        top.add_widget(Button(text="保存", size_hint=(None, 1), width=dp(70),
                              background_color=(0.2, 0.6, 0.3, 0.8),
                              on_release=lambda x: self._save()))
        root.add_widget(top)

        # 图片预览
        self.image_view = Image(
            size_hint=(1, 0.65),
            pos_hint={"top": 0.92},
            allow_stretch=True, keep_ratio=True
        )
        root.add_widget(self.image_view)

        # 构图说明
        self.explanation = Label(
            text="",
            size_hint=(1, None), height=dp(60),
            pos_hint={"top": 0.28},
            color=(1, 1, 1, 0.85),
            font_size=12, halign="left", valign="top",
            padding=(dp(10), dp(5))
        )
        root.add_widget(self.explanation)

        # 方案选择器
        self.result_selector = BoxLayout(
            size_hint=(1, None), height=dp(60),
            pos_hint={"top": 0.22}, spacing=dp(10), padding=(dp(10), dp(5))
        )
        for i in range(3):
            btn = Button(
                text=f"方案{i+1}",
                size_hint=(1, 1),
                background_color=(0.15, 0.15, 0.15, 0.9)
            )
            idx = i
            btn.bind(on_release=lambda _, n=idx: self._select_result(n))
            self.result_selector.add_widget(btn)
        root.add_widget(self.result_selector)

        # 底部操作
        bottom = BoxLayout(
            size_hint=(1, None), height=dp(50),
            pos_hint={"bottom": 1}, spacing=dp(5), padding=(dp(10), dp(5))
        )
        bottom.add_widget(Button(text="应用裁剪", size_hint=(1, 1),
                                 background_color=(0.2, 0.5, 0.8, 0.8),
                                 on_release=lambda x: self._apply_crop()))
        bottom.add_widget(Button(text="透视矫正", size_hint=(1, 1),
                                 background_color=(0.3, 0.3, 0.3, 0.8),
                                 on_release=lambda x: self._auto_perspective()))
        bottom.add_widget(Button(text="调色+", size_hint=(1, 1),
                                 background_color=(0.3, 0.3, 0.3, 0.8),
                                 on_release=lambda x: self._auto_enhance()))
        bottom.add_widget(Button(text="撤销", size_hint=(1, 1),
                                 background_color=(0.4, 0.2, 0.2, 0.8),
                                 on_release=lambda x: self._undo()))
        root.add_widget(bottom)

        self.add_widget(root)

    def load_photo(self, path: str):
        """加载照片并运行构图分析"""
        self.photo_path = path
        self.image_view.source = path

        # 加载图片分析
        from core.storage.photo_repo import PhotoRepository
        repo = PhotoRepository()
        image = repo.load_image(path)
        if image is None:
            return
        self.pipeline.load(image)

        # 异步运行构图分析
        Clock.schedule_once(lambda dt: self._run_composition(image))

    def _run_composition(self, image):
        """运行构图分析"""
        self.title_label.text = "分析中..."
        try:
            import numpy as np
            small = image
            if max(image.shape[:2]) > 1024:
                from core.cv.image_utils import resize_to_fit
                small = resize_to_fit(image, 1024)
            self.results = self.engine.evaluate(small)
            self.current_result_idx = 0
            self._show_result(0)
            self.title_label.text = "编辑"
        except Exception as e:
            self.title_label.text = f"分析失败: {e}"

    def _show_result(self, idx: int):
        """显示指定构图方案"""
        if idx >= len(self.results):
            return
        self.current_result_idx = idx
        result = self.results[idx]

        # 更新裁剪预览 (通过图片坐标偏移模拟)
        exp = self.explainer.explain(result)
        self.explanation.text = exp

        # 高亮选中的方案按钮
        for i, child in enumerate(self.result_selector.children):
            if isinstance(child, Button):
                child.background_color = (
                    (0.2, 0.5, 0.8, 0.9) if i == idx else (0.15, 0.15, 0.15, 0.9)
                )

    def _select_result(self, idx: int):
        self._show_result(idx)

    def _apply_crop(self):
        """应用当前选中的裁剪方案"""
        if not self.results:
            return
        result = self.results[self.current_result_idx]
        c = result.candidate
        self.pipeline.apply_crop(c.x, c.y, c.width, c.height)
        self._refresh_preview()

    def _auto_perspective(self):
        """自动透视矫正"""
        pass  # 后续实现

    def _auto_enhance(self):
        """自动增强色彩"""
        self.pipeline.apply_color(brightness=0.05, contrast=1.1, saturation=1.15)
        self._refresh_preview()

    def _undo(self):
        """撤销"""
        if self.pipeline.undo():
            self._refresh_preview()

    def _refresh_preview(self):
        """刷新预览"""
        import os
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp_path = tmp.name
        self.pipeline.save(tmp_path)
        self.image_view.source = tmp_path
        self.image_view.reload()

    def _save(self):
        """保存编辑结果"""
        if self.photo_path:
            self.pipeline.save(self.photo_path)
        self.manager.current = "gallery"
