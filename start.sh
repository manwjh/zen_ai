#!/bin/bash
#
# ZenAI Service Startup Script (Production)
# AI 对话服务启动脚本（生产环境）
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SERVICE_NAME="ZenAI"
PORT=8000
PID_FILE="zen_ai.pid"
LOG_FILE="logs/zen_ai.log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Starting $SERVICE_NAME Service${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Service already running (PID: $PID)${NC}"
        echo -e "${YELLOW}  Stop it first with: ./stop.sh${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ Removing stale PID file${NC}"
        rm "$PID_FILE"
    fi
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}Please copy env.example to .env and configure LLM credentials${NC}"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Create directories
mkdir -p data logs

# Start service (with scheduler enabled by default)
echo -e "${YELLOW}🚀 Starting service on port $PORT...${NC}"

nohup python3 -m src.main \
    --host 0.0.0.0 \
    --port $PORT \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

# Wait a moment and check if it's running
sleep 3
if ps -p $PID > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  $SERVICE_NAME Started Successfully${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "📊 Service Info:"
    echo -e "   PID:  $PID"
    echo -e "   Port: $PORT"
    echo -e "   URL:  http://localhost:$PORT"
    echo ""
    echo -e "📚 API Documentation:"
    echo -e "   Health: http://localhost:$PORT/health"
    echo -e "   Docs:   http://localhost:$PORT/docs (if available)"
    echo ""
    echo -e "📝 Logs: tail -f $LOG_FILE"
    echo -e "🛑 Stop: ./stop.sh"
    echo ""
    echo -e "${YELLOW}Note: Scheduler is enabled for automatic prompt evolution${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to start service${NC}"
    echo -e "${RED}   Check logs: tail -20 $LOG_FILE${NC}"
    rm "$PID_FILE"
    exit 1
fi
