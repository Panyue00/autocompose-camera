[app]
title = AutoCompose Camera
package.name = autocompose
package.domain = com.autocompose
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,tflite,json
version = 0.1.0
requirements = python3,kivy>=2.3.1,opencv-python,numpy,Pillow,requests,google-generativeai
orientation = portrait
fullscreen = 1
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,INTERNET
android.api = 30
android.minapi = 26
android.ndk = 26d
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
