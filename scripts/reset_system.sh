#!/bin/bash
# ZenAi System Reset Script / ZenAi 系统复位脚本
#
# WARNING: This script will DELETE ALL DATA and reset the system to initial state.
# 警告：此脚本将删除所有数据并将系统重置为初始状态。

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "ZenAi System Reset / ZenAi 系统复位"
echo "========================================"
echo ""

# Get project directory (go up one level from scripts/)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Check if database exists
DB_PATH="${DB_PATH:-data/zenai.db}"
BACKUP_DIR="backups"

echo -e "${YELLOW}Warning / 警告:${NC}"
echo "This will DELETE the following:"
echo "以下内容将被删除："
echo ""
echo "  1. Database file / 数据库文件: $DB_PATH"
echo "  2. All interactions / 所有交互记录"
echo "  3. All iterations / 所有迭代记录"
echo "  4. All prompt history / 所有提示词历史"
echo "  5. All metrics / 所有指标数据"
echo "  6. Report files (optional) / 报告文件（可选）"
echo ""
echo -e "${RED}THIS CANNOT BE UNDONE! / 此操作无法撤销！${NC}"
echo ""

# Ask for confirmation
read -p "Type 'RESET' to confirm / 输入 'RESET' 确认: " confirm

if [ "$confirm" != "RESET" ]; then
    echo ""
    echo "Reset cancelled / 已取消复位"
    echo ""
    exit 0
fi

echo ""
echo "========================================"
echo "Starting reset process / 开始复位流程"
echo "========================================"
echo ""

# Step 1: Create backup if database exists
if [ -f "$DB_PATH" ]; then
    echo "Step 1: Creating backup / 步骤 1: 创建备份"
    
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/zenai_backup_$TIMESTAMP.db"
    
    cp "$DB_PATH" "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} Database backed up to: $BACKUP_FILE"
    echo "  数据库已备份到: $BACKUP_FILE"
    echo ""
else
    echo "Step 1: No database found, skipping backup"
    echo "步骤 1: 未找到数据库，跳过备份"
    echo ""
fi

# Step 2: Stop running services
echo "Step 2: Checking for running services / 步骤 2: 检查运行中的服务"

# Find processes using port 8000
PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo -e "${YELLOW}Warning: Found process(es) using port 8000${NC}"
    echo "警告：发现使用端口 8000 的进程"
    read -p "Kill these processes? (y/n) / 终止这些进程？(y/n): " kill_confirm
    
    if [ "$kill_confirm" = "y" ] || [ "$kill_confirm" = "Y" ]; then
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Processes terminated / 进程已终止"
    else
        echo -e "${YELLOW}⚠${NC} Please stop the service manually before reset"
        echo "请在复位前手动停止服务"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} No running services found / 未发现运行中的服务"
fi
echo ""

# Step 3: Delete database
echo "Step 3: Removing database / 步骤 3: 删除数据库"
if [ -f "$DB_PATH" ]; then
    rm -f "$DB_PATH"
    echo -e "${GREEN}✓${NC} Database removed / 数据库已删除"
else
    echo "  No database to remove / 无数据库需删除"
fi
echo ""

# Step 4: Clean report files (optional)
echo "Step 4: Cleaning report files / 步骤 4: 清理报告文件"
read -p "Delete all report files in reports/? (y/n) / 删除 reports/ 中的所有报告？(y/n): " clean_reports

if [ "$clean_reports" = "y" ] || [ "$clean_reports" = "Y" ]; then
    if [ -d "reports" ]; then
        # Backup reports before deleting
        if [ -n "$(ls -A reports/ 2>/dev/null)" ]; then
            REPORT_BACKUP="$BACKUP_DIR/reports_backup_$TIMESTAMP"
            mkdir -p "$REPORT_BACKUP"
            cp -r reports/* "$REPORT_BACKUP/" 2>/dev/null || true
            echo "  Reports backed up to: $REPORT_BACKUP"
            echo "  报告已备份到: $REPORT_BACKUP"
        fi
        
        rm -rf reports/*
        echo -e "${GREEN}✓${NC} Report files removed / 报告文件已删除"
    else
        echo "  No reports directory found / 未找到报告目录"
    fi
else
    echo "  Keeping report files / 保留报告文件"
fi
echo ""

# Step 5: Recreate data directory
echo "Step 5: Recreating data directory / 步骤 5: 重建数据目录"
mkdir -p data
echo -e "${GREEN}✓${NC} Data directory ready / 数据目录已就绪"
echo ""

# Step 6: Initialize new database (optional)
echo "Step 6: Initialize new database? / 步骤 6: 初始化新数据库？"
read -p "Start the system to initialize? (y/n) / 启动系统进行初始化？(y/n): " init_db

if [ "$init_db" = "y" ] || [ "$init_db" = "Y" ]; then
    echo ""
    echo "Initializing database / 初始化数据库..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: Virtual environment not found${NC}"
        echo "错误：未找到虚拟环境"
        echo "Please run: python3.11 -m venv venv"
        echo "请运行：python3.11 -m venv venv"
        exit 1
    fi
    
    # Start system briefly to initialize database
    echo "Starting system for initialization / 启动系统以初始化..."
    ./venv/bin/python -m src.main --no-scheduler &
    PID=$!
    
    # Wait for initialization
    sleep 5
    
    # Stop the system
    kill $PID 2>/dev/null || true
    sleep 2
    
    if [ -f "$DB_PATH" ]; then
        echo -e "${GREEN}✓${NC} Database initialized / 数据库已初始化"
    else
        echo -e "${YELLOW}⚠${NC} Database not created, may need manual start"
        echo "数据库未创建，可能需要手动启动"
    fi
else
    echo "  Skipping initialization / 跳过初始化"
    echo "  The database will be created on first system start"
    echo "  数据库将在首次启动系统时创建"
fi
echo ""

# Summary
echo "========================================"
echo "Reset Complete / 复位完成"
echo "========================================"
echo ""
echo -e "${GREEN}✓${NC} System has been reset to initial state"
echo "  系统已重置为初始状态"
echo ""

if [ -n "$BACKUP_FILE" ]; then
    echo "Backup location / 备份位置:"
    echo "  Database: $BACKUP_FILE"
    if [ -d "$REPORT_BACKUP" ]; then
        echo "  Reports: $REPORT_BACKUP"
    fi
    echo ""
fi

echo "Next steps / 后续步骤:"
echo "  1. Start the system / 启动系统:"
echo "     ./venv/bin/python -m src.main --no-scheduler"
echo ""
echo "  2. Check status / 检查状态:"
echo "     ./venv/bin/python -m src.admin status"
echo ""
echo "  3. Run tests / 运行测试:"
echo "     ./venv/bin/python test_chat.py \"你好\""
echo ""
echo "========================================"
echo ""
