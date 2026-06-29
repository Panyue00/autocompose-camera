"""相册界面"""

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp


class GalleryScreen(Screen):
    """相册 — 浏览已拍照片"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = FloatLayout()

        # 顶部
        top = BoxLayout(
            size_hint=(1, None), height=dp(50),
            pos_hint={"top": 1}, padding=(dp(10), dp(5)),
            spacing=dp(10)
        )
        back = Button(text="← 相机", size_hint=(None, 1), width=dp(80),
                     background_color=(0.2, 0.2, 0.2, 0.8))
        back.bind(on_release=lambda x: setattr(self.manager, "current", "camera"))
        top.add_widget(back)
        top.add_widget(Label(text="相册", size_hint=(1, 1), color=(1, 1, 1, 0.9)))
        root.add_widget(top)

        # 照片网格
        scroll = ScrollView(
            size_hint=(1, None), height=root.height - dp(60),
            pos_hint={"y": 0}
        )
        self.grid = GridLayout(cols=3, spacing=dp(4), padding=dp(4),
                               size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self):
        """进入时加载照片"""
        self._load_photos()

    def _load_photos(self):
        """从存储中加载照片缩略图"""
        self.grid.clear_widgets()
        try:
            from core.storage.photo_repo import PhotoRepository
            repo = PhotoRepository()
            photos = repo.list_photos()
        except Exception:
            photos = []

        for photo in photos[::-1]:  # 最新的在前
            thumb = Image(
                source=photo.path,
                size_hint_y=None, height=dp(120),
                allow_stretch=True, keep_ratio=False
            )
            score_text = f"{photo.score:.0f}" if photo.score > 0 else "--"
            label = Label(
                text=score_text,
                size_hint_y=None, height=dp(20),
                color=(1, 0.84, 0, 1), font_size=11
            )
            box = BoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(140))
            box.add_widget(thumb)
            box.add_widget(label)
            box.bind(on_touch_down=lambda _, t, p=photo: self._open_photo(p))
            self.grid.add_widget(box)

    def _open_photo(self, photo):
        """打开照片编辑页"""
        screen = self.manager.get_screen("edit")
        screen.load_photo(photo.path)
        self.manager.current = "edit"
