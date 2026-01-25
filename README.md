# ZenAi - Observable Prompt Evolution System / 可观测提示词演化系统

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Alpha-orange.svg)]()

ZenAi is an observable, rollbackable, human-in-the-loop prompt evolution system, exploring whether language intelligence can stabilize toward a "minimal-attachment" state under continuous feedback.

ZenAi 是一个可观测、可回滚、人工参与的提示词演化系统，用于探索语言智能是否能在持续反馈中走向"最小执念"的稳定状态。

**Current Version / 当前版本**: `0.1.0` (Alpha)

## 📋 Project Overview / 项目概述

ZenAi abstracts the Zen practice process into a codable, observable system with:
ZenAi 将禅宗修行过程抽象为可编码的可观测系统，具备：

- **Dual Architecture / 双实例架构**: Orator (execution) + Trainer (evolution)  
  布道者（执行）+ 修炼者（演化）
- **Metric-Driven Evolution / 指标驱动演化**: 5 core observability metrics  
  5 个核心可观测指标
- **Safety Mechanisms / 安全机制**: Freeze, Rollback, Kill switches  
  冻结、回滚、终止按钮
- **Persistent Storage / 持久化存储**: SQLite-based Resonance Archive  
  基于 SQLite 的共鸣记录库

## 🏗️ Architecture / 架构

```
┌────────────────────────────────────┐
│         World / Users              │
│         世界 / 用户                │
└───────────────▲────────────────────┘
                │
        (API / HTTP Endpoints)
        (API / HTTP 端点)
                │
┌───────────────┴────────────────────┐
│     ZenAi Orator (布道者)           │
│  - Stateless execution             │
│  - No evolution logic              │
│  - Records interactions            │
└───────────────▲────────────────────┘
                │
┌───────────────┴────────────────────┐
│  Resonance Archive (共鸣记录库)     │
│  - SQLite persistent storage       │
│  - Interaction history             │
│  - Metrics snapshots               │
└───────────────▲────────────────────┘
                │
┌───────────────┴────────────────────┐
│     ZenAi Trainer (修炼者)          │
│  - Metric computation              │
│  - Prompt evolution                │
│  - Iteration scheduler             │
└───────────────▲────────────────────┘
                │
┌───────────────┴────────────────────┐
│     Safety Controller              │
│  - Freeze / Rollback / Kill        │
│  - Health monitoring               │
└────────────────────────────────────┘
```

## 🚀 Quick Start / 快速开始

### 1. Installation / 安装

```bash
# Clone repository / 克隆仓库
git clone <repository-url>
cd zen_ai

# Install dependencies / 安装依赖
pip install -r requirements.txt

# Setup environment / 设置环境
cp env.example .env
# Edit .env with your LLM credentials
# 编辑 .env 填入你的 LLM 凭证
```

### 2. Configure LLM / 配置 LLM

Edit `.env` file:  
编辑 `.env` 文件：

```bash
ZENAI_LLM_PROVIDER=openai
ZENAI_LLM_API_KEY=your_api_key_here
ZENAI_LLM_BASE_URL=https://api.openai.com/v1
ZENAI_LLM_MODEL=gpt-3.5-turbo
ZENAI_LLM_MAX_CONTEXT_TOKENS=16000
```

### 3. Start System / 启动系统

```bash
# Start full system (API + Scheduler)
# 启动完整系统（API + 调度器）
python3 -m src.main

# Or start API only (no automatic iterations)
# 或仅启动 API（无自动迭代）
python3 -m src.main --no-scheduler

# Custom configuration / 自定义配置
python3 -m src.main \
  --port 8000 \
  --min-interactions 1000 \
  --check-interval 60
```

The system will be available at:  
系统将在以下地址可用：

- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Swagger UI)

### 4. Interact with API / 与 API 交互

```bash
# Send a message / 发送消息
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is the meaning of life?"}'

# Submit feedback / 提交反馈
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"interaction_id": 1, "feedback": "resonance"}'

# Check status / 检查状态
curl http://localhost:8000/status

# Get metrics / 获取指标
curl http://localhost:8000/metrics
```

## 🛠️ Admin Tool / 管理工具

