from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    max_context_tokens: int

    def __repr__(self) -> str:
        """String representation with masked API key"""
        masked_key = self.api_key[:8] + "..." if len(self.api_key) > 8 else "***"
        return (
            f"LLMConfig(provider={self.provider!r}, "
            f"api_key={masked_key!r}, "
            f"base_url={self.base_url!r}, "
            f"model={self.model!r}, "
            f"max_context_tokens={self.max_context_tokens})"
        )


def load_llm_config() -> LLMConfig:
    provider = os.environ.get("ZENAI_LLM_PROVIDER")
    api_key = os.environ.get("ZENAI_LLM_API_KEY")
    base_url = os.environ.get("ZENAI_LLM_BASE_URL")
    model = os.environ.get("ZENAI_LLM_MODEL")
    max_context_tokens_raw = os.environ.get("ZENAI_LLM_MAX_CONTEXT_TOKENS")

    missing = [
        name
        for name, value in (
            ("ZENAI_LLM_PROVIDER", provider),
            ("ZENAI_LLM_API_KEY", api_key),
            ("ZENAI_LLM_BASE_URL", base_url),
            ("ZENAI_LLM_MODEL", model),
            ("ZENAI_LLM_MAX_CONTEXT_TOKENS", max_context_tokens_raw),
        )
        if not value
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {missing_list}."
        )

    try:
        max_context_tokens = int(max_context_tokens_raw)
    except ValueError as exc:
        raise ValueError(
            "ZENAI_LLM_MAX_CONTEXT_TOKENS must be an integer."
        ) from exc

    return LLMConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_context_tokens=max_context_tokens,
    )
