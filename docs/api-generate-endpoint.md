# 通用LLM生成接口文档

## 📌 概述

新增的 `/api/generate` 端点提供了**直接访问底层LLM的能力**，不经过ZenAI的禅意包装，适用于需要自定义prompt的应用场景。

## 🔗 端点信息

### **URL**
```
POST /api/generate
```

### **用途**
- 符号炼金术游戏
- 自定义AI应用
- 需要完全控制prompt的场景

## 📝 请求格式

### **Request Body** (JSON)

```json
{
  "prompt": "你的完整提示词",
  "temperature": 0.7,
  "max_tokens": 500
}
```

### **参数说明**

| 参数 | 类型 | 必需 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| `prompt` | string | ✅ | - | 1-50000 chars | 发送给LLM的完整提示词 |
| `temperature` | float | ❌ | 0.7 | 0.0-2.0 | 采样温度（越高越随机） |
| `max_tokens` | int | ❌ | 1000 | 1-4000 | 最大生成token数 |

## 📤 响应格式

### **Response Body** (JSON)

```json
{
  "text": "LLM生成的文本",
  "timestamp": "2026-01-20T12:34:56.789Z"
}
```

### **字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | LLM生成的原始文本 |
| `timestamp` | datetime | 生成时间戳 |

## 💻 使用示例

### **1. JavaScript (Fetch API)**

```javascript
async function generateWithLLM(prompt) {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: prompt,
      temperature: 0.7,
      max_tokens: 500,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  
  const data = await response.json();
  return data.text;
}

// 使用示例
const result = await generateWithLLM('请生成一个数学函数...');
console.log(result);
```

### **2. Python (requests)**

```python
import requests

def generate_with_llm(prompt, temperature=0.7, max_tokens=500):
    response = requests.post('http://localhost:8000/api/generate', json={
        'prompt': prompt,
        'temperature': temperature,
        'max_tokens': max_tokens,
    })
    response.raise_for_status()
    return response.json()['text']

# 使用示例
result = generate_with_llm('请生成一个数学函数...')
print(result)
```

### **3. cURL**

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请生成一个数学函数...",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

## 🎮 符号炼金术游戏集成

### **修改前** (使用ZenAI `/api/chat`)

```javascript
// ❌ 旧方式 - 会经过ZenAI的禅意包装
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_input: prompt,
    language: 'zh',
  }),
});
const data = await response.json();
return data.response_text; // 可能是禅意回答，不是JSON
```

### **修改后** (使用通用 `/api/generate`)

```javascript
// ✅ 新方式 - 直接调用LLM
const response = await fetch('/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    prompt: prompt,
    temperature: 0.7,
    max_tokens: 500,
  }),
});
const data = await response.json();
return data.text; // 原始LLM输出
```

## ⚙️ Temperature 参数指南

| Temperature | 效果 | 适用场景 |
|-------------|------|----------|
| 0.0 - 0.3 | 最确定性，重复性高 | 需要精确、一致的输出 |
| 0.4 - 0.7 | **平衡** | 大多数应用（推荐） |
| 0.8 - 1.2 | 更多创意和变化 | 创意写作、头脑风暴 |
| 1.3 - 2.0 | 高度随机 | 艺术创作、实验性应用 |

## 🔒 安全性考虑

1. **输入验证**: prompt长度限制在50000字符
2. **输出限制**: max_tokens最大4000
3. **错误处理**: 失败时返回500状态码和错误信息
4. **无状态**: 每次请求独立，不保存历史

## 🆚 `/api/chat` vs `/api/generate`

| 特性 | `/api/chat` (ZenAI) | `/api/generate` (通用) |
|------|---------------------|------------------------|
| **用途** | 禅意对话 | 通用LLM调用 |
| **Prompt** | ZenAI系统prompt包装 | 完全自定义 |
| **响应** | 禅意风格 | 原始LLM输出 |
| **记录** | 保存到数据库 | 不保存 |
| **反馈** | 支持用户反馈 | 无反馈机制 |
| **进化** | 参与系统进化 | 独立运行 |
| **适合场景** | ZenHeart产品对话 | 自定义应用 |

## 📊 性能建议

1. **并发控制**: 同时请求不要超过10个
2. **Token控制**: 根据需要调整max_tokens
3. **错误重试**: 建议实现指数退避重试
4. **超时设置**: 建议设置30秒超时

## ❓ 常见问题

### Q1: 为什么需要这个新接口？
**A**: ZenAI的 `/api/chat` 专为禅意对话设计，会用禅意风格包装响应。符号炼金术等应用需要直接的JSON输出，因此需要通用接口。

### Q2: 这个接口会影响ZenAI的进化吗？
**A**: 不会。`/api/generate` 是独立的，不记录交互历史，不参与系统进化。

### Q3: 可以用这个接口替代 `/api/chat` 吗？
**A**: 技术上可以，但不推荐。`/api/chat` 有完整的反馈和进化机制，是ZenHeart产品的核心。

### Q4: Temperature设置多少合适？
**A**: 对于符号炼金术这种需要一定创意但又要求格式正确的应用，推荐0.7。

## 🔧 故障排查

### **错误：500 Internal Server Error**
```json
{
  "detail": "LLM generation failed: ..."
}
```
**解决方案**:
1. 检查LLM配置是否正确（.env文件）
2. 检查API key是否有效
3. 检查网络连接

### **错误：422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required"
    }
  ]
}
```
**解决方案**: 确保请求包含必需的 `prompt` 字段

## 📚 相关文档

- [ZenAI API完整文档](./README.md)
- [符号炼金术游戏文档](../../docs/symbol-alchemy-feature.md)
- [LLM配置说明](./token-management_v0.1.md)

---

*最后更新: 2026-01-20*
*版本: v1.0.0*
