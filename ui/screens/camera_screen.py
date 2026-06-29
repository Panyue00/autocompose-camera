"""主相机取景器界面 — Kivy Camera + 构图叠加 + 快门"""

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock

from core.camera.camera_manager import CameraManager
from core.composition import CompositionEngine
from ui.widgets.composition_overlay import CompositionOverlay, update_overlay_lines


class CameraScreen(Screen):
    """相机主界面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = CameraManager()
        self.engine = CompositionEngine()
        self._analyzing = False
        self._frame_count = 0

        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        # 取景器
        self.camera_view = Camera(
            play=False,
            resolution=(1920, 1080),
            allow_stretch=True,
            keep_ratio=False
        )
        root.add_widget(self.camera_view)

        # 构图叠加层
        self.overlay = CompositionOverlay(mode="thirds")
        root.add_widget(self.overlay)

        # 顶部栏
        top_bar = BoxLayout(
            size_hint=(1, None), height=50,
            pos_hint={"top": 1},
            padding=(10, 5), spacing=10
        )
        score_label = Label(
            text="--",
            color=(1, 0.84, 0, 1),  # 金色
            size_hint=(None, 1), width=80,
            font_size=18
        )
        self.score_label = score_label
        top_bar.add_widget(Label(size_hint=(1, 1)))  # 占位
        top_bar.add_widget(score_label)
        root.add_widget(top_bar)

        # 底部控制栏
        bottom_bar = BoxLayout(
            size_hint=(1, None), height=120,
            pos_hint={"bottom": 1},
            padding=(20, 10), spacing=15
        )

        gallery_btn = Button(
            text="相册", size_hint=(0.2, 1),
            background_color=(0.2, 0.2, 0.2, 0.8)
        )
        gallery_btn.bind(on_release=self._open_gallery)
        bottom_bar.add_widget(gallery_btn)

        # 快门按钮 (圆形)
        shutter_btn = Button(
            size_hint=(0.15, 0.7),
            background_normal="",
            background_color=(1, 1, 1, 0.9)
        )
        shutter_btn.bind(on_release=self._capture)
        bottom_bar.add_widget(shutter_btn)

        switch_btn = Button(
            text="↺", size_hint=(0.2, 1),
            background_color=(0.2, 0.2, 0.2, 0.8)
        )
        switch_btn.bind(on_release=self._switch_camera)
        bottom_bar.add_widget(switch_btn)

        root.add_widget(bottom_bar)

        # 构图引导文字提示
        self.guide_label = Label(
            text="",
            color=(1, 1, 1, 0.8),
            size_hint=(1, None), height=30,
            pos_hint={"y": 0.18},
            font_size=13
        )
        root.add_widget(self.guide_label)

        self.add_widget(root)

    def on_enter(self):
        """进入相机界面"""
        self.camera.bind_widget(self.camera_view)
        # 每5帧分析一次构图
        Clock.schedule_interval(self._analyze_frame, 1.0 / 30.0)

    def on_leave(self):
        """离开相机界面"""
        Clock.unschedule(self._analyze_frame)
        self.camera.release()

    def _analyze_frame(self, dt):
        """分析当前帧的构图"""
        self._frame_count += 1
        if self._frame_count % 5 != 0 or self._analyzing:
            return

        frame = self.camera.get_frame()
        if frame is None:
            return

        self._analyzing = True
        try:
            result = self.engine.evaluate_live(frame)
            if result is not None:
                self.score_label.text = f"{result.total_score:.0f}"
                self.overlay.score = result.total_score
                self._update_guide(result)
            else:
                self.score_label.text = "--"
        except Exception:
            self.score_label.text = "--"
        finally:
            self._analyzing = False

    def _update_guide(self, result):
        """更新构图引导提示"""
        top_rule = max(result.rule_scores, key=result.rule_scores.get)
        hints = {
            "rule_of_thirds": "主体靠近三分线交点会更佳",
            "golden_ratio": "尝试将主体放在黄金螺旋收敛点",
            "leading_lines": "利用场景中的线条引导视线",
            "symmetry": "对称构图让画面更稳定",
            "negative_space": "多留些呼吸空间",
        }
        self.guide_label.text = hints.get(top_rule, "")

    def _capture(self, instance):
        """拍照"""
        path = self.camera.capture()
        if path:
            self.guide_label.text = "已保存！"
            Clock.schedule_once(lambda dt: setattr(self.guide_label, "text", ""), 2)

    def _switch_camera(self, instance):
        """切换前后摄"""
        self.camera.switch_camera()

    def _open_gallery(self, instance):
        """打开相册"""
        self.manager.current = "gallery"
