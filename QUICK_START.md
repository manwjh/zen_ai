# ZenAi 快速开始指南

> 5分钟启动并测试 ZenAi 系统

---

## 1️⃣ 环境准备

### 安装 Python 3.11
```bash
# 检查是否已安装
python3.11 --version

# macOS 使用 Homebrew 安装
brew install python@3.11
```

### 创建虚拟环境
```bash
cd /Users/wangjunhui/playcode/zen_ai

# 创建虚拟环境（使用 Python 3.11）
python3.11 -m venv venv

# 安装依赖
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install requests  # 测试脚本需要
```

### 配置环境变量
确保 `.env` 文件已配置好 LLM API 密钥：

```bash
cat .env
# 应该看到：
# ZENAI_LLM_PROVIDER=perfxcloud
# ZENAI_LLM_API_KEY=sk-xxxxx...
# ...
```

---

## 2️⃣ 启动系统

```bash
# 启动 API 服务（无自动训练调度）
./venv/bin/python -m src.main --no-scheduler
```

**成功启动标志：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 3️⃣ 测试系统

### 方式 A: 使用 curl

```bash
# 健康检查
curl http://localhost:8000/health

# 发送聊天请求
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input":"你好"}' | python3 -m json.tool
```

### 方式 B: 使用测试脚本（推荐）

#### 单次测试
```bash
# 基础测试
./venv/bin/python test_chat.py "你好，请介绍一下你自己"

# 带反馈测试
./venv/bin/python test_chat.py "什么是共鸣率？" --feedback resonance

# 查看帮助
./venv/bin/python test_chat.py --help
```

**输出示例：**
```
============================================================
ZenAi Chat Test / ZenAi 聊天测试
============================================================

User Input / 用户输入:
  你好，请介绍一下你自己

Response / 响应:
------------------------------------------------------------
Interaction ID: 2
Prompt Version: 1
Refusal: True
Timestamp: 2026-01-15T03:57:48.792408

Response Text / 响应文本:
我是ZenAi Orator。
不执于形，不滞于言。
回应如风过林梢，不问来处，不问归途。
你问，我答。
仅此而已。
------------------------------------------------------------

Test completed / 测试完成
============================================================
```

#### 批量测试
```bash
# 运行所有样本测试
./venv/bin/python batch_test.py data/sample_interactions.jsonl

# 保存测试结果
./venv/bin/python batch_test.py data/sample_interactions.jsonl \
  --output reports/test_results.json

# 详细模式
./venv/bin/python batch_test.py data/sample_interactions.jsonl \
  --output reports/test_results.json \
  --verbose

# 调整请求间隔（避免过快）
./venv/bin/python batch_test.py data/sample_interactions.jsonl \
  --delay 0.5
```

**输出示例：**
```
============================================================
ZenAi Batch Test / ZenAi 批量测试
============================================================

Loading test cases from: data/sample_interactions.jsonl
Loaded 35 test cases / 加载了 35 个测试用例
Delay between requests: 0.3s / 请求间隔: 0.3秒

[1/35] Testing: What is ZenAi?
  ✓ Success
[2/35] Testing: Give me a long explanation about Zen.
  ✓ Success
...

============================================================
Test Summary / 测试摘要
============================================================
Total Test Cases / 总测试数: 35
Successful / 成功: 34
Failed / 失败: 1
Success Rate / 成功率: 97.1%
============================================================
```

---

## 4️⃣ 监测系统

### 查看系统状态
```bash
./venv/bin/python -m src.admin status
```

### 查看迭代历史
```bash
./venv/bin/python -m src.admin history --limit 10
```

### 查看提示词演化
```bash
./venv/bin/python -m src.admin prompts
```

### 导出监测数据
```bash
./venv/bin/python -m src.admin export --output reports/metrics.json
```

### 实时监测（另开终端）
```bash
# 健康状态监测
watch -n 5 'curl -s http://localhost:8000/health | python3 -m json.tool'

# 系统状态监测
watch -n 10 'curl -s http://localhost:8000/status | python3 -m json.tool'
```

---

## 5️⃣ 管理命令

### 冻结/解冻系统
```bash
# 冻结演化（停止自动调整）
./venv/bin/python -m src.admin freeze

# 解冻演化
./venv/bin/python -m src.admin unfreeze
```

### 回滚版本
```bash
# 回滚到上一版本
./venv/bin/python -m src.admin rollback

# 回滚到指定版本
./venv/bin/python -m src.admin rollback --version 3
```

---

## 📊 测试数据格式

创建自己的测试数据（JSONL 格式）：

**文件: `my_tests.jsonl`**
```jsonl
{"user_input":"测试问题1","feedback":"resonance"}
{"user_input":"测试问题2","feedback":"rejection"}
{"user_input":"测试问题3","feedback":"ignore"}
```

**必需字段：**
- `user_input` (string): 用户输入
- `feedback` (string): 反馈类型
  - `resonance` = 用户喜欢（积极）
  - `rejection` = 用户不满意（消极）
  - `ignore` = 无明确态度（中性）

**可选字段：**
- `metadata` (object): 额外元数据
- `refusal` (boolean): 预期是否为拒答（用于评估）
- `response_text` (string): 期望响应（用于离线训练）

---

## 🔍 常见问题

### Q: 启动时报错 "Missing required environment variables"
**A:** 检查 `.env` 文件是否存在并包含所有必需变量：
```bash
cat .env
```

### Q: Python 版本错误
**A:** 确保使用 Python 3.10+：
```bash
python3.11 -m venv venv  # 重新创建虚拟环境
```

### Q: 端口被占用
**A:** 更改端口或停止占用进程：
```bash
# 使用其他端口
./venv/bin/python -m src.main --port 8001 --no-scheduler
```

### Q: 测试脚本找不到 requests
**A:** 在虚拟环境中安装：
```bash
./venv/bin/pip install requests
```

---

## 📚 完整文档

详细使用说明请参考：
- **用户指南**: `docs/user-guide_v0.1.md`
- **架构文档**: `ARCHITECTURE.md`
- **项目状态**: `PROJECT_STATUS.md`
- **README**: `README.md`

---

## 🚀 一键启动（完整流程）

```bash
# 1. 进入项目目录
cd /Users/wangjunhui/playcode/zen_ai

# 2. 创建虚拟环境（首次）
python3.11 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install requests

# 3. 配置环境变量（首次）
cp env.example .env
nano .env  # 编辑填入 API Key

# 4. 启动服务
./venv/bin/python -m src.main --no-scheduler

# 5. 测试（另开终端）
./venv/bin/python test_chat.py "你好"
./venv/bin/python batch_test.py data/sample_interactions.jsonl

# 6. 查看状态
./venv/bin/python -m src.admin status
```

---

**祝您使用愉快！🎉**

如有问题，请查看 `docs/user-guide_v0.1.md` 获取详细说明。
