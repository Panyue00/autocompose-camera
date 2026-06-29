[app]
title = AutoCompose Camera
package.name = autocompose
package.domain = com.autocompose
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,tflite,json
version = 0.1.0
requirements = python3,kivy==2.3.0,opencv-python==4.9.0.80,numpy==1.26.4,Pillow==10.3.0,requests==2.32.0,google-generativeai==0.7.0
orientation = portrait
fullscreen = 1
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,INTERNET
android.api = 30
android.minapi = 26
android.sdk = 30
android.ndk = 25c
android.arch = arm64-v8a, armeabi-v7a
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
