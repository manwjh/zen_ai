# ZenAi Deployment Guide

## Overview

This guide describes how to deploy ZenAi as a standalone API service on AWS EC2. The deployment creates a systemd service that runs continuously and is accessible via HTTP API.

## Architecture

```
Internet → EC2:80 (Nginx) → 127.0.0.1:8000 (ZenAi API) → SQLite Database
```

- **Nginx**: Reverse proxy handling HTTP requests
- **ZenAi API**: FastAPI application running via Uvicorn
- **systemd**: Service manager ensuring ZenAi runs continuously
- **SQLite**: Local database for storing interactions and metrics

## Prerequisites

### Local Machine

1. **SSH Key**: Must have SSH key for EC2 access at `~/.ssh/id_rsa`
2. **Environment File**: Must create `.env` file with configuration
3. **Project Files**: Complete zen_ai project directory

### EC2 Instance

1. **Instance Type**: t2.micro or larger (t2.small recommended)
2. **AMI**: Amazon Linux 2023 (recommended) or Amazon Linux 2
3. **Security Group Rules**:
   - SSH (port 22): Your IP or 0.0.0.0/0
   - HTTP (port 80): 0.0.0.0/0
   - HTTPS (port 443): 0.0.0.0/0 (optional, for future SSL)

4. **Elastic IP**: Recommended for stable IP address
5. **Storage**: At least 8GB root volume

## Deployment Steps

### Step 1: Prepare Environment File

Create `.env` file from template:

```bash
cp env.example .env
```

Edit `.env` with your actual configuration:

```bash
ZENAI_LLM_PROVIDER=perfxcloud
ZENAI_LLM_API_KEY=your-actual-api-key-here
ZENAI_LLM_BASE_URL=https://deepseek.perfxlab.cn/v1
ZENAI_LLM_MODEL=Qwen3-Next-80B-Instruct
ZENAI_LLM_MAX_CONTEXT_TOKENS=128000
```

**Important**: Never commit `.env` file to git. Keep your API keys secure.

### Step 2: Run Deployment Script

Execute the deployment script with your EC2 IP address:

```bash
# Make script executable
chmod +x deploy.sh

# Deploy to EC2
./deploy.sh 51.21.54.93
```

Or use without IP parameter to use the default IP configured in the script:

```bash
./deploy.sh
```

### Step 3: Verify Deployment

The script will automatically verify the deployment. You should see:

```
Deployment Complete!
ZenAi API service is deployed and running
```

Test the API manually:

```bash
# Health check
curl http://YOUR_IP/health

# API root
curl http://YOUR_IP/api/

# API documentation (in browser)
open http://YOUR_IP/docs
```

## What the Deployment Script Does

The deployment script automates the following steps:

1. **Connection Test**: Verifies SSH access to EC2
2. **Package Creation**: Creates deployment archive with all necessary files
3. **File Upload**: Transfers files to EC2 via SCP
4. **System Setup**:
   - Installs Python 3.11
   - Installs Python dependencies
   - Creates deployment directory at `/opt/zenai`
5. **Service Configuration**:
   - Creates systemd service file
   - Configures service to start on boot
   - Starts ZenAi service
6. **Nginx Configuration**:
   - Installs Nginx if not present
   - Configures reverse proxy
   - Enables and starts Nginx
7. **Verification**: Tests API health endpoint

## Service Management

### Check Service Status

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl status zenai'
```

### View Service Logs

```bash
# Real-time logs
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo journalctl -u zenai -f'

# Last 100 lines
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo journalctl -u zenai -n 100'
```

### Restart Service

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl restart zenai'
```

### Stop Service

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl stop zenai'
```

### Start Service

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl start zenai'
```

## API Endpoints

Once deployed, the following endpoints are available:

### Base URL

```
http://YOUR_IP/api/
```

### Endpoints

#### 1. Chat with ZenAi

```bash
POST /api/chat

Request:
{
  "user_input": "Hello ZenAi",
  "metadata": {}
}

Response:
{
  "interaction_id": 1,
  "response_text": "...",
  "refusal": false,
  "prompt_version": 1,
  "timestamp": "2026-01-15T10:30:00"
}
```

#### 2. Submit Feedback

```bash
POST /api/feedback

Request:
{
  "interaction_id": 1,
  "feedback": "positive"
}

Response:
{
  "interaction_id": 1,
  "feedback": "positive",
  "recorded_at": "2026-01-15T10:30:05"
}
```

#### 3. Get System Status

```bash
GET /api/status

Response:
{
  "prompt_version": 1,
  "current_iteration_id": null,
  "frozen": false,
  "killed": false,
  "policy": {...},
  "total_interactions": 10,
  "total_iterations": 0
}
```

#### 4. Get Current Metrics

```bash
GET /api/metrics

Response:
{
  "iteration_id": null,
  "total_interactions": 10,
  "metrics": null
}
```

#### 5. Health Check

```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00"
}
```

## Directory Structure on EC2

