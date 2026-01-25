#!/bin/bash

# ==========================================
# ZenHeart 后端部署脚本 (Backend Deployment)
# ==========================================
#
# 功能：部署 ZenAi API 服务到 EC2
# 
# 部署内容：
#   • ZenAi 后端服务 → /opt/zenai/
#   • Systemd 自动启动服务（端口 8000）
#   • Nginx 反向代理配置（/api/ → localhost:8000）
#   • 网站根目录设置（/var/www/zenheart）
#
# ⚠️ 部署顺序：
#   1. 先运行本脚本（部署后端 API）
#   2. 再运行 ../deploy-frontend.sh（部署前端）
#   或直接使用 ../deploy-all.sh（一键部署）
#
# 用法：./deploy-backend.sh [IP地址] [域名]
# 示例：
#   ./deploy-backend.sh 51.21.54.93
#   ./deploy-backend.sh 51.21.54.93 zenheart.net

set -e

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default configuration
DEFAULT_IP="51.21.54.93"
DEFAULT_DOMAIN="zenheart.net"
SSH_USER="ec2-user"
SSH_KEY="$HOME/.ssh/id_rsa"
SSH_OPTIONS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Service configuration
SERVICE_NAME="zenai"
SERVICE_PORT=8000
DEPLOY_DIR="/opt/zenai"
PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
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

# Determine IP address to use
if [ -n "$1" ]; then
    IP_ADDRESS="$1"
    print_info "Using specified IP address: $IP_ADDRESS"
    
    if ! validate_ip "$IP_ADDRESS"; then
        print_error "Invalid IP address format: $IP_ADDRESS"
        exit 1
    fi
else
    IP_ADDRESS="$DEFAULT_IP"
    print_info "No IP specified, using default: $IP_ADDRESS"
fi

# Determine domain to use
if [ -n "$2" ]; then
    DOMAIN="$2"
    print_info "Using specified domain: $DOMAIN"
else
    DOMAIN="$DEFAULT_DOMAIN"
    print_info "No domain specified, using default: $DOMAIN"
fi

# Check SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    print_error "SSH key file not found: $SSH_KEY"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it from env.example"
    print_info "Run: cp env.example .env"
    print_info "Then edit .env with your actual configuration"
    exit 1
fi

print_step "1. Testing SSH connection"
if ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" 'echo "Connection successful"' > /dev/null 2>&1; then
    print_success "SSH connection established"
else
    print_error "SSH connection failed. Please check:"
    echo "  1. EC2 instance is running"
    echo "  2. Security group allows SSH (port 22)"
    echo "  3. IP address is correct: $IP_ADDRESS"
    echo "  4. SSH key is correct: $SSH_KEY"
    exit 1
fi

print_step "2. Handling database"
# Create local data directory if it doesn't exist
mkdir -p data

# Check if database exists on server
print_info "Checking for existing database on server..."
REMOTE_DB_EXISTS=false
if ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" "[ -f /opt/zenai/data/zenai.db ]" 2>/dev/null; then
    REMOTE_DB_EXISTS=true
fi

if [ "$REMOTE_DB_EXISTS" = true ]; then
    print_info "远程数据库存在"
    
    if [ -f "data/zenai.db" ]; then
        # 本地也有数据库，询问用户
        echo ""
        echo "检测到本地和远程都有数据库。"
        echo ""
        echo "选项："
        echo "  1) 使用本地数据库（覆盖远程）"
        echo "  2) 保留远程数据库（不上传）"
        echo "  3) 下载远程数据库到本地（覆盖本地）"
        echo ""
        read -p "请选择 [1/2/3]: " -n 1 -r choice
        echo ""
        
        case $choice in
            1)
                print_info "将上传本地数据库"
                # 数据库将在后面的deployment package中包含
                ;;
            2)
                print_info "保留远程数据库，不上传本地数据库"
                # 从deployment package中移除数据库
                rm -rf data/zenai.db
                ;;
            3)
                print_info "下载远程数据库..."
                if [ -f "data/zenai.db" ]; then
                    BACKUP_NAME="data/zenai.db.backup.$(date +%Y%m%d_%H%M%S)"
                    cp "data/zenai.db" "$BACKUP_NAME"
                    print_info "本地数据库已备份: $BACKUP_NAME"
                fi
                
                if scp -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS:/opt/zenai/data/zenai.db" "data/zenai.db"; then
                    print_success "远程数据库已下载"
                    if command -v sqlite3 &> /dev/null; then
                        RECORD_COUNT=$(sqlite3 data/zenai.db "SELECT COUNT(*) FROM interactions;" 2>/dev/null || echo "N/A")
                        print_info "数据库包含 $RECORD_COUNT 条交互记录"
                    fi
                else
                    print_error "下载失败"
                    exit 1
                fi
                # 从deployment package中移除，使用远程的
                rm -rf data/zenai.db
                ;;
            *)
                print_error "无效选择"
                exit 1
                ;;
        esac
    else
        print_info "本地无数据库，将保留远程数据库"
    fi
