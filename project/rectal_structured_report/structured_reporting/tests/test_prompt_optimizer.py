from types import SimpleNamespace

import pytest
import yaml

from structured_reporting.optimizer import (
    PromptCandidate,
    PromptArtifact,
    load_prompt_artifact,
    optimize_prompt,
    save_prompt_artifact,
)
from structured_reporting.profile import ReportProfile


def make_profile(extra_rule=""):
    return ReportProfile.model_validate(
        {
            "version": 1,
            "name": "optimizer-demo",
            "base_prompt": f"严格依据原文。{extra_rule}",
            "fields": [
                {
                    "id": "category",
                    "label": "类别",
                    "type": "enum",
                    "choices": ["A", "B"],
                    "rule": "按原文选择。",
                },
                {
                    "id": "note",
                    "label": "备注",
                    "type": "text",
                    "rule": "原样提取。",
                },
            ],
        }
    )


class FakeRunnable:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    def invoke(self, payload):
        self.payloads.append(payload)
        return self.response


def config():
    return SimpleNamespace(
        provider="openai",
        model="prompt-model",
        base_url="https://example.test/v1",
        api_key="secret",
    )


def valid_candidate():
    return {
        "system_prompt": "请严格提取类别和备注，仅输出合法 JSON，不允许额外字段。",
        "user_prompt": "请处理以下报告：\n{report}",
    }


def test_optimizer_returns_profile_bound_artifact_and_passes_examples():
    runnable = FakeRunnable(valid_candidate())
    profile = make_profile()
    examples = [{"report": "示例", "output": {"类别": "A", "备注": None}}]

    artifact = optimize_prompt(
        profile,
        config=config(),
        runnable=runnable,
        examples=examples,
    )

    assert artifact.version == 1
    assert artifact.profile_digest == profile.digest()
    assert artifact.provider == "openai"
    assert artifact.model == "prompt-model"
    assert artifact.base_url == "https://example.test/v1"
    assert artifact.system_prompt == valid_candidate()["system_prompt"]
    assert artifact.prompt_digest()
    assert runnable.payloads[0]["examples"] == examples
    assert "default_system_prompt" in runnable.payloads[0]


def test_optimizer_rejects_candidate_that_changes_contract():
    runnable = FakeRunnable(
        {
            "system_prompt": "只提取类别并输出 JSON。",
            "user_prompt": "{report}",
        }
    )

    with pytest.raises(ValueError, match="备注"):
        optimize_prompt(make_profile(), config=config(), runnable=runnable)


def test_deepseek_style_candidate_alias_and_missing_user_prompt_use_default():
    spaced_system_prompt = (
        "请严格提取类 别和备 注，仅输出合法 JSON，不允许额外字段。"
    )
    runnable = FakeRunnable(
        {
            "optimized_system_prompt": spaced_system_prompt,
        }
    )
    profile = make_profile()

    artifact = optimize_prompt(profile, config=config(), runnable=runnable)

    assert artifact.system_prompt == spaced_system_prompt
    assert artifact.user_prompt == "报告原文：\n{report}"


def test_optimizer_uses_default_when_candidate_user_prompt_has_escaped_placeholder():
    runnable = FakeRunnable(
        {
            "system_prompt": valid_candidate()["system_prompt"],
            "user_prompt": "请处理以下报告：\n{{report}}",
        }
    )

    artifact = optimize_prompt(make_profile(), config=config(), runnable=runnable)

    assert artifact.system_prompt == valid_candidate()["system_prompt"]
    assert artifact.user_prompt == "报告原文：\n{report}"


def test_prompt_candidate_accepts_explicit_optimized_aliases():
    candidate = PromptCandidate.model_validate(
        {
            "optimized_system_prompt": valid_candidate()["system_prompt"],
            "optimized_user_prompt": "报告：\n{report}",
        }
    )

    assert candidate.system_prompt == valid_candidate()["system_prompt"]
    assert candidate.user_prompt == "报告：\n{report}"


def test_saved_artifact_rejects_a_different_profile(tmp_path):
    artifact = PromptArtifact.model_validate(
        {
            "version": 1,
            "profile_digest": make_profile().digest(),
            "provider": "openai",
            "model": "prompt-model",
            "base_url": "https://example.test/v1",
            **valid_candidate(),
        }
    )
    path = tmp_path / "prompt.json"
    save_prompt_artifact(path, artifact)

    loaded = load_prompt_artifact(path, profile=make_profile())
    assert loaded == artifact

    with pytest.raises(ValueError, match="different profile"):
        load_prompt_artifact(path, profile=make_profile("新增规则"))


def test_prompt_artifact_can_be_saved_and_loaded_as_yaml(tmp_path):
    artifact = PromptArtifact.model_validate(
        {
            "version": 1,
            "profile_digest": make_profile().digest(),
            "provider": "openai",
            "model": "prompt-model",
            "base_url": "https://example.test/v1",
            **valid_candidate(),
        }
    )
    path = tmp_path / "prompt.yaml"

    save_prompt_artifact(path, artifact)

    text = path.read_text(encoding="utf-8")
    assert "system_prompt:" in text
    assert not text.lstrip().startswith("{")
    raw = yaml.safe_load(text)
    assert raw["system_prompt"] == valid_candidate()["system_prompt"]
    assert raw["user_prompt"] == valid_candidate()["user_prompt"]
    assert load_prompt_artifact(path, profile=make_profile()) == artifact
