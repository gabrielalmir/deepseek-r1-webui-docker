from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


ProviderName = Literal["openai", "deepseek", "ollama"]

DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_OPENAI_BASE_URL = "https://apinebula.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"


@dataclass(frozen=True)
class ProviderConfig:
    provider: ProviderName
    model: str
    base_url: str
    api_key: str

    def checkpoint_metadata(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
        }


def _normalize_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    if not normalized:
        raise ValueError("base_url cannot be empty")
    return normalized


def _is_deepseek_url(value: str) -> bool:
    return (urlparse(value).hostname or "").lower() == "api.deepseek.com"


def resolve_provider_config(
    *,
    provider: str = "openai",
    model: str | None = None,
    base_url: str | None = None,
    environ: dict[str, str] | None = None,
) -> ProviderConfig:
    environment = os.environ if environ is None else environ
    provider_name = provider.strip().lower()

    if provider_name == "openai":
        resolved_url = _normalize_base_url(
            base_url
            or environment.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
        )
        if _is_deepseek_url(resolved_url):
            api_key = environment.get("OPENAI_API_KEY") or environment.get(
                "DEEPSEEK_API_KEY"
            )
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY or DEEPSEEK_API_KEY is required for DeepSeek"
                )
            return ProviderConfig(
                provider="deepseek",
                model=(model or DEFAULT_DEEPSEEK_MODEL).strip(),
                base_url=resolved_url,
                api_key=api_key,
            )

        api_key = environment.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for provider=openai")
        return ProviderConfig(
            provider="openai",
            model=(model or DEFAULT_OPENAI_MODEL).strip(),
            base_url=resolved_url,
            api_key=api_key,
        )

    if provider_name == "deepseek":
        api_key = environment.get("DEEPSEEK_API_KEY") or environment.get(
            "OPENAI_API_KEY"
        )
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY or OPENAI_API_KEY is required for provider=deepseek"
            )
        resolved_url = (
            base_url
            or environment.get("DEEPSEEK_BASE_URL")
            or environment.get("OPENAI_BASE_URL")
            or DEFAULT_DEEPSEEK_BASE_URL
        )
        return ProviderConfig(
            provider="deepseek",
            model=(model or DEFAULT_DEEPSEEK_MODEL).strip(),
            base_url=_normalize_base_url(resolved_url),
            api_key=api_key,
        )

    if provider_name == "ollama":
        if not model or not model.strip():
            raise ValueError("--model is required for provider=ollama")
        return ProviderConfig(
            provider="ollama",
            model=model.strip(),
            base_url=_normalize_base_url(base_url or DEFAULT_OLLAMA_BASE_URL),
            api_key="ollama",
        )

    raise ValueError(f"Unsupported provider: {provider}")