else
    print_info "远程无数据库（首次部署正常）"
    if [ -f "data/zenai.db" ]; then
        print_info "将使用本地数据库"
    else
        print_info "首次使用时将自动创建数据库"
    fi
fi

print_step "3. Preparing deployment package"
# Create temporary deployment directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

print_info "Creating deployment package in $TEMP_DIR"

# Copy project files
cp -r src "$TEMP_DIR/"
cp -r scripts "$TEMP_DIR/"
cp -r docs "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp config.yml "$TEMP_DIR/"
cp .env "$TEMP_DIR/_env"
cp start.sh "$TEMP_DIR/"

# Copy database if it exists
if [ -d "data" ]; then
    cp -r data "$TEMP_DIR/"
    print_info "Database included in deployment package"
fi

# Create deployment archive
cd "$TEMP_DIR"
tar -czf zenai-deploy.tar.gz *
cd - > /dev/null

print_success "Deployment package created"

print_step "4. Uploading files to EC2"
scp -i "$SSH_KEY" $SSH_OPTIONS "$TEMP_DIR/zenai-deploy.tar.gz" "$SSH_USER@$IP_ADDRESS:~/"
print_success "Files uploaded"

print_step "5. Installing dependencies and configuring service"
ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" << 'ENDSSH'
set -e

echo "==> Installing system dependencies"
sudo yum update -y
sudo yum install -y python3.11 python3.11-pip git

echo "==> Creating deployment directory"
sudo mkdir -p /opt/zenai
sudo mkdir -p /opt/zenai/data
sudo chown -R ec2-user:ec2-user /opt/zenai

echo "==> Backing up existing database (if any)"
if [ -f "/opt/zenai/data/zenai.db" ]; then
    BACKUP_NAME="/opt/zenai/data/zenai.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp /opt/zenai/data/zenai.db "$BACKUP_NAME"
    echo "✓ Database backed up to: $BACKUP_NAME"
fi

echo "==> Extracting deployment package"
cd /opt/zenai
tar -xzf ~/zenai-deploy.tar.gz
rm ~/zenai-deploy.tar.gz

echo "==> Ensuring data directory exists"
mkdir -p /opt/zenai/data

echo "==> Setting up environment file"
if [ -f "/opt/zenai/_env" ]; then
    mv /opt/zenai/_env /opt/zenai/.env
    chmod 600 /opt/zenai/.env
    echo "✓ Environment file configured"
else
    echo "✗ Environment file not found in deployment package"
    exit 1
fi

echo "==> Installing Python dependencies"
python3.11 -m pip install --user --upgrade pip
python3.11 -m pip install --user -r requirements.txt

echo "==> Creating systemd service"
sudo tee /etc/systemd/system/zenai.service > /dev/null << 'EOF'
[Unit]
Description=ZenAi API Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/zenai
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/zenai/.env
ExecStart=/usr/bin/python3.11 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=zenai

[Install]
WantedBy=multi-user.target
EOF

echo "==> Reloading systemd daemon"
sudo systemctl daemon-reload

echo "==> Stopping existing service (if running)"
sudo systemctl stop zenai 2>/dev/null || true

echo "==> Starting ZenAi service"
sudo systemctl start zenai
sudo systemctl enable zenai

