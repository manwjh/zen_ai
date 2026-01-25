# ZenAi 反馈系统设计文档

## 概述

ZenAi 采用**静默反馈映射**系统，通过观察用户的自然行为来推断反馈类型，而非直接询问用户满意度。这符合禅宗"观照"的理念 —— 不立文字，以行见心。

---

## 📊 数据库结构

### interactions 表

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY,
    iteration_id INTEGER,
    timestamp DATETIME,
    user_input TEXT,
    response_text TEXT,
    feedback VARCHAR(500),  -- 标准反馈类型
    refusal BOOLEAN,
    extra_data JSON         -- 详细反馈信息
);
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `feedback` | VARCHAR(500) | 标准反馈类型 | `resonance`, `rejection`, `ignore` |
| `extra_data` | JSON | 详细反馈信息 | 见下方结构说明 |

---

## 🎯 用户行为映射规则

### 映射表

| 用户行为 | feedback类型 | 权重 | 含义 | extra_data保存内容 |
|---------|-------------|------|------|-------------------|
| **agree** (启发) | `resonance` | 1.0 | 用户明确表示受到启发 | `behavior`, `timestamp` |
| **download** (下载) | `resonance` | 0.8 | 用户认为对话有保存价值 | `behavior`, `timestamp` |
| **explain** (请求解释) | `rejection` | 0.6 | 用户对回答感到困惑 | `behavior`, `comment`(解释内容), `timestamp` |
| **comment** (评论) | `ignore` | 0.0 | 普通交流（可情感分析） | `behavior`, `comment`(评论内容), `timestamp` |
| **timeout** (无操作) | `ignore` | 0.0 | 用户阅读后未采取行动 | `behavior`, `timestamp` |

---

## 📦 extra_data JSON 结构

### 1. 启发行为（agree）

```json
{
  "behavior": "agree",
  "feedback_type": "resonance",
  "timestamp": "2026-01-19T12:00:00.000Z"
}
```

### 2. 下载行为（download）

```json
{
  "behavior": "download",
  "feedback_type": "resonance",
  "timestamp": "2026-01-19T12:00:00.000Z"
}
```

### 3. 请求解释（explain）⭐ 包含AI生成的解释内容

```json
{
  "behavior": "explain",
  "feedback_type": "rejection",
  "comment": "这句禅语的意思是：放下执念，回归本心。就像水流一样，不执着于形态，自然而然地前行。",
  "comment_length": 42,
  "timestamp": "2026-01-19T12:00:00.000Z"
}
```

**重要**：解释内容是由另一个AI生成的白话解释，保存它可以：
- 分析哪些类型的回答需要解释
- 评估解释的质量
- 了解用户困惑的点
- 训练更易懂的回答模式

### 4. 用户评论（comment）⭐ 包含用户评论内容

```json
{
  "behavior": "comment",
  "feedback_type": "ignore",
  "comment": "这段话很有启发，让我想起了《金刚经》的那句'应无所住而生其心'",
  "comment_length": 33,
  "timestamp": "2026-01-19T12:00:00.000Z"
}
```

**重要**：用户评论是宝贵的质量反馈，保存它可以：
- 了解用户的真实想法
- 进行情感分析（未来可调整为 resonance/rejection）
- 发现用户感兴趣的主题
- 改进回答质量

### 5. 无操作（timeout）

```json
{
  "behavior": "timeout",
  "feedback_type": "ignore",
  "timestamp": "2026-01-19T12:00:00.000Z"
}
```

---

## 🔄 完整数据流

### 前端 → 后端

```javascript
// 前端发送（只发送原始行为）
POST /api/feedback
{
  "interaction_id": 123,
  "behavior": "explain",
  "comment": "这句禅语的意思是...",  // 可选
  "timestamp": "2026-01-19T12:00:00Z"
}
```

### 后端处理

