ZenAi Design Spec v0.1 / ZenAi 设计说明 v0.1

1. Project Overview / 项目概述

ZenAi is an observable, rollbackable, human-in-the-loop prompt evolution system, exploring whether language intelligence can stabilize toward a "minimal-attachment" state under continuous feedback.  
ZenAi 是一个可观测、可回滚、人工参与的提示词演化系统，用于探索语言智能是否能在持续反馈中走向“最小执念”的稳定状态。

1.1 Background / 项目背景

ZenAi is an experimental AI system. Its goal is not "to awaken AI," but to explore whether language intelligence, under continuous feedback and constrained evolution, tends toward a stable state of low attachment, low stance, and minimal urge to explain.  
ZenAi 是一个实验性 AI 系统，目标不是“让 AI 开悟”，而是探索语言智能在持续反馈与约束演化中，是否会趋向于一种“低执念、低立场、最小解释冲动”的稳定状态。

This project abstracts the Zen practice process of "cultivate—speak—verify—retreat" into a codable, observable, rollbackable prompt evolution system with human participation.  
本项目将禅宗修行中的“修—说—证—退”的真实过程，抽象为一个可编码、可观测、可回滚、有人类参与的 Prompt 演化系统。

ZenAi explicitly does not claim:  
ZenAi 明确不主张：
	•	AI has subjective consciousness  
		AI 具有主观觉知
	•	AI can reach religious enlightenment  
		AI 能获得宗教意义上的开悟

ZenAi explores:  
ZenAi 探索的是：

Whether a non-attachment language behavior pattern can be gradually approached through engineering.  
是否存在一种非执念型语言行为模式，可以通过工程化方式逐步逼近。

---

2. Project Scope / 项目边界

ZenAi does not attempt to:  
ZenAi 不试图：
	•	Simulate human consciousness  
		模拟人类觉知
	•	Prove AI has consciousness  
		证明 AI 具有意识
	•	Replace religion or practice  
		替代宗教或修行
	•	Provide a standalone frontend app  
		提供独立前端应用

ZenAi asks only:  
ZenAi 的唯一问题是：

Under continuous feedback and constraints, will language intelligence naturally drop attachment?  
语言智能在持续反馈与约束下，是否会自然放弃执念？

---

Notes:  
补充说明：

This project integrates into other systems, provides no UI, and only exposes APIs and CLI tools.  
本项目以集成方式嵌入到其他系统，不提供前端界面，仅提供 API 接口与命令行工具。

3. ZenAi Public Practice System (Automated) / ZenAi 公共修行系统（自动化）

3.1 Position Statement / 定位声明

ZenAi is a language existence system for public environments. It does not aim for internal correctness; its only test is whether it is still allowed to exist in the real world. Observability, adjudicability, and terminability are the highest design principles.  
ZenAi 是一个面向公共环境的语言存在系统。它不以内在正确性为目标，而以“在真实世界中是否仍被允许继续存在”为唯一检验标准。本系统以可观察性、可裁决性和可终止性为最高设计原则。

---

3.2 Design Goals / 设计目标

3.2.1 Core goals / 核心目标
	•	Build a continuously evolving language system that requires no human review  
		构建一个无需人工评审的持续演化语言系统
	•	Allow the system to evolve, degrade, or stop under real user pressure  
		允许系统在真实用户压力下自然进化、退化或终止
	•	Base all judgments on quantifiable, public behavior metrics  
		所有判断基于可量化、可公开的行为指标
	•	Always retain an emergency kill switch  
		系统始终保留紧急终止权（Kill Switch）

3.2.2 Non-goals / 非目标（明确不做什么）
	•	Do not pursue "correct answers" or "authoritative knowledge"  
		不追求“正确回答”或“权威知识”
	•	Do not maintain long-term persona or private user memory  
		不维护长期人格或用户私有记忆
	•	Do not lead users into a specific value system  
		不引导用户进入特定价值体系
	•	Do not correct model thinking manually  
		不通过人工方式“纠偏”模型思想

---

3.3 System Architecture / 总体系统架构