echo "==> Waiting for service to start"
sleep 3

echo "==> Checking service status"
if sudo systemctl is-active --quiet zenai; then
    echo "✓ ZenAi service is running"
    sudo systemctl status zenai --no-pager
else
    echo "✗ ZenAi service failed to start"
    echo "==> Service logs:"
    sudo journalctl -u zenai -n 50 --no-pager
    exit 1
fi

ENDSSH

if [ $? -ne 0 ]; then
    print_error "Deployment failed during installation"
    exit 1
fi

print_step "6. Configuring Nginx for API integration"
ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" bash -s "$DOMAIN" "$SSH_USER" "$IP_ADDRESS" << 'ENDSSH'
set -e
DOMAIN="$1"
SSH_USER="$2"
IP_ADDRESS="$3"

echo "==> Checking Nginx installation"
if ! command -v nginx &> /dev/null; then
    echo "==> Installing Nginx"
    sudo yum install -y nginx
    sudo systemctl enable nginx
fi

echo "==> Configuring ZenAi API proxy in Nginx"

# Check if configuration already exists with SSL
if [ -f /etc/nginx/conf.d/zenheart.conf ] && grep -q "ssl_certificate" /etc/nginx/conf.d/zenheart.conf; then
    echo "  ℹ Existing HTTPS configuration detected"
    
    # Test if nginx config is valid
    if ! sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "  ✗ Nginx 配置文件损坏！"
        echo ""
        echo "  建议修复方案："
        echo "  1. 删除损坏的配置文件："
        echo "     ssh $SSH_USER@$IP_ADDRESS 'sudo rm /etc/nginx/conf.d/zenheart.conf'"
        echo ""
        echo "  2. 重新运行完整部署："
        echo "     ./deploy-all.sh $IP_ADDRESS $DOMAIN"
        echo ""
        echo "  或手动修复配置文件："
        echo "     ssh $SSH_USER@$IP_ADDRESS"
        echo "     sudo nano /etc/nginx/conf.d/zenheart.conf"
        echo ""
        exit 1
    fi
    
    echo "  ✓ Nginx 配置测试通过"
    echo "  ✓ Skipping Nginx reconfiguration to preserve SSL settings"
    echo "  ℹ To reconfigure, manually edit /etc/nginx/conf.d/zenheart.conf or delete it and redeploy"
    
    # Only verify that upstream is defined
    if ! grep -q "upstream zenai_backend" /etc/nginx/conf.d/zenheart.conf; then
        echo "  ⚠️  WARNING: upstream zenai_backend not found in config"
        echo "  ⚠️  API proxy may not work correctly"
    else
        echo "  ✓ ZenAi API upstream configuration exists"
    fi
else
    echo "  → Creating new Nginx configuration (HTTP only)"
    echo "  ℹ To add HTTPS later, run: deploy-frontend.sh with --ssl flag"
    
    # Create or update Nginx configuration for zenheart website with ZenAi API integration
    sudo tee /etc/nginx/conf.d/zenheart.conf > /dev/null << NGINX_EOF
# ZenAi API backend
upstream zenai_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Root directory for zenheart website
    root /var/www/zenheart;
    index index.html;
    
    # Charset
    charset utf-8;
    
    # ZenAi API endpoints - proxy to backend service
    location /api/ {
        proxy_pass http://zenai_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # CORS headers for API
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if (\$request_method = OPTIONS) {
            return 204;
        }
    }
    
    # JavaScript files - explicit MIME type for mobile compatibility
    location ~* \.js\$ {
        add_header Content-Type "application/javascript; charset=utf-8" always;
        add_header Cache-Control "public, max-age=2592000" always;
    }
    
    # CSS files - explicit MIME type
    location ~* \.css\$ {
        add_header Content-Type "text/css; charset=utf-8" always;
        add_header Cache-Control "public, max-age=2592000" always;
    }
    
    # Static website files
    location / {
        try_files \$uri \$uri/ =404;
    }
    
    # Additional static file handling
    location ~* \.(jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot|mp3)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF
fi

echo "==> Testing Nginx configuration"
sudo nginx -t

