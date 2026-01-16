#!/bin/bash

# ZenAi Backend Service Deployment Script
# Deploys ZenAi as a standalone API service on EC2
# Usage: ./deploy.sh [IP_ADDRESS]
# Example: ./deploy.sh 51.21.54.93

set -e

# Default configuration
DEFAULT_IP="51.21.54.93"
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

print_step "2. Syncing database from server"
# Create local data directory if it doesn't exist
mkdir -p data

# Check if database exists on server
print_info "Checking for existing database on server..."
if ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" "[ -f /opt/zenai/data/zenai.db ]" 2>/dev/null; then
    print_info "Database found on server, downloading..."
    
    # Backup local database if it exists
    if [ -f "data/zenai.db" ]; then
        BACKUP_NAME="data/zenai.db.backup.$(date +%Y%m%d_%H%M%S)"
        cp "data/zenai.db" "$BACKUP_NAME"
        print_info "Local database backed up to: $BACKUP_NAME"
    fi
    
    # Download database from server
    if scp -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS:/opt/zenai/data/zenai.db" "data/zenai.db"; then
        print_success "Database synced from server"
        
        # Show database info
        if command -v sqlite3 &> /dev/null; then
            RECORD_COUNT=$(sqlite3 data/zenai.db "SELECT COUNT(*) FROM resonance_records;" 2>/dev/null || echo "N/A")
            print_info "Database contains $RECORD_COUNT resonance records"
        fi
    else
        print_warn "Failed to download database, will use local version if available"
    fi
else
    print_info "No database found on server (this is normal for first deployment)"
    if [ -f "data/zenai.db" ]; then
        print_info "Will use existing local database"
    else
        print_info "A new database will be created on first use"
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
ssh -i "$SSH_KEY" $SSH_OPTIONS "$SSH_USER@$IP_ADDRESS" << 'ENDSSH'
set -e

echo "==> Checking Nginx installation"
if ! command -v nginx &> /dev/null; then
    echo "==> Installing Nginx"
    sudo yum install -y nginx
    sudo systemctl enable nginx
fi

echo "==> Configuring ZenAi API proxy in Nginx"
# Create or update Nginx configuration for zenheart website with ZenAi API integration
sudo tee /etc/nginx/conf.d/zenheart.conf > /dev/null << 'EOF'
# ZenAi API backend
upstream zenai_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name _;
    
    # Root directory for zenheart website
    root /var/www/zenheart;
    index index.html;
    
    # ZenAi API endpoints - proxy to backend service
    location /api/ {
        proxy_pass http://zenai_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # CORS headers for API
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    
    # Static website files
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Additional static file handling
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

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
echo "  - Website: http://$IP_ADDRESS/ (zenheart)"
echo "  - API Base: http://$IP_ADDRESS/api/ (ZenAi)"
echo "  - Internal API: http://localhost:8000 (on server)"
echo ""
echo "API Endpoints:"
echo "  - POST http://$IP_ADDRESS/api/chat - Send message to ZenAi"
echo "  - POST http://$IP_ADDRESS/api/feedback - Submit feedback"
echo "  - GET http://$IP_ADDRESS/api/status - Get system status"
echo "  - GET http://$IP_ADDRESS/api/metrics - Get current metrics"
echo "  - GET http://$IP_ADDRESS/api/health - Health check"
echo "  - GET http://$IP_ADDRESS/api/docs - API documentation"
echo ""
echo "Next Steps:"
echo "  1. Deploy zenheart website files to /var/www/zenheart/"
echo "  2. Test website at: http://$IP_ADDRESS/"
echo "  3. Website can call API at: http://$IP_ADDRESS/api/"
echo ""
echo "Useful Commands:"
echo "  - Check ZenAi: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo systemctl status zenai'"
echo "  - Check Nginx: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo systemctl status nginx'"
echo "  - View API logs: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo journalctl -u zenai -f'"
echo "  - View Nginx logs: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo tail -f /var/log/nginx/access.log'"
echo "  - Restart ZenAi: ssh -i $SSH_KEY $SSH_USER@$IP_ADDRESS 'sudo systemctl restart zenai'"
echo ""
print_info "To update ZenAi service, run this script again: ./deploy_ec2.sh"
