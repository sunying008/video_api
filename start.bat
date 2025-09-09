@echo off
echo 启动YouTube视频解析API服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查是否在正确目录
if not exist app.py (
    echo 错误: 未找到app.py，请确保在video_api目录下运行此脚本
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 警告: 依赖安装可能有问题，继续启动服务...
)

echo.
echo 启动服务中...
echo 服务地址: http://localhost:8002
echo API文档: http://localhost:8002/docs
echo 按 Ctrl+C 停止服务
echo.

REM 启动服务
python app.py

pause