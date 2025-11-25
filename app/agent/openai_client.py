from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from openai import OpenAI

from .simple_messages import BaseMessage
from .pipeline_utils import debug_log_messages, serialize_message


@dataclass(slots=True)
class OpenAIClientConfig:
    # Default model: gpt-5-mini
    model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    api_key: str | None = os.getenv("OPENAI_API_KEY")
    base_url: str | None = os.getenv("OPENAI_BASE_URL")

    # Shared options
    temperature: float | None = (
        float(os.getenv("OPENAI_TEMPERATURE"))
        if os.getenv("OPENAI_TEMPERATURE") is not None
        else None
    )

    # chat.completions only 
    max_completion_tokens: int = int(
        os.getenv("OPENAI_MAX_COMPLETION_TOKENS", os.getenv("OPENAI_MAX_TOKENS", "2048"))
    )

class OpenAIChatClient:
    """Minimal chat-completions client so we can swap backends easily."""

    def __init__(self, config: OpenAIClientConfig | None = None) -> None:
        self.config = config or OpenAIClientConfig()
        if not self.config.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for API-based engines.")
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def chat(self, messages: Iterable[BaseMessage]) -> str:
        message_list = list(messages)
        debug_log_messages(message_list, header="openai chat")
        serialized = [serialize_message(msg) for msg in message_list]


        return self._call_chat_endpoint(serialized)

    # ---------- chat.completions ----------

    def _call_chat_endpoint(self, serialized_messages: Sequence[dict]) -> str:
        kwargs = {
            "model": self.config.model,
            "input": serialized_messages, 
        }
        

        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature


        response = self.client.responses.create(**kwargs)

        try:

            content = response.output_text
        except (AttributeError, IndexError) as exc:  
            raise RuntimeError("Unexpected OpenAI payload: {}".format(response)) from exc

        return content.strip()


    def _use_responses_api(self) -> bool:
        lowered = self.config.model.lower()

        if lowered.startswith("gpt-5-mini"):
            return False
        prefixes = ("gpt-5", "o1", "o3", "gpt-4.1")
        return lowered.startswith(prefixes)





__all__ = ["OpenAIChatClient", "OpenAIClientConfig"]
