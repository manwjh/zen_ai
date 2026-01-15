# ZenAi 文档中心

欢迎来到 ZenAi 文档中心！这里提供了完整的使用指南和技术文档。

---

## 📖 文档目录

### 快速开始
- **[QUICK_START.md](../QUICK_START.md)** - 5分钟快速启动指南
  - 环境准备
  - 启动系统
  - 单次测试
  - 批量测试
  - 监测管理

### 用户指南
- **[user-guide_v0.1.md](user-guide_v0.1.md)** - 完整使用指南
  - 详细启动步骤
  - 系统监测方法
  - 单次测试教程
  - 批量测试教程
  - 管理命令详解
  - 常见问题解答
  - API 端点参考

### 技术文档
- **[design-spec_v0.1.md](design-spec_v0.1.md)** - 设计规范
  - 核心概念
  - 系统设计
  - 演化机制

- **[token-management_v0.1.md](token-management_v0.1.md)** - Token 管理
  - Token 计算
  - 预算控制
  - 优化策略

### 架构文档
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - 系统架构
  - 系统层次
  - 模块职责
  - 数据流
  - 部署架构

### 项目信息
- **[README.md](../README.md)** - 项目概述
  - 项目介绍
  - 核心特性
  - 快速开始
  - 项目结构

- **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** - 项目状态
  - 开发进度
  - 已完成功能
  - 待办事项

---

## 🚀 使用流程

### 1. 首次使用
1. 阅读 [QUICK_START.md](../QUICK_START.md)
2. 按步骤配置环境
3. 启动系统
4. 运行测试

### 2. 日常使用
1. 启动系统：`./venv/bin/python -m src.main --no-scheduler`
2. 单次测试：`./venv/bin/python test_chat.py "你的问题"`
3. 批量测试：`./venv/bin/python batch_test.py data/your_tests.jsonl`
4. 查看状态：`./venv/bin/python -m src.admin status`

### 3. 深入学习
1. 阅读 [user-guide_v0.1.md](user-guide_v0.1.md) 了解所有功能
2. 阅读 [ARCHITECTURE.md](../ARCHITECTURE.md) 了解系统架构
3. 阅读 [design-spec_v0.1.md](design-spec_v0.1.md) 了解设计理念

---

## 🛠️ 测试工具

### 测试脚本
- **test_chat.py** - 单次聊天测试脚本
  ```bash
  ./venv/bin/python test_chat.py "你的问题" --feedback resonance
  ```

- **batch_test.py** - 批量测试脚本
  ```bash
  ./venv/bin/python batch_test.py data/sample_interactions.jsonl --output reports/results.json
  ```

### 管理工具
- **src.admin** - 系统管理工具
  ```bash
  # 查看状态
  ./venv/bin/python -m src.admin status
  
  # 查看历史
  ./venv/bin/python -m src.admin history
  
  # 查看提示词演化
  ./venv/bin/python -m src.admin prompts
  
  # 导出数据
  ./venv/bin/python -m src.admin export --output reports/metrics.json
  ```

---

## 📊 测试数据

### 样本数据
- **data/sample_interactions.jsonl** - 35个测试样本
  - 英文测试用例
  - 中文测试用例
  - 各种场景覆盖

### 创建自定义测试
```jsonl
{"user_input":"你的问题","feedback":"resonance"}
{"user_input":"另一个问题","feedback":"rejection"}
```

---

## 🔗 API 端点

### 基础端点
- `GET /health` - 健康检查
- `GET /status` - 系统状态
- `POST /chat` - 聊天接口
- `POST /feedback` - 提交反馈

### API 文档
启动系统后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📝 反馈类型

- **resonance** - 共鸣（用户喜欢，积极反馈）
- **rejection** - 否定（用户不满意，消极反馈）
- **ignore** - 忽略（用户无明确态度，中性）

---

## 🎯 核心指标

系统监测以下 5 个核心指标：

1. **RR** (Resonance Ratio) - 共鸣率
2. **RD** (Rejection Density) - 否定密度
3. **RLD** (Response Length Drift) - 响应长度漂移
4. **RF** (Refusal Frequency) - 拒答率
5. **SCI** (Semantic Collapse Index) - 语义塌缩指数

详见 [user-guide_v0.1.md](user-guide_v0.1.md)

---

## 📞 获取帮助

### 查看帮助信息
```bash
# 主程序帮助
./venv/bin/python -m src.main --help

# 管理工具帮助
./venv/bin/python -m src.admin --help

# 测试脚本帮助
./venv/bin/python test_chat.py --help
./venv/bin/python batch_test.py --help
```

### 常见问题
参考 [user-guide_v0.1.md](user-guide_v0.1.md) 中的 FAQ 章节

---

## 📅 文档版本

- **user-guide**: v0.1 (2026-01-15)
- **design-spec**: v0.1
- **token-management**: v0.1
- **QUICK_START**: v1.0 (2026-01-15)

---

**祝您使用愉快！如有问题，欢迎查阅相关文档。**
