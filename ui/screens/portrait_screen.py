"""人像模式界面"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.metrics import dp


class PortraitScreen(Screen):
    """人像虚化模式"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        top = BoxLayout(
            size_hint=(1, None), height=dp(50),
            pos_hint={"top": 1}, padding=(dp(10), dp(5)), spacing=dp(10)
        )
        back = Button(text="← 相机", size_hint=(None, 1), width=dp(80),
                     background_color=(0.2, 0.2, 0.2, 0.8))
        back.bind(on_release=lambda x: setattr(self.manager, "current", "camera"))
        top.add_widget(back)
        top.add_widget(Label(text="人像", size_hint=(1, 1), color=(1, 1, 1, 0.9)))
        root.add_widget(top)

        # 控制区
        controls = BoxLayout(
            orientation="vertical",
            size_hint=(1, 0.35), pos_hint={"bottom": 1},
            padding=(dp(15), dp(5)), spacing=dp(8)
        )

        # 光圈滑块
        aperture_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        aperture_row.add_widget(Label(text="光圈", size_hint=(0.2, 1), color=(1, 1, 1, 0.8)))
        self.aperture_label = Label(text="f/2.8", size_hint=(0.15, 1), color=(1, 0.84, 0, 0.9))
        aperture_row.add_widget(self.aperture_label)
        slider = Slider(min=1, max=16, value=2.8, step=0.1, size_hint=(0.65, 1))
        slider.bind(value=lambda s, v: self._on_aperture(v))
        aperture_row.add_widget(slider)
        controls.add_widget(aperture_row)

        # 光斑形状
        bokeh_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        bokeh_row.add_widget(Label(text="光斑", size_hint=(0.2, 1), color=(1, 1, 1, 0.8)))
        for shape in ["圆形", "六角", "八角"]:
            btn = Button(text=shape, size_hint=(1, 1), font_size=10,
                        background_color=(0.15, 0.15, 0.15, 0.9))
            bokeh_row.add_widget(btn)
        controls.add_widget(bokeh_row)

        # 应用按钮
        apply_btn = Button(text="拍摄人像", size_hint_y=None, height=dp(45),
                          background_color=(0.2, 0.5, 0.8, 0.8),
                          on_release=lambda x: self._capture_portrait())
        controls.add_widget(apply_btn)

        root.add_widget(controls)
        self.add_widget(root)

    def _on_aperture(self, value):
        f_stops = {1: 1.4, 2: 2.0, 3: 2.8, 4: 4.0, 5: 5.6, 6: 8.0, 7: 11.0, 8: 16.0}
        nearest = min(f_stops.keys(), key=lambda k: abs(k - value))
        f_val = f_stops.get(nearest, 2.8)
        self.aperture_label.text = f"f/{f_val}"

    def _capture_portrait(self):
        """拍照 + 虚化处理"""
        from kivy.app import App
        app = App.get_running_app()
        camera_screen = app.root.get_screen("camera")
        path = camera_screen.camera.capture()
        if path:
            # 在编辑界面中打开并自动应用虚化
            edit_screen = app.root.get_screen("edit")
            edit_screen.load_photo(path)
            app.root.current = "edit"