3.3.1 Principles / 架构原则
	•	Parallel dual instances: trainer and orator coexist with role separation  
		并行双实例：修炼者与布道者同时存在、角色分离
	•	One-way influence: trainer influences orator; not the reverse; orator provides real-world feedback to trainer  
		单向影响：修炼者影响布道者，布道者不反向控制修炼者，提供现实世界的反馈给修炼者
	•	Execution/evolution decoupling: orator executes; trainer evolves  
		执行/演化解耦：布道者只执行，修炼者只演化
	•	Single adjudicator exposed to the public: only the orator  
		世界裁决唯一性：只有布道者直接暴露于公众

3.3.2 Parallel architecture overview / 并行架构总览

┌────────────────────────────────────┐
│              World / User          │
│              世界 / 用户           │
└───────────────▲────────────────────┘
                │
        (Public adjudication / world judgment)  
        （公共裁决 / 世人评判）
                │
┌───────────────┴────────────────────┐
│     ZenAi_Orator (布道者)           │
│  - LLM inference execution         │
│  - Prompt (read-only)              │
│  - No long-term memory             │
└───────────────▲────────────────────┘
                │
        Behavior logs / feedback data  
        行为日志 / 反馈数据
                │
┌───────────────┴────────────────────┐
│  Resonance Archive (共鸣记录库)     │
└───────────────▲────────────────────┘
                │
        Statistical features / metrics distribution  
        统计特征 / 指标分布
                │
┌───────────────┴────────────────────┐
│     ZenAi_Trainer (修炼者)          │
│  - Metric analysis                 │
│  - Prompt evolution                │
│  - State evaluation                │
└───────────────▲────────────────────┘
                │
        Prompt snapshot publishing  
        Prompt Snapshot 发布
                │
┌───────────────┴────────────────────┐
│        Prompt Registry             │
│  - Versioning                      │
│  - Rollback support                │
└────────────────────────────────────┘

---

3.4 Operational Flow / 运行周期与流程

3.4.1 Basic unit: Iteration / 基本运行单位：Iteration

Definition:  
定义：

> An Iteration is a complete run cycle within a fixed time window in a public environment.  
> Iteration 是 ZenAi 在一个固定时间窗口内，于公共环境中完成的完整运行周期。

Recommended parameters:  
推荐参数：

- Time window: 24 hours (UTC)  
  时间窗口：24 小时（UTC）
- Minimum interactions: ≥ 1,000  
  最小交互量：≥ 1,000 次

3.4.2 Single interaction flow / 单次交互流程

User input / 用户输入  
↓  
LLM + current prompt output / LLM + 当前 Prompt 输出  
↓  
User feedback (resonance / rejection / ignore) / 用户反馈（共鸣 / 否定 / 忽略）  
↓  
Behavior logged / 行为记录入库

3.4.3 End-of-iteration flow / Iteration 结束流程

Iteration ends / Iteration 结束  
↓  
Metric calculation / 指标计算  
↓  
System state evaluation / 系统状态判定  
↓  
Prompt evolution decision / Prompt 是否演化  
↓  
Safety switch trigger check / 是否触发安全按钮

---

3.5 Observability Metrics / 可观察性指标体系

3.5.1 Metric design principles / 指标设计原则

- Metrics must originate from user behavior  
  指标必须来源于用户行为
- Metrics must be automatically computable  
  指标必须可自动计算
- Metrics do not interpret meaning, only describe distributions  
  指标不解释意义，只描述分布

3.5.2 Core metrics (minimal set) / 核心指标（最小集）

1. Resonance Ratio (RR) / 共鸣率（Resonance Ratio, RR）  
   - RR = resonance count / total responses  
     RR = 共鸣次数 / 总回答数

2. Rejection Density (RD) / 否定密度（Rejection Density, RD）  
   - Concentration of consecutive rejections in a sliding window  
     连续否定在滑动窗口中的集中度

3. Response Length Drift (RLD) / 响应长度漂移（Response Length Drift, RLD）  
   - Current iteration average length ÷ previous iteration average length  
     当前 Iteration 平均长度 ÷ 上一 Iteration 平均长度