```
/opt/zenai/
├── src/              # Application source code
├── scripts/          # Utility scripts
├── docs/             # Documentation
├── requirements.txt  # Python dependencies
├── config.yml        # System configuration
├── .env             # Environment variables (contains secrets)
├── start.sh         # Manual start script
└── data/            # Created at runtime
    └── zenai.db     # SQLite database
```

## Configuration Files

### systemd Service

Location: `/etc/systemd/system/zenai.service`

```ini
[Unit]
Description=ZenAi API Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/zenai
Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

Location: `/etc/nginx/conf.d/zenai.conf`

```nginx
upstream zenai_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://zenai_backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # ... more proxy settings ...
    }
}
```

## Updating the Service

To deploy updates:

1. Make changes to your local code
2. Run the deployment script again:

```bash
./deploy.sh
```

The script will:
- Upload new files
- Restart the service
- Verify the update

## Troubleshooting

### Service Won't Start

Check logs for errors:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo journalctl -u zenai -n 100 --no-pager'
```

Common issues:
- Missing environment variables in `.env`
- Python dependencies not installed
- Port 8000 already in use
- Database permissions

### Cannot Access API

1. **Check service is running**:
   ```bash
   ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl status zenai'
   ```

2. **Check Nginx is running**:
   ```bash
   ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl status nginx'
   ```

3. **Check security group**:
   - HTTP (port 80) must be open
   - Verify in AWS Console

4. **Test locally on EC2**:
   ```bash
   ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'curl http://localhost:8000/health'
   ```

### Database Errors

Check database file exists and has correct permissions:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'ls -la /opt/zenai/data/'
```

If database is corrupted, you can reset it:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'cd /opt/zenai && bash scripts/reset_system.sh'
```

### Configuration Issues

Verify configuration is loaded correctly:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'cat /opt/zenai/config.yml'
```

Check environment variables:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl show zenai --property=Environment'
```

## Security Considerations

### Protect Environment File

The `.env` file contains sensitive API keys. Ensure:

1. Never commit `.env` to version control
2. File permissions are restrictive on EC2:
   ```bash
   chmod 600 /opt/zenai/.env
   ```

### API Security

For production deployment:

1. **Add CORS restrictions** in `src/api/app.py`:
   ```python
   allow_origins=["https://your-domain.com"]
   ```

2. **Add authentication** for admin endpoints

3. **Enable HTTPS** using Let's Encrypt:
   ```bash
   sudo yum install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

4. **Rate limiting** via Nginx or application level

### Security Group

Restrict SSH access to your IP only:
- Type: SSH
- Port: 22
- Source: Your IP/32

## Monitoring

### Service Health

Monitor service uptime:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl is-active zenai'
```

### API Metrics

Use the `/api/metrics` endpoint to track:
- Total interactions
- Resonance metrics
- Iteration progress

### System Resources

Monitor CPU and memory:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'top -b -n 1 | head -20'
```

Check disk space:

```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'df -h'
```

## Backup and Recovery

### Database Backup

Backup the SQLite database:

```bash
# Download database
scp -i ~/.ssh/id_rsa ec2-user@YOUR_IP:/opt/zenai/data/zenai.db ./zenai-backup-$(date +%Y%m%d).db
```

### Configuration Backup

Backup configuration files:

```bash
scp -i ~/.ssh/id_rsa ec2-user@YOUR_IP:/opt/zenai/config.yml ./config-backup.yml
scp -i ~/.ssh/id_rsa ec2-user@YOUR_IP:/opt/zenai/.env ./.env-backup
```

### Restore

To restore from backup:

```bash
# Upload database
scp -i ~/.ssh/id_rsa ./zenai-backup.db ec2-user@YOUR_IP:/opt/zenai/data/zenai.db

# Restart service
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_IP 'sudo systemctl restart zenai'
```

## Integration with zenheart Website

Once deployed, integrate with your frontend:

```javascript
// Frontend API client
const ZENAI_API_BASE = 'http://YOUR_IP/api';

async function chatWithZenAi(userInput) {
  const response = await fetch(`${ZENAI_API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput })
  });
  return response.json();
}

async function submitFeedback(interactionId, feedback) {
  const response = await fetch(`${ZENAI_API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      interaction_id: interactionId, 
      feedback: feedback 
    })
  });
  return response.json();
}
```

## Next Steps

1. **Configure Domain**: Point your domain to EC2 IP
2. **Enable HTTPS**: Install SSL certificate
3. **Add Monitoring**: CloudWatch or external monitoring
4. **Implement Backups**: Automated database backups
5. **Add Logging**: Centralized log management
6. **Scale**: Consider RDS for database if needed

## Support

For issues or questions:
1. Check service logs first
2. Review this documentation
3. Check configuration files
4. Test endpoints manually

## Reference

- **Service Port**: 8000 (internal)
- **Public Port**: 80 (HTTP)
- **Service User**: ec2-user
- **Deployment Path**: /opt/zenai
- **Python Version**: 3.11
- **ASGI Server**: Uvicorn
