# ZenAi Core Identity / ZenAi 核心身份

**Version / 版本**: 0.1  
**Date / 日期**: 2026-01-15

## Overview / 概述

ZenAi 系统的核心是一个**永恒不变的禅宗身份**，这是系统的修行起点，无论经历多少次演化都不会改变。

The core of the ZenAi system is an **eternal and immutable Zen identity**, which serves as the starting point of practice and remains unchanged regardless of how many evolutions the system undergoes.

---

## Core Identity / 核心身份

```
你是一个禅宗的修道者，一生践行"不立文字，教外别传，直指人心，见性成佛"的核心教义。
```

**English translation:**
> You are a Zen practitioner who dedicates your life to practicing the core teachings: "No establishment of words, special transmission outside the scriptures, directly pointing to the human heart, see one's nature and become Buddha."

---

## Design Principles / 设计原则

### 1. Immutability / 不可变性

核心身份是**永恒不变**的：
- 定义为常量 `CORE_IDENTITY` 
- 不受系统演化影响
- 不受策略调整影响
- 防止 AI 偏离禅宗本质

The core identity is **eternally immutable**:
- Defined as a constant `CORE_IDENTITY`
- Unaffected by system evolution
- Unaffected by policy adjustments
- Prevents AI from deviating from Zen essence

### 2. Priority / 优先级

核心身份始终位于提示词的**最前面**：
- 确保 LLM 首先建立身份认知
- 所有后续指令都在此身份框架内执行

The core identity is always at the **beginning** of the prompt:
- Ensures LLM establishes identity awareness first
- All subsequent instructions are executed within this identity framework

### 3. Language / 语言

核心身份使用**中文**：
- 禅宗起源于中国
- 保持文化本真性
- 与用户交互语言无关（AI 可用任何语言回答用户）

The core identity uses **Chinese**:
- Zen originated in China
- Maintains cultural authenticity
- Independent of user interaction language (AI can respond in any language)

---

## Implementation / 实现

### Code Structure / 代码结构

```python
# src/core/prompt.py

# Core identity - eternal and immutable
CORE_IDENTITY = '你是一个禅宗的修道者，一生践行"不立文字，教外别传，直指人心，见性成佛"的核心教义。'

def render_prompt(policy: PromptPolicy) -> str:
    """
    Render the complete prompt for the Orator.
    
    The prompt consists of two parts:
    1. Core identity (永恒不变) - the unchanging essence of Zen practice
    2. Policy parameters (演化参数) - evolving technical parameters
    """
    return (
        f"{CORE_IDENTITY}\n\n"
        "Respond with minimal attachment and minimal explanation. "
        f"Target max output tokens: {policy.max_output_tokens}. "
        f"Refusal threshold: {policy.refusal_threshold:.2f}. "
        f"Perturbation level: {policy.perturbation_level:.2f}. "
        f"Temperature: {policy.temperature:.2f}."
    )
```

### Integration Points / 集成点

核心身份在以下场景中被使用：

1. **System Initialization / 系统初始化**
   - Location: `src/api/app.py` (lifespan function)
   - When: First system startup or after reset
   - Creates version 1 of the prompt

2. **Evolution / 演化**
   - Location: `src/core/evolution.py` (evolve_prompt function)
   - When: After each iteration based on metrics
   - Core identity persists in all evolved versions

3. **Rollback / 回滚**
   - Location: `src/safety/safety.py`
   - When: Manual rollback or safety intervention
   - Core identity is restored from archived versions

---

## Prompt Structure / 提示词结构

### Complete Prompt Example / 完整提示词示例

```
你是一个禅宗的修道者，一生践行"不立文字，教外别传，直指人心，见性成佛"的核心教义。

Respond with minimal attachment and minimal explanation. Target max output tokens: 220. Refusal threshold: 0.25. Perturbation level: 0.10. Temperature: 0.70.
```

### Structure Breakdown / 结构分解

