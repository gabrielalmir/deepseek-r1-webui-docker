import pytest

from structured_reporting.providers import resolve_provider_config


def test_openai_defaults_require_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        resolve_provider_config(provider="openai")


def test_openai_uses_existing_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config = resolve_provider_config(provider="openai")

    assert config.provider == "openai"
    assert config.model == "gpt-5.4"
    assert config.base_url == "https://apinebula.com/v1"
    assert config.api_key == "test-key"


def test_openai_uses_environment_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1/")

    config = resolve_provider_config(provider="openai")

    assert config.base_url == "https://example.test/v1"


def test_openai_auto_detects_deepseek_compatible_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

    config = resolve_provider_config(provider="openai")

    assert config.provider == "deepseek"
    assert config.model == "deepseek-v4-flash"
    assert config.base_url == "https://api.deepseek.com/v1"
    assert config.api_key == "test-key"


def test_deepseek_provider_supports_dedicated_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config = resolve_provider_config(provider="deepseek")

    assert config.provider == "deepseek"
    assert config.model == "deepseek-v4-flash"
    assert config.base_url == "https://api.deepseek.com"
    assert config.api_key == "deepseek-key"


def test_ollama_uses_placeholder_key_and_default_url(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    config = resolve_provider_config(provider="ollama", model="qwen3:8b")

    assert config.provider == "ollama"
    assert config.model == "qwen3:8b"
    assert config.base_url == "http://localhost:11434/v1"
    assert config.api_key == "ollama"


def test_ollama_requires_explicit_model(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="--model is required"):
        resolve_provider_config(provider="ollama")


def test_base_url_trailing_slash_is_removed(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = resolve_provider_config(
        provider="ollama",
        model="qwen3:8b",
        base_url="http://ollama.internal:11434/v1///",
    )

    assert config.base_url == "http://ollama.internal:11434/v1"


def test_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        resolve_provider_config(provider="local")