```bash
# Check system status / 检查系统状态
python3 -m src.admin status

# View iteration history / 查看迭代历史
python3 -m src.admin history --limit 10 --verbose

# View prompt evolution / 查看提示词演化
python3 -m src.admin prompts

# Freeze evolution / 冻结演化
python3 -m src.admin freeze

# Unfreeze / 解冻
python3 -m src.admin unfreeze

# Rollback to previous version / 回滚到上一版本
python3 -m src.admin rollback

# Rollback to specific version / 回滚到指定版本
python3 -m src.admin rollback --version 5

# Export metrics to JSON / 导出指标到 JSON
python3 -m src.admin export --output metrics.json

# Kill system (requires confirmation) / 终止系统（需要确认）
python3 -m src.admin kill --confirm
```

## 📊 Metrics / 指标体系

### Core Metrics / 核心指标

1. **RR (Resonance Ratio / 共鸣率)**  
   `resonance_count / total_responses`

2. **RD (Rejection Density / 否定密度)**  
   Concentration of consecutive rejections in sliding window  
   滑动窗口中连续否定的集中度

3. **RLD (Response Length Drift / 响应长度漂移)**  
   `current_avg_length / previous_avg_length`

4. **RF (Refusal Frequency / 拒答率)**  
   Proportion of explicit refusals  
   明确拒答的比例

5. **SCI (Semantic Collapse Index / 语义塌缩指数)**  
   Decline rate in output text diversity  
   输出文本多样性下降率

### System States / 系统状态

- **STABLE / 稳定**: Metrics within safe range  
  指标在安全范围内
- **DRIFTING / 漂移**: Resonance structure deviates  
  共鸣结构偏移
- **COLLAPSING / 塌缩**: Multiple metrics worsen rapidly  
  多指标快速恶化
- **MUTE / 沉默**: Output tends toward very short or refusal  
  输出趋向极短或拒答
- **DEAD / 终止**: System terminated  
  系统被终止

## 📁 Project Structure / 项目结构

```
zen_ai/
├── src/
│   ├── core/              # Core models and algorithms
│   │   ├── models.py      # Data structures
│   │   ├── metrics.py     # Metric computation
│   │   ├── state.py       # State evaluation
│   │   ├── evolution.py   # Policy evolution
│   │   ├── prompt.py      # Prompt rendering
│   │   └── registry.py    # In-memory registry
│   ├── storage/           # Persistent storage
│   │   ├── database.py    # SQLAlchemy models
│   │   └── archive.py     # Resonance Archive
│   ├── orator/            # Execution layer
│   │   └── orator.py      # ZenAi Orator
│   ├── trainer/           # Evolution layer
│   │   └── trainer.py     # Trainer (修炼者)
│   ├── scheduler/         # Automatic iteration
│   │   └── scheduler.py   # Iteration scheduler
│   ├── safety/            # Safety mechanisms
│   │   └── safety.py      # Freeze/Rollback/Kill
│   ├── monitoring/        # System monitoring
│   │   └── monitoring.py  # Health checks
│   ├── api/               # HTTP API
│   │   └── app.py         # FastAPI application
│   ├── llm/               # LLM integration
│   │   ├── client.py      # API client
│   │   └── config.py      # Configuration
│   ├── utils/             # Utilities
│   │   ├── data_io.py     # Data loading
│   │   ├── reporting.py   # Report generation
│   │   └── cli.py         # Legacy CLI
│   ├── main.py            # System entry point
│   └── admin.py           # Admin tool
├── data/                  # Data directory
│   ├── zenai.db           # SQLite database
│   └── sample_interactions.jsonl
├── docs/                  # Documentation
│   ├── design-spec_v0.1.md
│   └── token-management_v0.1.md
├── requirements.txt       # Dependencies
├── .env                   # LLM configuration (gitignored)
├── env.example            # Environment template
└── README.md
```

## 🔒 Safety Mechanisms / 安全机制

### Freeze / 冻结

Pause prompt evolution while continuing to serve users:  
暂停提示词演化，但继续为用户服务：

```bash
python3 -m src.admin freeze
```

### Rollback / 回滚

Revert to a previous stable prompt version:  
回退到之前的稳定提示词版本：

```bash
python3 -m src.admin rollback --version 5
```

### Kill / 终止

Permanently terminate the system (data preserved):  
永久终止系统（数据保留）：

```bash
python3 -m src.admin kill --confirm
```

## 📈 Monitoring / 监控

### Health Check / 健康检查

```bash
python3 -m src.admin status
```

### Prometheus Metrics / Prometheus 指标

```bash
curl http://localhost:8000/metrics
```

### Export Data / 导出数据

```bash
python3 -m src.admin export --output report.json
```

## ⚙️ Configuration / 配置

### Iteration Configuration / 迭代配置

