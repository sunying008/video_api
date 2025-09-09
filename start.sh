#!/bin/bash

echo "启动YouTube视频解析API服务..."
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否在正确目录
if [ ! -f "app.py" ]; then
    echo "错误: 未找到app.py，请确保在video_api目录下运行此脚本"
    exit 1
fi

# 安装依赖
echo "正在安装依赖包..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "警告: 依赖安装可能有问题，继续启动服务..."
fi

echo
echo "启动服务中..."
echo "服务地址: http://localhost:8002"
echo "API文档: http://localhost:8002/docs"
echo "按 Ctrl+C 停止服务"
echo

# 启动服务
python3 app.py