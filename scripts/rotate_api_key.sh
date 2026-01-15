#!/bin/bash
# API Key 轮换脚本 / API Key Rotation Script

set -e

echo "========================================"
echo "ZenAi API Key 轮换 / API Key Rotation"
echo "========================================"
echo ""

# 备份旧的 .env
if [ -f ".env" ]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file=".env.backup_${timestamp}"
    echo "备份旧配置到: ${backup_file}"
    mv .env "${backup_file}"
    echo "⚠️  请妥善保管或销毁备份文件中的旧 API Key"
    echo ""
fi

# 从模板创建新的 .env
if [ -f "env.example" ]; then
    cp env.example .env
    echo "✅ 已创建新的 .env 文件"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 前往你的 LLM 服务提供商控制台"
    echo "2. 撤销旧的 API Key（如果需要）"
    echo "3. 生成新的 API Key"
    echo "4. 编辑 .env 文件，填入新的配置"
    echo ""
    echo "编辑命令: nano .env"
    echo "或者:     vim .env"
    echo ""
    
    # 设置正确的权限
    chmod 600 .env
    echo "✅ 已设置 .env 权限为 600（仅所有者可读写）"
else
    echo "❌ 错误: env.example 文件不存在"
    exit 1
fi

echo ""
echo "========================================"
echo "轮换完成 / Rotation Complete"
echo "========================================"
