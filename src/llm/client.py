from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

from openai import OpenAI

from .config import LLMConfig


@dataclass(frozen=True)
class LlmMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LlmRequest:
    endpoint: str
    headers: dict[str, str]
    payload: dict[str, object]


def build_chat_request(
    config: LLMConfig,
    messages: Iterable[LlmMessage],
    temperature: float,
    max_tokens: int,
) -> LlmRequest:
    endpoint = urljoin(config.base_url.rstrip("/") + "/", "chat/completions")
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return LlmRequest(endpoint=endpoint, headers=headers, payload=payload)


def send_chat_completion(
    config: LLMConfig,
    messages: Iterable[LlmMessage],
    temperature: float,
    max_tokens: int,
) -> str:
    client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
    )
    response = client.chat.completions.create(
        model=config.model,
        messages=[{"role": msg.role, "content": msg.content} for msg in messages],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return content or ""
