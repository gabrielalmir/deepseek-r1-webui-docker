from datetime import date

import pytest
from pydantic import ValidationError

from structured_reporting.profile import ReportProfile
from structured_reporting.schema import compile_schema
from structured_reporting.validators import register_validator


def make_profile():
    return ReportProfile.model_validate(
        {
            "version": 1,
            "name": "all-types",
            "base_prompt": "只提取原文事实。",
            "fields": [
                {
                    "id": "title",
                    "label": "标题",
                    "type": "text",
                    "rule": "原样提取标题",
                    "pattern": "^[A-Z]",
                    "min_length": 2,
                },
                {
                    "id": "category",
                    "label": "类别",
                    "type": "enum",
                    "rule": "选择类别",
                    "choices": ["A", "B"],
                },
                {
                    "id": "length",
                    "label": "长度",
                    "type": "number",
                    "rule": "换算为毫米",
                    "minimum": 0,
                    "maximum": 100,
                    "unit": "mm",
                    "unit_conversions": {"mm": 1, "cm": 10},
                },
                {
                    "id": "positive",
                    "label": "阳性",
                    "type": "boolean",
                    "rule": "明确阳性时为 true",
                },
                {
                    "id": "exam_date",
                    "label": "检查日期",
                    "type": "date",
                    "rule": "ISO 日期",
                },
                {
                    "id": "tags",
                    "label": "标签",
                    "type": "list",
                    "item_type": "text",
                    "rule": "提取标签",
                    "min_items": 1,
                    "max_items": 3,
                },
            ],
        }
    )


def valid_payload():
    return {
        "标题": "Alpha",
        "类别": "A",
        "长度": "6 cm",
        "阳性": True,
        "检查日期": "2026-06-15",
        "标签": ["one", "two"],
    }


def test_compiled_schema_preserves_labels_and_strong_types():
    model = compile_schema(make_profile())

    result = model.model_validate(valid_payload())

    assert result.model_dump(by_alias=True) == {
        "标题": "Alpha",
        "类别": "A",
        "长度": 60.0,
        "阳性": True,
        "检查日期": date(2026, 6, 15),
        "标签": ["one", "two"],
    }
    schema = model.model_json_schema(by_alias=True)
    assert list(schema["properties"]) == [
        "标题",
        "类别",
        "长度",
        "阳性",
        "检查日期",
        "标签",
    ]


def test_every_key_is_required_but_accepts_null():
    model = compile_schema(make_profile())
    payload = {label: None for label in ["标题", "类别", "长度", "阳性", "检查日期", "标签"]}

    result = model.model_validate(payload)
    assert result.model_dump(by_alias=True) == payload

    payload.pop("标题")
    with pytest.raises(ValidationError, match="Field required"):
        model.model_validate(payload)


def test_compiled_schema_rejects_extra_keys_and_constraint_violations():
    model = compile_schema(make_profile())
    extra = {**valid_payload(), "解释": "not allowed"}
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate(extra)

    invalid = {**valid_payload(), "类别": "C"}
    with pytest.raises(ValidationError):
        model.model_validate(invalid)

    invalid = {**valid_payload(), "长度": "11 cm"}
    with pytest.raises(ValidationError):
        model.model_validate(invalid)


def test_registered_validator_runs_after_builtin_normalization():
    register_validator(
        "test_uppercase",
        lambda value, field, profile: None if value is None else value.upper(),
    )
    profile = ReportProfile.model_validate(
        {
            "version": 1,
            "name": "validator",
            "base_prompt": "规则",
            "fields": [
                {
                    "id": "name",
                    "label": "名称",
                    "type": "text",
                    "rule": "规则",
                    "validators": ["test_uppercase"],
                }
            ],
        }
    )

    model = compile_schema(profile)

    assert model.model_validate({"名称": "alpha"}).model_dump(by_alias=True) == {
        "名称": "ALPHA"
    }


def test_unknown_registered_validator_is_rejected_when_compiling():
    profile = ReportProfile.model_validate(
        {
            "version": 1,
            "name": "validator",
            "base_prompt": "规则",
            "fields": [
                {
                    "id": "name",
                    "label": "名称",
                    "type": "text",
                    "rule": "规则",
                    "validators": ["missing_validator"],
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="missing_validator"):
        compile_schema(profile)
