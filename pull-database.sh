#!/bin/bash

# ==========================================
# ZenHeart 数据库拉取脚本
# ==========================================
#
# 功能：从远程服务器拉取数据库到本地
#
# 用法：./pull-database.sh [IP地址]
# 示例：
#   ./pull-database.sh              # 使用默认IP
#   ./pull-database.sh 51.21.54.93  # 指定IP地址

set -e

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default configuration
DEFAULT_IP="51.21.54.93"
SSH_USER="ec2-user"
SSH_KEY="$HOME/.ssh/id_rsa"
SSH_OPTIONS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
REMOTE_DB_PATH="/opt/zenai/data/zenai.db"
LOCAL_DATA_DIR="data"
LOCAL_DB_PATH="$LOCAL_DATA_DIR/zenai.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
}

# Validate IP address
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Get database info
get_db_info() {
    local db_path=$1
    if [ ! -f "$db_path" ]; then
        echo "不存在"
        return
    fi
    
    if ! command -v sqlite3 &> /dev/null; then
        echo "存在（无法读取详情，请安装sqlite3）"
        return
    fi
    
    local record_count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM resonance_records;" 2>/dev/null || echo "N/A")
    local file_size=$(du -h "$db_path" | cut -f1)
    local mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$db_path" 2>/dev/null || stat -c "%y" "$db_path" 2>/dev/null | cut -d'.' -f1)
    
    echo "存在 | 记录数: $record_count | 大小: $file_size | 修改时间: $mod_time"
}

print_header "ZenHeart 数据库拉取工具"

# Determine IP address to use
if [ -n "$1" ]; then
    IP_ADDRESS="$1"
    print_info "使用指定的IP地址: $IP_ADDRESS"
    
    if ! validate_ip "$IP_ADDRESS"; then
        print_error "无效的IP地址格式: $IP_ADDRESS"
        exit 1
    fi
else
    IP_ADDRESS="$DEFAULT_IP"
    print_info "使用默认IP地址: $IP_ADDRESS"
fi

echo ""
print_info "远程服务器: $SSH_USER@$IP_ADDRESS"
print_info "远程数据库: $REMOTE_DB_PATH"
print_info "本地数据库: $LOCAL_DB_PATH"
echo ""

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    print_error "SSH密钥文件不存在: $SSH_KEY"
    exit 1
fi

# Test SSH connection
print_info "测试SSH连接..."
if ! ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" 'echo "连接成功"' > /dev/null 2>&1; then
    print_error "SSH连接失败，请检查："
    echo "  1. EC2实例正在运行"
    echo "  2. 安全组允许SSH（端口22）"
    echo "  3. IP地址正确: $IP_ADDRESS"
    echo "  4. SSH密钥正确: $SSH_KEY"
    exit 1
fi
print_success "SSH连接正常"
echo ""

# Check remote database exists
print_info "检查远程数据库..."
if ! ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" "[ -f $REMOTE_DB_PATH ]" 2>/dev/null; then
    print_error "远程服务器上不存在数据库文件: $REMOTE_DB_PATH"
    print_info "可能原因："
    echo "  1. 后端服务尚未部署"
    echo "  2. 数据库尚未创建（尚未有用户交互）"
    echo "  3. 数据库路径不正确"
    exit 1
fi

# Get remote database info
print_info "远程数据库信息..."
REMOTE_INFO=$(ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" << 'EOF'
if command -v sqlite3 &> /dev/null; then
    RECORD_COUNT=$(sqlite3 /opt/zenai/data/zenai.db "SELECT COUNT(*) FROM resonance_records;" 2>/dev/null || echo "N/A")
    echo "记录数: $RECORD_COUNT"
fi
FILE_SIZE=$(du -h /opt/zenai/data/zenai.db | cut -f1)
echo "大小: $FILE_SIZE"
MOD_TIME=$(stat -c "%y" /opt/zenai/data/zenai.db 2>/dev/null | cut -d'.' -f1)
echo "修改时间: $MOD_TIME"
EOF
)

echo "$REMOTE_INFO" | while read line; do
    echo "  $line"
done
echo ""

# Create local data directory if it doesn't exist
mkdir -p "$LOCAL_DATA_DIR"

# Backup local database if it exists
if [ -f "$LOCAL_DB_PATH" ]; then
    print_warn "本地数据库已存在"
    print_info "本地数据库信息: $(get_db_info "$LOCAL_DB_PATH")"
    echo ""
    
    BACKUP_NAME="$LOCAL_DATA_DIR/zenai.db.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "正在备份本地数据库..."
    cp "$LOCAL_DB_PATH" "$BACKUP_NAME"
    print_success "本地数据库已备份到: $BACKUP_NAME"
    echo ""
fi

# Download database from server
print_info "正在从远程服务器下载数据库..."
if scp -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS:$REMOTE_DB_PATH" "$LOCAL_DB_PATH"; then
    print_success "数据库下载成功！"
else
    print_error "数据库下载失败"
    exit 1
fi

echo ""
print_header "拉取完成！"

# Show updated local database info
print_info "更新后的本地数据库信息:"
LOCAL_INFO=$(get_db_info "$LOCAL_DB_PATH")
echo "  $LOCAL_INFO"
echo ""

# List recent backups
BACKUP_COUNT=$(ls -1 "$LOCAL_DATA_DIR"/zenai.db.backup.* 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt 0 ]; then
    print_info "最近的备份文件（共 $BACKUP_COUNT 个）:"
    ls -lht "$LOCAL_DATA_DIR"/zenai.db.backup.* 2>/dev/null | head -5 | awk '{print "  " $9 " (" $6 " " $7 " " $8 ")"}'
    echo ""
fi

print_info "数据库位置: $LOCAL_DB_PATH"
print_success "可以开始使用本地数据库进行开发了！"
echo ""

# Suggest cleanup if too many backups
if [ "$BACKUP_COUNT" -gt 10 ]; then
    print_warn "检测到超过10个备份文件，建议清理旧备份："
    echo "  ls -lt $LOCAL_DATA_DIR/zenai.db.backup.* | tail -n +6 | awk '{print \$9}' | xargs rm"
    echo ""
fi

print_info "其他有用的命令："
echo "  查看数据库: sqlite3 $LOCAL_DB_PATH"
echo "  查看表结构: sqlite3 $LOCAL_DB_PATH '.schema'"
echo "  查看记录数: sqlite3 $LOCAL_DB_PATH 'SELECT COUNT(*) FROM resonance_records;'"
echo "  恢复备份: cp $LOCAL_DATA_DIR/zenai.db.backup.YYYYMMDD_HHMMSS $LOCAL_DB_PATH"
