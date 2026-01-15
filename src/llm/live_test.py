from __future__ import annotations

from .llm_client import LlmMessage, send_chat_completion
from .llm_config import load_llm_config


def main() -> int:
    config = load_llm_config()
    response = send_chat_completion(
        config=config,
        messages=[
            LlmMessage(role="system", content="You are a concise assistant."),
            LlmMessage(role="user", content="Say hello in one short sentence."),
        ],
        temperature=0.2,
        max_tokens=32,
    )
    print("LLM live response:")
    print(response.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