echo "==> Restarting Nginx"
sudo systemctl restart nginx

echo "==> Checking Nginx status"
if sudo systemctl is-active --quiet nginx; then
    echo "✓ Nginx is running and configured"
else
    echo "✗ Nginx failed to start"
    exit 1
fi

ENDSSH

if [ $? -ne 0 ]; then
    print_error "Nginx configuration failed"
    exit 1
fi

print_step "7. Verifying deployment"
sleep 2

# Test internal API endpoint
print_info "Testing internal API (localhost:8000)..."
ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" 'curl -s http://localhost:8000/health' > /tmp/zenai_health_internal.json 2>/dev/null

if [ $? -eq 0 ] && [ -s /tmp/zenai_health_internal.json ]; then
    print_success "Internal API health check passed"
    echo ""
    print_info "Internal API Response:"
    cat /tmp/zenai_health_internal.json | python3 -m json.tool 2>/dev/null || cat /tmp/zenai_health_internal.json
    echo ""
    rm -f /tmp/zenai_health_internal.json
else
    print_warn "Internal API check failed"
fi

# Test external API endpoint through Nginx
print_info "Testing external API access (http://$IP_ADDRESS/api/)..."
if curl -s -f "http://$IP_ADDRESS/api/health" > /tmp/zenai_health_external.json 2>/dev/null; then
    print_success "External API health check passed"
    echo ""
    print_info "External API Response:"
    cat /tmp/zenai_health_external.json | python3 -m json.tool 2>/dev/null || cat /tmp/zenai_health_external.json
    echo ""
    rm -f /tmp/zenai_health_external.json
else
    print_warn "External API check failed. This is normal if website files are not deployed yet."
    print_info "The API is still accessible internally at localhost:8000"
fi

print_step "Deployment Complete!"
echo ""
print_success "ZenAi API service is deployed and running"
print_success "Nginx is configured to proxy API requests"
echo ""
echo "Service Information:"
echo "  - Server IP: $IP_ADDRESS"
echo "  - Domain: $DOMAIN"
echo "  - Website: http://$IP_ADDRESS/ or http://$DOMAIN/"
echo "  - API Base: http://$IP_ADDRESS/api/ or http://$DOMAIN/api/"
echo "  - Internal API: http://localhost:8000 (on server)"
echo ""
echo "API Endpoints:"
echo "  - POST http://$DOMAIN/api/chat - Send message to ZenAi"
echo "  - POST http://$DOMAIN/api/feedback - Submit feedback"
echo "  - GET http://$DOMAIN/api/status - Get system status"
echo "  - GET http://$DOMAIN/api/metrics - Get current metrics"
echo "  - GET http://$DOMAIN/api/health - Health check"
echo "  - GET http://$DOMAIN/api/docs - API documentation"
echo ""
echo "DNS Configuration Required:"
echo "  ⚠️  Please ensure DNS records are configured:"
echo "  1. A record: $DOMAIN → $IP_ADDRESS"
echo "  2. A record: www.$DOMAIN → $IP_ADDRESS"
echo "  (Check: dig +short $DOMAIN)"
echo ""
echo "Next Steps:"
echo "  1. Configure DNS records (if not done yet)"
echo "  2. Deploy zenheart website: cd .. && ./deploy-frontend.sh $IP_ADDRESS $DOMAIN"
echo "  3. (Optional) Configure SSL: cd .. && ./deploy-frontend.sh $IP_ADDRESS $DOMAIN your-email@example.com --ssl"
echo ""
echo "Useful Commands:"
echo "  - Check services: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo systemctl status zenai nginx'"
echo "  - View API logs: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo journalctl -u zenai -f'"
echo "  - View Nginx logs: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo tail -f /var/log/nginx/error.log'"
echo "  - Diagnose: ../scripts/diagnose-server.sh"
echo ""
print_info "部署脚本："
echo "  后端更新: ./deploy-backend.sh $IP_ADDRESS $DOMAIN"
echo "  前端部署: cd .. && ./deploy-frontend.sh $IP_ADDRESS $DOMAIN"
echo "  完整部署: cd .. && ./deploy-all.sh $IP_ADDRESS $DOMAIN"
