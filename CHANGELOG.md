# Changelog / 更新日志

All notable changes to the ZenAi project will be documented in this file.

本文件记录 ZenAi 项目的所有重要变更。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
项目遵循[语义化版本](https://semver.org/lang/zh-CN/)规范。

---

## [0.1.0] - 2026-01-19

### Added / 新增功能

#### Core System / 核心系统
- 🏗️ **Dual Architecture** - Orator (execution) + Trainer (evolution) architecture
  - 双实例架构 - 布道者（执行）+ 修炼者（演化）
- 📊 **Five Core Metrics** - RR, RD, RLD, RF, SCI for system observability
  - 五大核心指标 - 共鸣率、否定密度、响应长度漂移、拒答率、语义塌缩指数
- 🔄 **Automatic Iteration Scheduler** - Time-window based prompt evolution
  - 自动迭代调度器 - 基于时间窗口的提示词演化
- 💾 **Persistent Storage** - SQLite-based Resonance Archive
  - 持久化存储 - 基于 SQLite 的共鸣记录库

#### API & Integration / API 与集成
- 🌐 **RESTful API** - FastAPI-based HTTP endpoints
  - RESTful API - 基于 FastAPI 的 HTTP 端点
- 💬 **Chat Interface** - `/chat` endpoint for user interactions
  - 对话接口 - `/chat` 端点处理用户交互
- 👍 **Feedback System** - `/feedback` endpoint for user feedback
  - 反馈系统 - `/feedback` 端点收集用户反馈
- 📈 **Status & Metrics** - `/status` and `/metrics` endpoints
  - 状态与指标 - `/status` 和 `/metrics` 端点
- 🌍 **Multi-language Support** - Chinese, English, Japanese, Korean, Traditional Chinese
  - 多语言支持 - 中文、英文、日文、韩文、繁体中文

#### Safety & Control / 安全与控制
- ❄️ **Freeze Mechanism** - Pause evolution while continuing service
  - 冻结机制 - 暂停演化但继续服务
- ⏮️ **Rollback Capability** - Restore to previous prompt versions
  - 回滚功能 - 恢复到之前的提示词版本
- ⛔ **Kill Switch** - Emergency system termination
  - 终止开关 - 紧急系统终止
- 🔍 **Safety Controller** - Automatic health monitoring and intervention
  - 安全控制器 - 自动健康监控和干预

#### Management Tools / 管理工具
- 🛠️ **Admin CLI** - Command-line management interface
  - 管理命令行 - 命令行管理界面
- 📊 **Status Dashboard** - View system status and metrics
  - 状态面板 - 查看系统状态和指标
- 📝 **History Viewer** - View iteration and prompt evolution history
  - 历史查看器 - 查看迭代和提示词演化历史
- 💾 **Data Export** - Export metrics and reports to JSON
  - 数据导出 - 导出指标和报告到 JSON

#### LLM Integration / LLM 集成
- 🤖 **Multi-provider Support** - OpenAI, DeepSeek, Qwen, etc.
  - 多提供商支持 - OpenAI、DeepSeek、通义千问等
- 🔧 **Flexible Configuration** - Environment-based LLM configuration
  - 灵活配置 - 基于环境变量的 LLM 配置
- 🔄 **Retry Mechanism** - Automatic retry on failures
  - 重试机制 - 失败时自动重试
- ⏱️ **Timeout Control** - Configurable request timeouts
  - 超时控制 - 可配置的请求超时

#### Data & Storage / 数据与存储
- 💾 **Interaction Records** - Complete user-system interaction history
  - 交互记录 - 完整的用户-系统交互历史
- 📊 **Metrics Snapshots** - Point-in-time metrics snapshots
  - 指标快照 - 时间点指标快照
- 📝 **Prompt History** - Full version history of all prompts
  - 提示词历史 - 所有提示词的完整版本历史
- 🔄 **Iteration Sessions** - Complete iteration metadata and results
  - 迭代会话 - 完整的迭代元数据和结果
- 🗄️ **Database Backup** - Automatic backup mechanism
  - 数据库备份 - 自动备份机制

#### Deployment / 部署
- 🚢 **Deployment Scripts** - Automated deployment to EC2
  - 部署脚本 - 自动化部署到 EC2
- 🔧 **Systemd Integration** - System service management
  - Systemd 集成 - 系统服务管理
- 📝 **Comprehensive Documentation** - Complete setup and usage guides
  - 完整文档 - 完整的设置和使用指南

### Technical Details / 技术细节

#### Architecture / 架构
- Python 3.10+ with type hints
- FastAPI for async web framework
- SQLAlchemy for ORM
- SQLite for data storage
- APScheduler for iteration scheduling

#### Database Schema / 数据库模式
- `interactions` - User interaction records with feedback
- `iterations` - Iteration session metadata
- `metrics_snapshots` - Point-in-time metrics
- `prompt_history` - Prompt version history
- `system_status` - Global system control flags

#### Configuration / 配置
- Environment-based configuration via `.env`
- Configurable iteration windows (default: 24 hours)
- Configurable interaction thresholds (default: 1000)
- Configurable check intervals (default: 60 minutes)

### Documentation / 文档
- 📖 Design Specification v0.1
- 📖 Core Identity v0.1
- 📖 Token Management v0.1
- 📖 Coding Guidelines v0.1
- 📖 User Guide v0.1
- 📖 Feedback System Documentation
- 📖 Algorithm Analysis
- 📖 README with quick start guide

### Known Limitations / 已知限制
- ⚠️ Single instance only (no distributed deployment)
  - 仅支持单实例（不支持分布式部署）
- ⚠️ SQLite database (not suitable for high concurrency)
  - SQLite 数据库（不适合高并发）
- ⚠️ No authentication/authorization system yet
  - 尚无认证/授权系统
- ⚠️ Basic semantic collapse detection (can be improved)
  - 基础的语义塌缩检测（可改进）

---

## Version Format / 版本格式

Versions follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
  - **MAJOR**: Incompatible API changes / 不兼容的 API 变更
  - **MINOR**: New features, backward compatible / 新功能，向后兼容
  - **PATCH**: Bug fixes, backward compatible / Bug 修复，向后兼容

版本遵循[语义化版本](https://semver.org/lang/zh-CN/)规范：
- **主版本号.次版本号.修订号** (例如：1.2.3)

---

## Links / 链接

- [GitHub Repository](https://github.com/manwjh/zen_ai)
- [Documentation](./docs/)
- [Issue Tracker](https://github.com/manwjh/zen_ai/issues)

---

**Note**: This is an experimental system in active development.
All APIs and behaviors are subject to change.

**注意**：这是一个实验性系统，正在积极开发中。
所有 API 和行为都可能发生变化。
