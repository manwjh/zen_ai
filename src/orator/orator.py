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
    ) -> OratorResponse:
        """
        Execute inference and return response.
        
        Flow:
        1. Load current prompt from archive
        2. Execute LLM inference
        3. Detect refusal patterns
        4. Record interaction to archive
        5. Return response with tracking ID
        """
        # Load latest prompt
        prompt_record = self.archive.get_latest_prompt()
        if not prompt_record:
            raise RuntimeError("No prompt available. Initialize system first.")

        prompt_text = prompt_record.prompt_text
        prompt_version = prompt_record.version
        policy = prompt_record.policy

        # Build messages
        messages = [
            LlmMessage(role="system", content=prompt_text),
            LlmMessage(role="user", content=user_input),
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

        # Record interaction
        interaction_id = self.archive.record_interaction(
            user_input=user_input,
            response_text=response_text,
            feedback=None,  # Feedback comes later
            refusal=refusal,
            iteration_id=self.current_iteration_id,
            metadata=metadata or {},
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
