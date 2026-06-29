# WSL 打包指南

## 前置: 安装 WSL

在 Windows PowerShell (管理员) 中执行:
```
wsl --install -d Ubuntu-22.04
```
重启电脑, 然后从开始菜单打开 "Ubuntu 22.04"

---

## 第1步: 安装 Buildozer

在 Ubuntu 终端中:
```bash
sudo apt update
sudo apt install -y python3-pip python3-dev git openjdk-17-jdk \
    autoconf libtool cmake libffi-dev libssl-dev

pip3 install --user buildozer cython==0.29.37
```

---

## 第2步: 把项目复制到 WSL 内

Buildozer 在 Windows 路径 (/mnt/c/...) 下会有权限问题, 必须复制到 Linux 文件系统:

```bash
# 复制项目到 WSL 家目录
cp -r /mnt/c/Users/panyue/AppData/Local/Reasonix/autocompose-camera ~/autocompose-camera
cd ~/autocompose-camera
```

---

## 第3步: 打包

```bash
buildozer android debug
```

第一次需要下载 Android SDK/NDK (~30分钟), 之后每次 3-5 分钟。

APK 产物在 `~/autocompose-camera/bin/` 下, 文件名为 `autocompose-0.1.0-debug.apk`。

---

## 第4步: 安装到手机

```bash
# 复制 APK 回 Windows 桌面
cp ~/autocompose-camera/bin/*.apk /mnt/c/Users/panyue/Desktop/

# 用 USB 传手机, 或直接 adb 安装:
# adb install ~/autocompose-camera/bin/autocompose-0.1.0-debug.apk
```
