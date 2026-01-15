#!/bin/bash
# ZenAi Quick Start Script / ZenAi 快速启动脚本

set -e

echo "========================================"
echo "ZenAi System Quick Start"
echo "ZenAi 系统快速启动"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python 3 not found!"; exit 1; }

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "警告：.env 文件不存在！"
    echo "Copying env.example to .env..."
    cp env.example .env
    echo "Please edit .env with your LLM credentials before starting."
    echo "请在启动前编辑 .env 填入你的 LLM 凭证。"
    exit 1
fi

# Create data directory
mkdir -p data

echo ""
echo "========================================"
echo "Setup complete! / 设置完成！"
echo "========================================"
echo ""
echo "Choose an option / 选择一个选项:"
echo "1) Start full system (API + Scheduler)"
echo "   启动完整系统（API + 调度器）"
echo "2) Start API only (no automatic iterations)"
echo "   仅启动 API（无自动迭代）"
echo "3) Check system status"
echo "   检查系统状态"
echo "4) Exit"
echo "   退出"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Starting ZenAi full system..."
        python3 -m src.main
        ;;
    2)
        echo "Starting ZenAi API only..."
        python3 -m src.main --no-scheduler
        ;;
    3)
        echo "Checking system status..."
        python3 -m src.admin status
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
