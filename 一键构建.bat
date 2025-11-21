@echo off
chcp 65001 >nul
title 电子标签多条码识别系统 - Windows构建工具

echo ========================================================================
echo                电子标签多条码识别系统 - Windows构建工具
echo ========================================================================
echo.

REM 检查Python
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.10或更高版本
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM 检查Node.js
echo [2/4] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Node.js，请先安装Node.js 18或更高版本
    echo    下载地址: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM 安装依赖
echo [3/4] 安装构建依赖...
echo 正在安装Python构建工具...
pip install -r build_requirements.txt
if errorlevel 1 (
    echo ❌ 安装构建依赖失败
    pause
    exit /b 1
)
echo ✅ 构建依赖安装完成
echo.

REM 执行构建
echo [4/4] 开始构建...
echo ========================================================================
python build_windows.py
if errorlevel 1 (
    echo.
    echo ❌ 构建失败！
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo 🎉 构建成功！
echo ========================================================================
echo.
echo 📦 发布包位置: release\LabelScan_Windows_v1.0.0.zip
echo 📂 程序目录: dist\LabelScan\
echo.
echo 后续步骤:
echo   1. 将发布包复制到目标机器并解压
echo   2. 安装Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki)
echo   3. 配置config\system.yaml中的Tesseract路径
echo   4. 双击start.bat启动系统
echo.
pause
