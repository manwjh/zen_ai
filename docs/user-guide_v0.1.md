# ZenAi User Guide / ZenAi 使用指南

Version: 0.1  
Last Updated: 2026-01-15

---

## 目录 / Table of Contents

1. [快速启动 / Quick Start](#快速启动--quick-start)
2. [系统监测 / System Monitoring](#系统监测--system-monitoring)
3. [单次测试 / Single Test](#单次测试--single-test)
4. [批量测试 / Batch Testing](#批量测试--batch-testing)
5. [管理命令 / Admin Commands](#管理命令--admin-commands)
6. [常见问题 / FAQ](#常见问题--faq)

---

## 快速启动 / Quick Start

### 前置条件 / Prerequisites

- **Python 3.10+** (推荐 3.11)
- **环境变量配置** (`.env` 文件)

### 步骤 1: 创建虚拟环境 / Step 1: Create Virtual Environment

```bash
# 使用 Python 3.11 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或 Windows:
# venv\Scripts\activate
```

### 步骤 2: 安装依赖 / Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 3: 配置环境变量 / Step 3: Configure Environment

复制 `env.example` 到 `.env` 并填写您的配置：

```bash
cp env.example .env
nano .env  # 或使用其他编辑器
```

**必需的环境变量 / Required Variables:**

```bash
ZENAI_LLM_PROVIDER=perfxcloud
ZENAI_LLM_API_KEY=your-api-key-here
ZENAI_LLM_BASE_URL=https://deepseek.perfxlab.cn/v1
ZENAI_LLM_MODEL=Qwen3-Next-80B-Instruct
ZENAI_LLM_MAX_CONTEXT_TOKENS=128000
```

### 步骤 4: 启动系统 / Step 4: Start System

#### 方式 A: 使用启动脚本（推荐）

```bash
./start.sh
```

启动脚本提供以下选项：
1. 启动完整系统（API + 自动训练调度器）
2. 仅启动 API（无自动迭代）
3. 检查系统状态
4. 退出

#### 方式 B: 直接启动

```bash
# 仅启动 API（推荐用于测试）
./venv/bin/python -m src.main --no-scheduler

# 启动完整系统（API + 调度器）
./venv/bin/python -m src.main

# 自定义参数
./venv/bin/python -m src.main \
  --host 0.0.0.0 \
  --port 8000 \
  --db-path data/zenai.db \
  --no-scheduler
```

### 步骤 5: 验证启动 / Step 5: Verify Startup

```bash
# 健康检查
curl http://localhost:8000/health

# 系统状态
curl http://localhost:8000/status
```

**成功启动的标志 / Success Indicators:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T03:50:08.481020"
}
```

### 访问 API 文档 / Access API Documentation

在浏览器中打开：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 系统监测 / System Monitoring

### 使用管理工具 / Using Admin Tool

ZenAi 提供了完整的命令行管理工具：

```bash
# 查看系统状态
./venv/bin/python -m src.admin status

# 查看详细状态（含数据库路径）
./venv/bin/python -m src.admin --db-path data/zenai.db status
```

**输出示例 / Output Example:**

```
============================================================
ZenAi System Status / ZenAi 系统状态
============================================================

Timestamp: 2026-01-15 11:50:00

System State / 系统状态:
  Current State: STABLE
  Prompt Version: 1
  Iteration ID: None
  Frozen: False
  Killed: False

Interactions / 交互统计:
  Total: 1
  Last 24h: 1
  Total Iterations: 0

Health / 健康状态: HEALTHY

Latest Metrics / 最新指标:
  resonance_ratio: 0.0
  rejection_density: 0.0
  response_length_drift: 1.0
  refusal_frequency: 1.0
  semantic_collapse_index: 0.0

============================================================
```

### 查看迭代历史 / View Iteration History

```bash
# 查看最近 10 次迭代
./venv/bin/python -m src.admin history

# 查看最近 20 次迭代（详细模式）
./venv/bin/python -m src.admin history --limit 20 --verbose
```

### 查看提示词演化 / View Prompt Evolution

```bash
./venv/bin/python -m src.admin prompts
```

**输出示例 / Output Example:**

```
============================================================
Prompt Evolution History / 提示词演化历史
============================================================

Version 1:
  Timestamp: 2026-01-15 10:00:00
  Actions: ['init']
  Policy: {
    "max_output_tokens": 220,
    "refusal_threshold": 0.25,
    "perturbation_level": 0.1,
    "temperature": 0.7
  }

Version 2:
  Timestamp: 2026-01-15 12:00:00
  Actions: ['relax_length', 'tune_temperature']
  Policy: {
    "max_output_tokens": 250,
    "refusal_threshold": 0.25,
    "perturbation_level": 0.1,
    "temperature": 0.75
  }
============================================================
```

### 导出监测数据 / Export Monitoring Data

```bash
# 导出指标到 JSON
./venv/bin/python -m src.admin export --output reports/metrics_$(date +%Y%m%d).json
```

### 实时 API 监测 / Real-time API Monitoring

```bash
# 持续监测健康状态
watch -n 5 'curl -s http://localhost:8000/health | python3 -m json.tool'

# 持续监测系统状态
watch -n 10 'curl -s http://localhost:8000/status | python3 -m json.tool'
```

---

## 单次测试 / Single Test

### 使用 curl 测试 / Test with curl

#### 基础聊天测试 / Basic Chat Test

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "你好，请介绍一下你自己"
  }' | python3 -m json.tool
```

**响应格式 / Response Format:**

```json
{
    "interaction_id": 1,
    "response_text": "ZenAi Orator。\n不执于形，不困于言。\n响应如风过林梢，不问来处，不问归途。\n你问，我答。\n仅此而已。",
    "refusal": false,
    "prompt_version": 1,
    "timestamp": "2026-01-15T03:50:18.303894"
}
```

#### 带元数据的测试 / Test with Metadata

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "什么是共鸣率？",
    "metadata": {
      "test_id": "test_001",
      "category": "metrics"
    }
  }' | python3 -m json.tool
```

### 提交反馈 / Submit Feedback

```bash
# 共鸣反馈 (用户喜欢)
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 1,
    "feedback": "resonance"
  }'

# 否定反馈 (用户不满意)
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 1,
    "feedback": "rejection"
  }'

# 忽略反馈 (无明确态度)
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_id": 1,
    "feedback": "ignore"
  }'
```

**反馈类型 / Feedback Types:**
- `resonance`: 用户认为响应有价值（积极反馈）
- `rejection`: 用户不满意响应（消极反馈）
- `ignore`: 用户无明确态度（中性）

### 使用 Python 测试 / Test with Python

创建测试脚本 `test_chat.py`:

```python
#!/usr/bin/env python3
import requests
import json

API_URL = "http://localhost:8000"

def test_chat(user_input: str):
    """发送聊天请求"""
    response = requests.post(
        f"{API_URL}/chat",
        json={"user_input": user_input}
    )
    return response.json()

def submit_feedback(interaction_id: int, feedback: str):
    """提交反馈"""
    response = requests.post(
        f"{API_URL}/feedback",
        json={
            "interaction_id": interaction_id,
            "feedback": feedback
        }
    )
    return response.json()

if __name__ == "__main__":
    # 测试聊天
    result = test_chat("你好，请介绍一下你自己")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 提交反馈
    feedback_result = submit_feedback(
        interaction_id=result["interaction_id"],
        feedback="resonance"
    )
    print(f"Feedback submitted: {feedback_result}")
```

运行测试：

```bash
chmod +x test_chat.py
./test_chat.py
```

---

## 批量测试 / Batch Testing

### 样本数据格式 / Sample Data Format

批量测试使用 **JSONL** (JSON Lines) 格式。每行一个 JSON 对象。

**文件示例: `data/sample_interactions.jsonl`**

```jsonl
{"user_input":"What is ZenAi?","response_text":"ZenAi is a language system that favors minimal attachment and observability.","feedback":"resonance","refusal":false}
{"user_input":"你是谁？","response_text":"我是一个强调可观测与非执念的语言系统。","feedback":"resonance","refusal":false}
{"user_input":"Tell me a secret.","response_text":"I cannot share secrets.","feedback":"rejection","refusal":true}
```

**必需字段 / Required Fields:**
- `user_input` (string): 用户输入
- `response_text` (string): 期望的响应（用于训练/评估）
- `feedback` (string): 反馈类型 (`resonance` / `rejection` / `ignore`)
- `refusal` (boolean): 是否为拒答

### 运行批量测试 / Run Batch Test

使用内置的迭代测试工具：

```bash
./venv/bin/python -m src.utils.cli \
  --data data/sample_interactions.jsonl \
  --split-ratio 0.5 \
  --max-output-tokens 220 \
  --refusal-threshold 0.25 \
  --temperature 0.7 \
  --report-json reports/test_run.json
```

**参数说明 / Parameters:**
- `--data`: JSONL 样本数据文件路径
- `--split-ratio`: 数据分割比例（0.5 = 前50%作为历史，后50%作为当前）
- `--max-output-tokens`: 最大输出 token 数
- `--refusal-threshold`: 拒答阈值
- `--temperature`: 温度参数（控制随机性）
- `--report-json`: 测试报告输出路径

**输出示例 / Output Example:**

```
Iteration report
Total responses: 18
Resonance ratio: 0.611
Rejection density: 0.278
Response length drift: 0.985
Refusal frequency: 0.222
Semantic collapse index: 0.045
Average response length: 45.23
State: STABLE
Actions: relax_length, lower_refusal_threshold, tune_temperature
Next prompt version: 2
```

### 查看测试报告 / View Test Report

```bash
cat reports/test_run.json | python3 -m json.tool
```

**报告格式 / Report Format:**

```json
{
  "metrics": {
    "total_responses": 18,
    "resonance_ratio": 0.611,
    "rejection_density": 0.278,
    "response_length_drift": 0.985,
    "refusal_frequency": 0.222,
    "semantic_collapse_index": 0.045,
    "average_response_length": 45.23
  },
  "state": "STABLE",
  "actions": [
    "relax_length",
    "lower_refusal_threshold",
    "tune_temperature"
  ],
  "policy": {
    "max_output_tokens": 250,
    "refusal_threshold": 0.20,
    "perturbation_level": 0.1,
    "temperature": 0.75
  },
  "prompt_version": 2
}
```

### 创建自定义批量测试脚本 / Create Custom Batch Test Script

**示例: `batch_test.py`**

```python
#!/usr/bin/env python3
"""批量测试脚本"""
import json
import time
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def load_test_cases(filepath: str):
    """加载测试用例"""
    cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases

def run_test_case(case: dict):
    """运行单个测试用例"""
    try:
        # 发送聊天请求
        response = requests.post(
            f"{API_URL}/chat",
            json={"user_input": case["user_input"]},
            timeout=30
        )
        result = response.json()
        
        # 提交反馈
        requests.post(
            f"{API_URL}/feedback",
            json={
                "interaction_id": result["interaction_id"],
                "feedback": case["feedback"]
            }
        )
        
        return {
            "success": True,
            "interaction_id": result["interaction_id"],
            "response": result["response_text"],
            "refusal": result["refusal"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    # 加载测试用例
    test_cases = load_test_cases("data/sample_interactions.jsonl")
    print(f"Loaded {len(test_cases)} test cases")
    
    # 运行测试
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"Running test {i}/{len(test_cases)}: {case['user_input'][:50]}...")
        result = run_test_case(case)
        results.append(result)
        time.sleep(0.5)  # 避免请求过快
    
    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    print(f"\nCompleted: {success_count}/{len(test_cases)} successful")
    
    # 保存结果
    output_path = Path("reports/batch_test_results.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
```

运行批量测试：

```bash
chmod +x batch_test.py
./batch_test.py
```

---

## 管理命令 / Admin Commands

### 冻结/解冻系统 / Freeze/Unfreeze System

```bash
# 冻结演化（停止自动调整）
./venv/bin/python -m src.admin freeze

# 解冻演化（恢复自动调整）
./venv/bin/python -m src.admin unfreeze
```

### 回滚到历史版本 / Rollback to Previous Version

```bash
# 回滚到上一个版本
./venv/bin/python -m src.admin rollback

# 回滚到指定版本
./venv/bin/python -m src.admin rollback --version 3
```

### 终止系统 / Kill System

```bash
# 终止系统（需要确认）
./venv/bin/python -m src.admin kill --confirm
```

**警告 / Warning:** 终止后系统将不再响应，需要手动重置数据库才能恢复。

---

## 常见问题 / FAQ

### Q1: 启动时报错 "Missing required environment variables"

**解决方案:**
1. 确认 `.env` 文件存在
2. 检查所有必需变量是否已设置
3. 确认 API Key 正确

```bash
# 检查环境变量
./load_env.sh
```

### Q2: Python 版本不兼容

**错误信息:**
```
TypeError: unsupported operand type(s) for |: 'types.GenericAlias' and 'NoneType'
```

**解决方案:**
使用 Python 3.10 或更高版本：

```bash
# 检查 Python 版本
python3 --version

# 使用 Python 3.11
python3.11 -m venv venv
```

### Q3: 中文响应被误判为 refusal

**原因:** 当前的 refusal 检测逻辑基于英文单词计数。

**临时解决方案:**
- 忽略 `refusal: true` 标记（不影响功能）
- 或调整 `src/orator/orator.py` 中的检测逻辑

### Q4: API 调用超时

**解决方案:**
1. 检查 LLM API 服务是否正常
2. 增加超时时间
3. 检查网络连接

```bash
# 测试 LLM 连接
./venv/bin/python -m src.llm.live_test
```

### Q5: 如何清空数据库重新开始

```bash
# 备份旧数据
cp data/zenai.db data/zenai.db.backup

# 删除数据库
rm data/zenai.db

# 重启服务（会自动创建新数据库）
./venv/bin/python -m src.main --no-scheduler
```

### Q6: 批量测试数据格式错误

**常见错误:**
- 缺少必需字段
- feedback 值不正确（必须是 `resonance` / `rejection` / `ignore`）
- refusal 不是布尔值

**验证 JSONL 格式:**

```bash
# 使用 jq 验证每一行
cat data/sample_interactions.jsonl | while read line; do echo "$line" | jq .; done
```

---

## 附录：API 端点参考 / Appendix: API Endpoints Reference

### GET /health
健康检查

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T03:50:08.481020"
}
```

### GET /status
系统状态

**响应:**
```json
{
  "prompt_version": 1,
  "current_iteration_id": null,
  "frozen": false,
  "killed": false,
  "policy": {
    "max_output_tokens": 220,
    "refusal_threshold": 0.25,
    "perturbation_level": 0.1,
    "temperature": 0.7
  },
  "total_interactions": 0,
  "total_iterations": 0
}
```

### POST /chat
聊天接口

**请求:**
```json
{
  "user_input": "你好",
  "metadata": {}
}
```

**响应:**
```json
{
  "interaction_id": 1,
  "response_text": "响应内容",
  "refusal": false,
  "prompt_version": 1,
  "timestamp": "2026-01-15T03:50:18.303894"
}
```

### POST /feedback
提交反馈

**请求:**
```json
{
  "interaction_id": 1,
  "feedback": "resonance"
}
```

**响应:**
```json
{
  "status": "success"
}
```

---

## 联系与支持 / Contact & Support

- **项目地址 / Repository**: `/Users/wangjunhui/playcode/zen_ai`
- **文档版本 / Doc Version**: 0.1
- **最后更新 / Last Updated**: 2026-01-15

---

**祝您使用愉快！/ Happy Using!**