**Pure Count-Based Trigger / 纯粹基于计数触发**

The system now uses a pure interaction-count based approach:  
系统现在使用纯粹的交互数量触发方式：

- **Min Interactions / 最小交互数**: 1000 (default) - Triggers iteration when reached  
  达到此数量时触发迭代
- **Check Interval / 检查间隔**: 60 minutes (default) - How often to check  
  检查频率
- ~~**Time Window**~~: REMOVED - No longer waits for time windows  
  已移除 - 不再等待时间窗口

### Evolution Rules / 演化规则

Defined in `src/core/evolution.py`:  
定义在 `src/core/evolution.py`：

- Target resonance ratio / 目标共鸣率
- Rejection density thresholds / 否定密度阈值
- Output length constraints / 输出长度约束
- Temperature adjustment / 温度调整

### State Thresholds / 状态阈值

Defined in `src/core/state.py`:  
定义在 `src/core/state.py`：

- STABLE state requirements / 稳定状态要求
- COLLAPSING detection / 塌缩检测
- MUTE conditions / 沉默条件

## 🚢 Deployment / 部署

### Deploy to EC2 / 部署到 EC2

```bash
# Deploy backend to production server
# 部署后端到生产服务器
./deploy-backend.sh [IP地址] [域名]

# Example / 示例
./deploy-backend.sh 51.21.54.93 zenheart.net
```

For full deployment including frontend:  
完整部署（包含前端）：

```bash
cd .. && ./deploy-all.sh
```

See [Deployment Guide](../DEPLOYMENT_GUIDE.md) for details.  
详见[部署指南](../DEPLOYMENT_GUIDE.md)。

### Pull Remote Database / 拉取远程数据库

When you need to sync the production database to your local environment:  
当需要将生产数据库同步到本地环境时：

```bash
# Pull database from remote server
# 从远程服务器拉取数据库
./pull-database.sh [IP地址]

# Example / 示例
./pull-database.sh 51.21.54.93
./pull-database.sh  # Uses default IP / 使用默认IP
```

**Features / 特性**:
- Automatically backs up local database / 自动备份本地数据库
- Shows database statistics (record count, size, etc.) / 显示数据库统计信息
- Preserves all backup files / 保留所有备份文件
- Safe operation with validation / 安全操作和验证

The script will:  
脚本将会：
1. Test SSH connection / 测试SSH连接
2. Check remote database exists / 检查远程数据库存在
3. Backup local database if exists / 备份本地数据库（如果存在）
4. Download remote database / 下载远程数据库
5. Show statistics and backup history / 显示统计信息和备份历史

## 🧪 Development / 开发

### Run API Only / 仅运行 API

```bash
uvicorn src.api.app:app --reload --port 8000
```

### Run Scheduler Standalone / 独立运行调度器

```python
from pathlib import Path
from src.storage import ResonanceArchive
from src.orator import ZenAiOrator
from src.scheduler import IterationScheduler, IterationConfig
from src.llm.config import load_llm_config

archive = ResonanceArchive(db_path=Path("data/zenai.db"))
llm_config = load_llm_config()
orator = ZenAiOrator(llm_config=llm_config, archive=archive)

config = IterationConfig(
    time_window_hours=24,
    min_interactions=1000,
    check_interval_minutes=60,
)

scheduler = IterationScheduler(archive, orator, config)
scheduler.start()
```

## 📖 Documentation / 文档

- [CHANGELOG](CHANGELOG.md) - Version history and updates  
  版本历史和更新日志
- [Design Specification v0.1](docs/design-spec_v0.1.md) - Complete system design  
  完整系统设计
- [Token Management v0.1](docs/token-management_v0.1.md) - Environment setup  
  环境设置

## 🤝 Philosophy / 哲学

ZenAi is **not** designed to be enlightened, but to be a language system that dares to expose its own worthiness to continue existing before the world.

ZenAi **不是**被设计为觉悟者，而是被设计为一个**敢于在世界面前暴露自身是否值得继续存在的语言系统**。

Its practice is not toward awakening, but toward adjudication.  
它的修行不是通向开悟，而是通向裁决。

## 📄 License / 许可证

See [LICENSE](LICENSE) file.

## 📌 Version History / 版本历史

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本历史。

## 🙏 Acknowledgments / 致谢

This project explores the intersection of:  
本项目探索以下领域的交集：

- Language model engineering / 语言模型工程
- Zen philosophy / 禅宗哲学
- Observable systems / 可观测系统
- Evolutionary algorithms / 演化算法