```python
# 1. 映射行为到反馈类型
mapping = BEHAVIOR_FEEDBACK_MAPPING.get(behavior)
feedback_type = mapping['feedback_type']  # 'rejection'

# 2. 构建详细数据
feedback_data = {
    'behavior': 'explain',
    'feedback_type': 'rejection',
    'timestamp': request.timestamp,
}

if request.comment:
    feedback_data['comment'] = request.comment
    feedback_data['comment_length'] = len(request.comment)

# 3. 保存到数据库
interactions.feedback = 'rejection'  # 标准类型
interactions.extra_data = feedback_data  # 详细信息
```

### 后端 → 前端

```json
{
  "success": true,
  "interaction_id": 123,
  "behavior": "explain",
  "feedback_type": "rejection",
  "recorded_at": "2026-01-19T12:00:00Z"
}
```

---

## 💡 数据分析示例

### 查询所有带解释的记录

```sql
SELECT 
    id,
    user_input,
    response_text,
    json_extract(extra_data, '$.comment') as explanation
FROM interactions
WHERE 
    feedback = 'rejection' 
    AND json_extract(extra_data, '$.behavior') = 'explain'
ORDER BY timestamp DESC;
```

### 查询所有用户评论

```sql
SELECT 
    id,
    user_input,
    response_text,
    json_extract(extra_data, '$.comment') as user_comment
FROM interactions
WHERE 
    json_extract(extra_data, '$.behavior') = 'comment'
    AND json_extract(extra_data, '$.comment') IS NOT NULL
ORDER BY timestamp DESC;
```

### 统计各行为类型分布

```sql
SELECT 
    json_extract(extra_data, '$.behavior') as behavior,
    feedback as feedback_type,
    COUNT(*) as count
FROM interactions
GROUP BY behavior, feedback
ORDER BY count DESC;
```

### 找出需要解释最多的问题类型

```sql
SELECT 
    user_input,
    COUNT(*) as explain_count
FROM interactions
WHERE json_extract(extra_data, '$.behavior') = 'explain'
GROUP BY user_input
ORDER BY explain_count DESC
LIMIT 10;
```

---

## 🎯 未来扩展

### 1. 情感分析

对用户评论进行情感分析，自动调整 feedback_type：

```python
if request.behavior == 'comment' and request.comment:
    sentiment_score = analyze_sentiment(request.comment)
    if sentiment_score > 0.7:
        feedback_type = 'resonance'  # 正面评论
    elif sentiment_score < 0.3:
        feedback_type = 'rejection'  # 负面评论
```

### 2. 行为权重

根据用户历史行为调整权重：

```python
if user_history.consecutive_downloads >= 3:
    # 连续下载说明质量很高
    feedback_type = 'resonance'
    weight = 1.0
```

### 3. 时间因素

考虑行为发生的时间：

```python
time_diff = (datetime.now() - interaction_time).seconds
if request.behavior == 'download' and time_diff < 10:
    # 10秒内就下载，说明非常满意
    weight = 1.0
```

---

## ✅ 验证清单

- [x] feedback 字段存储标准类型（resonance/rejection/ignore）
- [x] extra_data 字段存储详细信息（behavior, comment, timestamp）
- [x] 用户评论内容完整保存
- [x] AI生成的解释内容完整保存
- [x] 前端只发送原始行为，映射由后端处理
- [x] 所有行为都有对应的映射规则
- [x] 数据结构支持未来扩展

---

## 📚 相关文件

- **前端**: `src/js/zen.js`
  - `BEHAVIOR_UI_CONFIG` - UI配置
  - `submitFeedback()` - 提交反馈
  - `handleCardAction()` - 处理按钮点击
  - `handleExplainAction()` - 获取解释内容

- **后端**: `zen_ai/src/api/app.py`
  - `BEHAVIOR_FEEDBACK_MAPPING` - 映射规则
  - `/feedback` - 反馈API端点

- **数据库**: `zen_ai/src/storage/archive.py`
  - `update_interaction_feedback()` - 更新反馈

- **测试**: `zen_ai/test_feedback_complete.py`
  - 完整的功能测试脚本

---

**最后更新**: 2026-01-19  
**版本**: v1.0