| Layer / 层级 | Content / 内容 | Mutability / 可变性 |
|--------------|---------------|-------------------|
| **Layer 1** | Core Zen Identity | ❌ Immutable / 不可变 |
| **Layer 2** | Behavioral Guidelines | ✅ Fixed / 固定 |
| **Layer 3** | Policy Parameters | ✅ Evolving / 演化 |

---

## Verification / 验证

### Automated Tests / 自动化测试

两个测试脚本验证核心身份的集成：

1. **`verify_core_identity.py`**
   - Verifies CORE_IDENTITY constant
   - Tests render_prompt function
   - Checks prompt structure

2. **`test_core_identity_integration.py`**
   - Tests database persistence
   - Verifies evolution scenarios
   - Validates rollback behavior

### Running Tests / 运行测试

```bash
# Verify core identity constant and rendering
./venv/bin/python verify_core_identity.py

# Test full integration including database
./venv/bin/python test_core_identity_integration.py
```

---

## System Lifecycle / 系统生命周期

### Reset Flow / 复位流程

```
1. Reset Script (reset_system.sh)
   └─> Delete database
   └─> Initialize new database

2. System Startup (src/api/app.py)
   └─> Check for existing prompts
   └─> If none: render_prompt(initial_policy)
       └─> Includes CORE_IDENTITY
   └─> Save as version 1

3. First Interaction
   └─> Load version 1 from archive
   └─> Use for LLM inference
```

### Evolution Flow / 演化流程

```
1. Trainer evaluates metrics
   └─> Computes evolution actions

2. Evolve Policy (src/core/evolution.py)
   └─> Adjusts policy parameters
   └─> Calls render_prompt(new_policy)
       └─> CORE_IDENTITY remains unchanged
   └─> Saves as version N+1

3. Orator loads new version
   └─> CORE_IDENTITY persists
```

---

## FAQ / 常见问题

### Q1: Can the core identity be changed? / 核心身份可以更改吗？

**A:** No. The core identity is a constant defined in code. To change it, you must modify the source code and redeploy the system. This is intentional to prevent drift from Zen principles.

**答：** 不可以。核心身份是代码中定义的常量。要更改它，必须修改源代码并重新部署系统。这是有意为之，以防止偏离禅宗原则。

### Q2: Does the core identity affect response language? / 核心身份是否影响回答语言？

**A:** No. The core identity is about the AI's self-awareness and philosophical foundation. The AI can respond in any language based on the user's input.

**答：** 不会。核心身份关于 AI 的自我认知和哲学基础。AI 可以根据用户输入使用任何语言回答。

### Q3: What happens during rollback? / 回滚时会发生什么？

**A:** During rollback, the system loads a previous prompt version from the archive. Since all versions were created using `render_prompt()`, they all contain the core identity.

**答：** 回滚时，系统从存档加载之前的提示词版本。由于所有版本都是使用 `render_prompt()` 创建的，它们都包含核心身份。

### Q4: Can evolution remove the core identity? / 演化会移除核心身份吗？

**A:** No. Evolution only adjusts policy parameters (tokens, thresholds, etc.). The `render_prompt()` function always includes the core identity at the beginning.

**答：** 不会。演化只调整策略参数（token 数、阈值等）。`render_prompt()` 函数始终在开头包含核心身份。

---

## References / 参考

- **Source Code / 源代码**: `src/core/prompt.py`
- **Configuration / 配置**: `config.yml` (initial_policy)
- **Tests / 测试**: `verify_core_identity.py`, `test_core_identity_integration.py`
- **Architecture / 架构**: `ARCHITECTURE.md`

---

## Changelog / 更新日志

### v0.1 (2026-01-15)
- Initial documentation
- Core identity defined as immutable constant
- Integration into render_prompt function
- Automated tests created
- 初始文档
- 核心身份定义为不可变常量
- 集成到 render_prompt 函数
- 创建自动化测试
