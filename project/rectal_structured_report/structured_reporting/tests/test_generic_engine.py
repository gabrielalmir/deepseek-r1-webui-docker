from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

import structured_reporting.engine as engine_module
from structured_reporting.engine import ExtractionEngine, create_live_engine
from structured_reporting.optimizer import PromptArtifact
from structured_reporting.profile import ReportProfile
from structured_reporting.providers import ProviderConfig
from structured_reporting.prompt import compile_default_prompt


def make_profile(rule="规则"):
    return ReportProfile.model_validate(
        {
            "version": 1,
            "name": "engine-demo",
            "base_prompt": rule,
            "fields": [
                {
                    "id": "category",
                    "label": "类别",
                    "type": "enum",
                    "choices": ["A", "B"],
                    "rule": "明确出现时选择。",
                },
                {
                    "id": "length",
                    "label": "长度",
                    "type": "number",
                    "unit": "mm",
                    "unit_conversions": {"mm": 1, "cm": 10},
                    "rule": "换算为毫米。",
                },
            ],
        }
    )


class FakeRunnable:
    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []

    def invoke(self, payload):
        self.payloads.append(payload)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_engine_passes_exact_report_and_returns_alias_keyed_dict():
    runnable = FakeRunnable([{"类别": "A", "长度": "2 cm"}])
    engine = ExtractionEngine(make_profile(), runnable=runnable, sleep=lambda _: None)

    result = engine.extract("原始报告")

    assert runnable.payloads == [{"report": "原始报告"}]
    assert result == {"类别": "A", "长度": 20.0}


def test_blank_report_returns_all_null_without_model_call():
    runnable = FakeRunnable([])
    engine = ExtractionEngine(make_profile(), runnable=runnable)

    assert engine.extract("  ") == {"类别": None, "长度": None}
    assert runnable.payloads == []


def test_validation_failure_is_retried_before_success():
    runnable = FakeRunnable(
        [
            {"类别": "C", "长度": 10},
            {"类别": "B", "长度": 10},
        ]
    )
    delays = []
    engine = ExtractionEngine(
        make_profile(), runnable=runnable, max_retries=2, sleep=delays.append
    )

    assert engine.extract("报告") == {"类别": "B", "长度": 10.0}
    assert delays == [1.0]


def test_engine_rejects_prompt_artifact_for_different_profile():
    profile = make_profile()
    bundle = compile_default_prompt(profile)
    artifact = PromptArtifact(
        version=1,
        profile_digest=make_profile("不同规则").digest(),
        provider="openai",
        model="model",
        base_url="https://example.test/v1",
        system_prompt=bundle.system_prompt,
        user_prompt=bundle.user_prompt,
    )

    with pytest.raises(ValueError, match="different profile"):
        ExtractionEngine(profile, runnable=FakeRunnable([]), prompt=artifact)


@pytest.mark.parametrize(
    ("provider", "method"),
    [("openai", "json_schema"), ("ollama", "json_schema"), ("deepseek", "json_mode")],
)
def test_live_engine_selects_provider_structured_output_method(
    monkeypatch, provider, method
):
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs

        def with_structured_output(self, schema, **kwargs):
            captured["schema"] = schema
            captured["structured_kwargs"] = kwargs
            return RunnableLambda(lambda _: {"类别": "A", "长度": 5})

    monkeypatch.setattr(engine_module, "ChatOpenAI", FakeChatOpenAI)
    config = ProviderConfig(
        provider=provider,
        model="model",
        base_url="http://localhost/v1",
        api_key="key",
    )

    engine = create_live_engine(make_profile(), config=config)

    assert engine.extract("报告") == {"类别": "A", "长度": 5.0}
    assert captured["structured_kwargs"] == {"method": method}
    assert captured["schema"].model_json_schema()["additionalProperties"] is False
