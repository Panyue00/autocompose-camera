"""
AutoCompose Camera — 专业自动构图相机 APP
基于 Kivy 框架，Python 编写，Buildozer 打包为 Android APK
"""

import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.clock import Clock

from ui.screens.camera_screen import CameraScreen
from ui.screens.gallery_screen import GalleryScreen
from ui.screens.edit_screen import EditScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.portrait_screen import PortraitScreen


class AutoComposeApp(App):
    title = "AutoCompose"

    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(CameraScreen(name="camera"))
        sm.add_widget(GalleryScreen(name="gallery"))
        sm.add_widget(EditScreen(name="edit"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(PortraitScreen(name="portrait"))
        return sm


if __name__ == "__main__":
    AutoComposeApp().run()
