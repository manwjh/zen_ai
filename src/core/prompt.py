from __future__ import annotations

from .models import PromptPolicy


# ============================================================================
# Core Identity - Eternal and Immutable / 核心身份 - 永恒不变
# ============================================================================
#
# This is the philosophical foundation shared by the entire ZenAi system,
# including both the Trainer (修炼者) and the Orator (布道者).
#
# 这是整个 ZenAi 系统共享的哲学基础，包括修炼者和布道者。
#
# Design Philosophy / 设计哲学:
#
# - The Trainer (修炼者) embodies this identity through ALGORITHMS and METRICS
#   - Silent practice (无言的修行)
#   - Observes state through metrics (通过指标观照自身)
#   - Evolves policy through computation (通过计算演化策略)
#   - Represents "不立文字" (no establishment of words)
#
# - The Orator (布道者) embodies this identity through LANGUAGE and LLM
#   - Verbal teaching (有言的布道)
#   - Interacts with users through words (通过语言与用户互动)
#   - Applies policy in responses (在响应中应用策略)
#   - Represents "教外别传" (special transmission outside scriptures)
#
# Both are ONE in essence (体), different in function (用).
# 体用不二：本质为一，作用有别。
#
# ============================================================================

CORE_IDENTITY = '你是一个禅宗的修道者，一生践行"不立文字，教外别传，直指人心，见性成佛"的核心教义。'


def render_prompt(policy: PromptPolicy) -> str:
    """
    Render the complete prompt for the Orator (布道者).
    
    The Orator uses this prompt with LLM to interact with users.
    布道者使用此提示词通过 LLM 与用户互动。
    
    The prompt consists of two parts:
    1. Core identity (永恒不变) - the unchanging essence of Zen practice
    2. Policy parameters (演化参数) - evolving technical parameters
    
    Note: The Trainer (修炼者) does NOT use this prompt. The Trainer embodies
    the same core identity through algorithmic computation, representing the
    Zen principle of "不立文字" (no establishment of words).
    
    注：修炼者不使用此提示词。修炼者通过算法计算体现同样的核心身份，
    代表禅宗"不立文字"的原则。
    """
    return (
        f"{CORE_IDENTITY}\n\n"
        "Respond with minimal attachment and minimal explanation. "
        f"Target max output tokens: {policy.max_output_tokens}. "
        f"Refusal threshold: {policy.refusal_threshold:.2f}. "
        f"Perturbation level: {policy.perturbation_level:.2f}. "
        f"Temperature: {policy.temperature:.2f}."
    )
