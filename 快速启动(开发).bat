@echo off
chcp 65001 >nul
title 电子标签多条码识别系统 - 开发模式

echo ========================================================================
echo                电子标签多条码识别系统 - 开发模式启动
echo ========================================================================
echo.

REM 检查依赖
echo 检查Python依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo ✅ 依赖检查完成
echo.

REM 启动后端
echo 启动后端服务...
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================================================
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
