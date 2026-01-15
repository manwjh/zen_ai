# ZenAi EC2 Deployment Guide

## Quick Start

一键部署ZenAi到EC2服务器：

```bash
./deploy_ec2.sh
```

## 部署架构

```
Internet → EC2:80 (Nginx) → {
    /         → /var/www/zenheart (zenheart website)
    /api/*    → localhost:8000 (ZenAi API)
}
```

## 部署内容

部署脚本会自动完成以下操作：

1. **上传文件** - 将ZenAi项目打包上传到EC2
2. **安装依赖** - Python 3.11 + 所有依赖包
3. **配置服务** - systemd服务，开机自启
4. **配置Nginx** - 反向代理，集成到80端口
5. **验证部署** - 自动测试API是否正常

## 服务信息

- **服务器**: 51.21.54.93
- **ZenAi API**: http://51.21.54.93/api/
- **内部端口**: localhost:8000
- **网站目录**: /var/www/zenheart/

## API端点

所有API通过 `/api/` 前缀访问：

```bash
# 健康检查
GET http://51.21.54.93/api/health

# 聊天
POST http://51.21.54.93/api/chat
Content-Type: application/json
{"user_input": "你好"}

# 反馈
POST http://51.21.54.93/api/feedback
{"interaction_id": 1, "feedback": "positive"}

# 状态
GET http://51.21.54.93/api/status

# 指标
GET http://51.21.54.93/api/metrics

# API文档
GET http://51.21.54.93/api/docs
```

## zenheart网站集成

zenheart网站可以直接调用API：

```javascript
// 前端代码示例
const API_BASE = 'http://51.21.54.93/api';

async function chatWithZenAi(userInput) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput })
  });
  return response.json();
}
```

## 更新部署

修改代码后，只需重新运行部署脚本：

```bash
./deploy_ec2.sh
```

脚本会自动：
- 上传新代码
- 重启服务
- 验证部署

## 管理命令

### 查看服务状态

```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo systemctl status zenai'
```

### 查看实时日志

```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo journalctl -u zenai -f'
```

### 重启服务

```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo systemctl restart zenai'
```

### 检查Nginx配置

```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo nginx -t'
```

### 查看Nginx日志

```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo tail -f /var/log/nginx/access.log'
```

## 配置文件位置

- **ZenAi服务**: `/etc/systemd/system/zenai.service`
- **Nginx配置**: `/etc/nginx/conf.d/zenheart.conf`
- **项目目录**: `/opt/zenai/`
- **环境变量**: `/opt/zenai/.env`
- **数据库**: `/opt/zenai/data/zenai.db`

## 故障排查

### API无法访问

1. 检查ZenAi服务状态：
```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo systemctl status zenai'
```

2. 检查Nginx状态：
```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo systemctl status nginx'
```

3. 测试内部API：
```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'curl http://localhost:8000/health'
```

### 服务无法启动

查看详细日志：
```bash
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo journalctl -u zenai -n 100'
```

常见问题：
- 环境变量缺失 - 检查 `/opt/zenai/.env`
- 端口被占用 - 检查 `netstat -tlnp | grep 8000`
- 权限问题 - 检查文件所有者 `ls -la /opt/zenai/`

## 安全提醒

1. **.env文件** 包含敏感信息，确保：
   - 不要提交到git
   - 服务器上文件权限为600
   - 定期轮换API密钥

2. **SSH密钥** 保管好 `~/.ssh/id_rsa`

3. **EC2安全组** 确保配置正确：
   - 22端口：仅允许必要IP访问
   - 80端口：公开访问
   - 8000端口：不对外开放（内部使用）

## 下一步

1. 部署zenheart网站文件到 `/var/www/zenheart/`
2. 在网站中集成ZenAi API
3. 配置域名（可选）
4. 启用HTTPS（推荐）

## 备份

### 备份数据库

```bash
scp -i ~/.ssh/id_rsa ec2-user@51.21.54.93:/opt/zenai/data/zenai.db \
    ./backup-$(date +%Y%m%d).db
```

### 恢复数据库

```bash
scp -i ~/.ssh/id_rsa ./backup.db ec2-user@51.21.54.93:/opt/zenai/data/zenai.db
ssh -i ~/.ssh/id_rsa ec2-user@51.21.54.93 'sudo systemctl restart zenai'
```

## 支持

- 部署脚本：`deploy_ec2.sh`
- 详细文档：`docs/deployment-guide.md`
- API文档：http://51.21.54.93/api/docs
