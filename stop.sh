#!/bin/bash
#
# ZenAI Service Stop Script
# AI 对话服务停止脚本
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
PID_FILE="zen_ai.pid"

echo -e "${YELLOW}Stopping $SERVICE_NAME Service...${NC}"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}✗ PID file not found. Service may not be running.${NC}"
    
    # Try to find and stop any running zen_ai process
    PIDS=$(pgrep -f "python.*src.main" || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}⚠ Found running zen_ai process(es), stopping...${NC}"
        echo "$PIDS" | xargs kill 2>/dev/null || true
        sleep 2
        echo -e "${GREEN}✓ Process(es) stopped${NC}"
    fi
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Service not running (PID $PID not found)${NC}"
    rm "$PID_FILE"
    exit 0
fi

# Send SIGTERM for graceful shutdown
echo -e "${YELLOW}Sending SIGTERM to PID $PID...${NC}"
kill $PID

# Wait for graceful shutdown (up to 10 seconds)
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Force kill if still running
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Process still running, force killing...${NC}"
    kill -9 $PID
    sleep 1
fi

rm "$PID_FILE"

echo -e "${GREEN}✓ $SERVICE_NAME stopped${NC}"
