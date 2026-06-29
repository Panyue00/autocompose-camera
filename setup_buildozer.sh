#!/bin/bash
# AutoCompose Camera — WSL Buildozer 一键安装脚本
# 在 WSL Ubuntu-22.04 中执行: bash setup_buildozer.sh

set -e

echo "=== 1. 系统依赖 ==="
sudo apt update
sudo apt install -y python3-pip python3-dev build-essential git \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev \
    openjdk-17-jdk

echo "=== 2. Buildozer + Cython ==="
pip3 install --user buildozer cython==0.29.37

echo "=== 3. 验证 ==="
buildozer --version

echo ""
echo "=== 安装完成 ==="
echo "下一步: cd /mnt/c/Users/panyue/AppData/Local/Reasonix/autocompose-camera"
echo "        buildozer android debug"
