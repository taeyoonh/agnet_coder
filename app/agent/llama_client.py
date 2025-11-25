"""HTTP client wrapper for local llama.cpp server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List

import requests

from .simple_messages import BaseMessage

from .pipeline_utils import serialize_message


@dataclass(slots=True)
class LlamaServerConfig:
    base_url: str = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080")
    model: str = os.getenv(
        "LLAMA_SERVER_MODEL"
    )
    temperature: float = float(os.getenv("LLAMA_SERVER_TEMPERATURE", "0"))
    max_tokens: int = int(os.getenv("LLAMA_SERVER_MAX_TOKENS", "2048"))
    timeout: int = int(os.getenv("LLAMA_SERVER_TIMEOUT", "300"))
    stop: List[str] = ("<END-OF-CODE>",)
    ignore_eos: bool = True


class LlamaServerClient:
    """Thin wrapper around llama.cpp's OpenAI-compatible HTTP server."""

    def __init__(self, config: LlamaServerConfig | None = None) -> None:
        self.config = config or LlamaServerConfig()

        print("[llama] max_tokens =", self.config.max_tokens)  # 디버그용 한 줄


    def chat(self, messages: Iterable[BaseMessage]) -> str:
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "ignore_eos": self.config.ignore_eos,
            "stop": list(self.config.stop),


            "cache_prompt": False,  # 이전 프롬프트 캐시 재사용 X
            "n_keep": 0,            # KV 캐시에 남겨둘 토큰 0

            
            "messages": [serialize_message(msg) for msg in messages],
        }
        response = requests.post(
            f"{self.config.base_url.rstrip('/')}/v1/chat/completions",
            json=payload,
            timeout=self.config.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text.strip()
            raise RuntimeError(
                f"llama-server HTTP {response.status_code}: {detail or 'no detail'}"
            ) from exc
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Unexpected llama-server payload: {data}") from exc


__all__ = ["LlamaServerClient", "LlamaServerConfig"]
