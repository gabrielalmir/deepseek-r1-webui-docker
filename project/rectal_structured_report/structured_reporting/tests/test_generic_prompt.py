import pytest

from structured_reporting.profile import ReportProfile
from structured_reporting.prompt import PromptBundle, compile_default_prompt, validate_prompt_bundle


def make_profile():
    return ReportProfile.model_validate(
        {
            "version": 1,
            "name": "prompt-demo",
            "base_prompt": "严格依据报告原文，不要推测。",
            "fields": [
                {
                    "id": "category",
                    "label": "类别",
                    "type": "enum",
                    "choices": ["A", "B"],
                    "rule": "只能选择明确出现的类别。",
                },
                {
                    "id": "length",
                    "label": "长度",
                    "type": "number",
                    "unit": "mm",
                    "unit_conversions": {"mm": 1, "cm": 10},
                    "minimum": 0,
                    "rule": "提取长度并换算为毫米。",
                },
            ],
        }
    )


def test_default_prompt_is_deterministic_and_covers_the_contract():
    first = compile_default_prompt(make_profile())
    second = compile_default_prompt(make_profile())

    assert first == second
    assert first.digest() == second.digest()
    assert first.user_prompt == "报告原文：\n{report}"
    assert first.user_prompt.count("{report}") == 1
    assert "严格依据报告原文，不要推测。" in first.system_prompt
    assert "类别" in first.system_prompt
    assert "A、B" in first.system_prompt
    assert "长度" in first.system_prompt
    assert "目标单位 mm" in first.system_prompt
    assert '"类别": null' in first.system_prompt
    assert '"长度": null' in first.system_prompt
    assert "不允许额外字段" in first.system_prompt


@pytest.mark.parametrize(
    "user_prompt",
    ["没有占位符", "{report} 和 {report}", "{report} {patient_id}"],
)
def test_prompt_bundle_requires_exactly_one_report_placeholder(user_prompt):
    bundle = PromptBundle(system_prompt="类别 长度 JSON", user_prompt=user_prompt)

    with pytest.raises(ValueError, match="report"):
        validate_prompt_bundle(make_profile(), bundle)


def test_prompt_bundle_requires_every_output_label():
    bundle = PromptBundle(
        system_prompt="只输出类别 JSON，不允许额外字段",
        user_prompt="{report}",
    )

    with pytest.raises(ValueError, match="长度"):
        validate_prompt_bundle(make_profile(), bundle)

