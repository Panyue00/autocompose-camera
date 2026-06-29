"""设置界面"""

from kivy.uix.screen import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp


class SettingsScreen(Screen):
    """设置"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        top = BoxLayout(
            size_hint=(1, None), height=dp(50),
            pos_hint={"top": 1}, padding=(dp(10), dp(5))
        )
        back = Button(text="← 返回", size_hint=(None, 1), width=dp(80),
                     background_color=(0.2, 0.2, 0.2, 0.8))
        back.bind(on_release=lambda x: setattr(self.manager, "current", "camera"))
        top.add_widget(back)
        top.add_widget(Label(text="设置", size_hint=(1, 1), color=(1, 1, 1, 0.9)))
        root.add_widget(top)

        scroll = ScrollView(size_hint=(1, 0.9), pos_hint={"y": 0})
        content = BoxLayout(orientation="vertical", size_hint_y=None,
                           spacing=dp(4), padding=(dp(15), dp(5)))
        content.bind(minimum_height=content.setter("height"))

        settings = [
            ("构图引导模式", ["仅视觉", "视觉+震动", "全部"]),
            ("引导详细度", ["简洁", "标准", "专业"]),
            ("构图风格偏好", ["均衡", "风光", "人像", "街拍"]),
            ("默认画幅", ["4:3", "16:9", "1:1", "3:2"]),
            ("JPEG 质量", ["85%", "95%", "100%"]),
            ("云端增强", ["仅离线", "WiFi", "始终"]),
        ]

        for name, options in settings:
            row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
            row.add_widget(Label(text=name, size_hint=(0.35, 1),
                                color=(1, 1, 1, 0.8), font_size=13))
            for opt in options:
                btn = Button(text=opt, size_hint=(1, 1), font_size=11,
                            background_color=(0.15, 0.15, 0.15, 0.9))
                row.add_widget(btn)
            content.add_widget(row)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)
