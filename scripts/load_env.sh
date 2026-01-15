#!/bin/bash
# Load environment variables from .env file / 从 .env 文件加载环境变量

set -a
source .env
set +a

echo "Environment variables loaded / 环境变量已加载"
echo "Provider: $ZENAI_LLM_PROVIDER"
echo "API Key: ${ZENAI_LLM_API_KEY:0:10}..." # Show first 10 chars only
echo "Base URL: $ZENAI_LLM_BASE_URL"
echo "Model: $ZENAI_LLM_MODEL"
echo "Max Context Tokens: $ZENAI_LLM_MAX_CONTEXT_TOKENS"
