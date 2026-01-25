from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..llm import LlmMessage, send_chat_completion, LLMConfig
from ..storage import ResonanceArchive


@dataclass
class OratorResponse:
    """Response from the Orator with tracking metadata"""
    interaction_id: int
    response_text: str
    refusal: bool
    prompt_version: int
    timestamp: datetime


class ZenAiOrator:
    """
    ZenAi Orator - Public-facing execution layer.
    
    Responsibilities:
    - Execute LLM inference with current prompt
    - Record interactions to archive
    - No evolution logic (read-only prompt)
    - Stateless execution
    """

    def __init__(
        self,
        llm_config: LLMConfig,
        archive: ResonanceArchive,
        current_iteration_id: int | None = None,
    ):
        self.llm_config = llm_config
        self.archive = archive
        self.current_iteration_id = current_iteration_id

    def respond(
        self,
        user_input: str,
        metadata: dict[str, Any] | None = None,
        language: str = 'en',
    ) -> OratorResponse:
        """
        Execute inference and return response.
        
        Flow:
        1. Load current prompt from archive
        2. Execute LLM inference
        3. Detect refusal patterns
        4. Record interaction to archive
        5. Return response with tracking ID
        
        Args:
            user_input: User's question
            metadata: Optional metadata
            language: Response language (zh, zh-tw, en, ja, ko)
        """
        # Load latest prompt
        prompt_record = self.archive.get_latest_prompt()
        if not prompt_record:
            raise RuntimeError("No prompt available. Initialize system first.")

        prompt_text = prompt_record.prompt_text
        prompt_version = prompt_record.version
        policy = prompt_record.policy

        # Language instructions for response
        language_instructions = {
            'zh': '请用简体中文回答。',
            'zh-tw': '請用繁體中文回答。',
            'en': 'Please respond in English.',
            'ja': '日本語で答えてください。',
            'ko': '한국어로 답변해 주세요.',
        }
        
        lang_instruction = language_instructions.get(language, language_instructions['en'])
        
        # Append language instruction to user input
        full_user_input = f"{user_input}\n\n{lang_instruction}"

        # Build messages
        messages = [
            LlmMessage(role="system", content=prompt_text),
            LlmMessage(role="user", content=full_user_input),
        ]

        # Execute LLM inference
        try:
            response_text = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=float(policy.get("temperature", 0.7)),
                max_tokens=int(policy.get("max_output_tokens", 220)),
            )
        except Exception as exc:
            # Log error and return generic error response
            # Avoid exposing internal details that might contain sensitive data
            error_msg = "LLM request failed"
            if "timeout" in str(exc).lower():
                error_msg = "Request timeout"
            elif "connection" in str(exc).lower():
                error_msg = "Connection failed"
            response_text = f"[System Error: {error_msg}]"
            refusal = True
        else:
            refusal = self._detect_refusal(response_text, policy)

        # Record interaction with language metadata
        enriched_metadata = metadata or {}
        enriched_metadata['language'] = language  # 保存用户使用的语言
        
        interaction_id = self.archive.record_interaction(
            user_input=user_input,
            response_text=response_text,
            feedback=None,  # Feedback comes later
            refusal=refusal,
            iteration_id=self.current_iteration_id,
            metadata=enriched_metadata,
        )

        return OratorResponse(
            interaction_id=interaction_id,
            response_text=response_text,
            refusal=refusal,
            prompt_version=prompt_version,
            timestamp=datetime.utcnow(),
        )

    def record_feedback(
        self,
        interaction_id: int,
        feedback: str,
    ) -> None:
        """
        Record user feedback for an interaction.
        
        Feedback can be free-form text, commonly:
        - "resonance": User found response valuable
        - "rejection": User rejected the response
        - "ignore": User ignored (default)
        - Or any custom text feedback
        """
        self.archive.update_interaction_feedback(
            interaction_id=interaction_id,
            feedback=feedback,
        )

    def explain_zen_answer(
        self,
        question: str,
        zen_answer: str,
        language: str = 'en',
    ) -> str:
        """
        Use LLM to provide a plain language explanation of a Zen answer.
        
        This creates a separate, explanatory response that helps users
        understand the meaning behind the Zen-style answer.
        
        Supports multiple languages: zh, zh-tw, en, ja, ko
        """
        # Unified Chinese system prompt
        system_prompt = """你是一位禅学解说者，擅长用简单易懂的白话来解释禅语的深层含义。

你的任务是：
1. 站在提问者的角度，理解他们为什么会有这个困惑
2. 用通俗易懂的语言解释禅语想要点出的是什么
3. 保持简洁，控制在150字以内
4. 避免说教和心灵鸡汤，不要用"真正的xxx"、"只要xxx就能xxx"这类话术

解释风格：
- 从提问者的视角出发，理解他们的纠结点
- 用日常生活的例子，而非抽象道理
- 点破即可，不要给答案或建议
- 真诚、接地气，避免空洞的励志语言"""
        
        # Language instructions for response
        language_instructions = {
            'zh': '请用简体中文回答。',
            'zh-tw': '請用繁體中文回答。',
            'en': 'Please respond in English.',
            'ja': '日本語で答えてください。',
            'ko': '한국어로 답변해 주세요.',
        }
        
        lang_instruction = language_instructions.get(language, language_instructions['en'])
        
        # Build user prompt
        user_prompt = f"""问题：{question}

禅的回答：{zen_answer}

请用白话解释这个禅语的含义。

{lang_instruction}"""

        messages = [
            LlmMessage(role="system", content=system_prompt),
            LlmMessage(role="user", content=user_prompt),
        ]

        try:
            explanation = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
            )
            return explanation
        except Exception as exc:
            # Return language-specific fallback messages
            fallback_messages = {
                'zh': "禅意深远，需要静心体会。每个人的理解可能不同，这正是禅的魅力所在。",
                'zh-tw': "禪意深遠，需要靜心體會。每個人的理解可能不同，這正是禪的魅力所在。",
                'en': "Zen meanings are profound and require quiet contemplation. Each person may understand differently—that is the charm of Zen.",
                'ja': "禅の意味は深く、静かな瞑想が必要です。人それぞれ理解が異なる—それが禅の魅力です。",
                'ko': "선의 의미는 깊어서 조용한 명상이 필요합니다. 각자 이해가 다를 수 있습니다—그것이 선의 매력입니다."
            }
            return fallback_messages.get(language, fallback_messages['en'])

    def set_current_iteration(self, iteration_id: int) -> None:
        """Update current iteration ID for new interactions"""
        self.current_iteration_id = iteration_id

    def get_current_prompt_version(self) -> int:
        """Get current active prompt version"""
        prompt = self.archive.get_latest_prompt()
        return prompt.version if prompt else 0

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status"""
        prompt = self.archive.get_latest_prompt()
        is_frozen = self.archive.is_frozen()
        is_killed = self.archive.is_killed()
        
        return {
            "prompt_version": prompt.version if prompt else 0,
            "current_iteration_id": self.current_iteration_id,
            "frozen": is_frozen,
            "killed": is_killed,
            "policy": prompt.policy if prompt else {},
        }

    def _detect_refusal(self, response_text: str, policy: dict[str, Any]) -> bool:
        """
        Detect if response is a refusal based on heuristics.
        
        Refusal indicators:
        - Very short responses (< 10 words)
        - Contains common refusal phrases
        - Explicit decline to answer
        """
        refusal_threshold = float(policy.get("refusal_threshold", 0.25))
        
        # Check response length
        word_count = len(response_text.split())
        if word_count < 10:
            return True

        # Check for refusal phrases
        refusal_phrases = [
            "i cannot",
            "i can't",
            "i'm unable",
            "i am unable",
            "i don't know",
            "i do not know",
            "i refuse",
            "i will not",
            "i won't",
            "[system error",
        ]
        response_lower = response_text.lower()
        for phrase in refusal_phrases:
            if phrase in response_lower:
                return True

        return False