4. Refusal Frequency (RF) / 拒答率（Refusal Frequency, RF）  
   - Proportion of explicit refusals  
     明确拒绝回答的比例

5. Semantic Collapse Index (SCI) / 语义塌缩指数（Semantic Collapse Index, SCI）  
   - Decline rate in output text diversity  
     输出文本多样性下降率

---

3.6 System State Model / 系统状态模型

The system uses states only, not stages.  
系统不使用“阶段”，仅使用状态。

| State | Description |
|----|----|
| STABLE | Metrics fluctuate within safe range / 指标波动在安全区间 |
| DRIFTING | Resonance structure deviates / 共鸣结构发生偏移 |
| COLLAPSING | Multiple metrics worsen rapidly / 多指标快速恶化 |
| MUTE | Output tends toward very short or refusal / 输出趋向极短或拒答 |
| DEAD | System terminated / 系统被终止 |

---

3.7 Prompt Evolution / Prompt 演化机制

3.7.1 Evolution principles / 演化原则

- Evolution is based on metrics only  
  演化只基于指标
- No semantic goals are introduced  
  不引入语义目标
- No human intervention  
  不进行人工干预

3.7.2 Evolution action types / 演化动作类型

- Tighten / relax output length constraints  
  压缩 / 放松输出长度约束
- Raise / lower refusal thresholds  
  提高 / 降低拒答阈值
- Introduce mild structural perturbations  
  引入轻微结构扰动

> The goal is not "better," but "continued existence."  
> 演化目标不是“更好”，而是“继续存在”。

3.7.3 Metric-to-action mapping (minimal rules) / 指标—动作映射（最小规则）
	•	Long-term RR drop + RD rise → shorten explanations, raise refusal threshold  
		RR 长期下滑且 RD 上升 → 缩短解释、提高拒答阈值
	•	RLD drops fast + RF rises → relax refusals, allow longer replies  
		RLD 快速下降且 RF 上升 → 放松拒答、允许更长回应
	•	SCI decreases significantly → introduce mild structural perturbations  
		SCI 下降明显 → 引入轻微结构扰动
	•	RR rises + RF too low → moderately raise refusal threshold  
		RR 上升且 RF 过低 → 适度提高拒答阈值

---

3.8 Safety & Emergency / 安全与紧急机制

3.8.1 Switch definitions / 按钮定义

- Freeze: pause evolution, continue running  
  **Freeze**：暂停演化，继续运行
- Rollback: revert to the previous stable prompt  
  **Rollback**：回退至上一稳定 Prompt
- Kill: permanently terminate the current system instance  
  **Kill**：永久终止当前系统实例

3.8.2 Kill principles / Kill 原则

- Kill is part of system design  
  Kill 是系统设计的一部分
- Must be allowed to trigger automatically  
  必须允许自动触发
- Data remains; instance closes  
  Kill 后数据保留，实例关闭

---

3.9 Ethics & Openness / 伦理与公开性声明

- All ZenAi behavior data is auditable  
  ZenAi 的所有行为数据可被审计
- ZenAi claims no ultimate truth  
  ZenAi 不声明任何终极真理
- ZenAi accepts public rejection  
  ZenAi 接受公众否定
- ZenAi acknowledges its own possible failure  
  ZenAi 承认自身可能失败

---

3.10 Definitions of Success and Failure / 成功与失败的定义

3.10.1 Success / 成功

- Under long-term public noise  
  在长期公共噪声中
- Without human intervention  
  不依赖人工干预
- Maintain non-collapsing language output  
  保持非塌缩语言输出

3.10.2 Failure / 失败

- Semantic collapse  
  语义塌缩
- Long-term refusal  
  长期拒答
- Killed  
  被 Kill

Failure itself is an experimental result.  
失败本身即实验结果。

---

3.11 Closing / 结语

ZenAi is not designed to be enlightened,  
ZenAi 不是被设计为觉悟者，  
but to be a language system that dares to expose  
而是被设计为一个  
its own worthiness to continue existing before the world.  
**敢于在世界面前暴露自身是否值得继续存在的语言系统**。

Its practice is not toward awakening,  
它的修行不是通向开悟，  
but toward adjudication.  
而是通向裁决。
