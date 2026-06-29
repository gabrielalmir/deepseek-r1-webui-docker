import json

import pytest
from pydantic import ValidationError

from structured_reporting.profile import ReportProfile, load_profile


PROFILE = {
    "version": 1,
    "name": "demo",
    "language": "zh-CN",
    "base_prompt": "严格依据原文。",
    "missing": {"excel_value": "None"},
    "fields": [
        {
            "id": "category",
            "label": "类别",
            "type": "enum",
            "choices": ["A", "B"],
            "rule": "只选择明确出现的类别。",
        }
    ],
}


def test_yaml_and_json_load_to_the_same_profile(tmp_path):
    yaml_path = tmp_path / "profile.yaml"
    yaml_path.write_text(
        """version: 1
name: demo
language: zh-CN
base_prompt: 严格依据原文。
missing:
  excel_value: None
fields:
  - id: category
    label: 类别
    type: enum
    choices: [A, B]
    rule: 只选择明确出现的类别。
""",
        encoding="utf-8",
    )
    json_path = tmp_path / "profile.json"
    json_path.write_text(json.dumps(PROFILE, ensure_ascii=False), encoding="utf-8")

    from_yaml = load_profile(yaml_path)
    from_json = load_profile(json_path)

    assert from_yaml == from_json
    assert from_yaml.digest() == from_json.digest()


def test_profile_rejects_duplicate_ids_and_labels():
    duplicate = dict(PROFILE)
    duplicate["fields"] = [PROFILE["fields"][0], PROFILE["fields"][0]]

    with pytest.raises(ValidationError, match="unique"):
        ReportProfile.model_validate(duplicate)


@pytest.mark.parametrize("field_id", ["肿瘤", "bad-id", "1field"])
def test_profile_requires_stable_ascii_field_ids(field_id):
    invalid = dict(PROFILE)
    invalid["fields"] = [{**PROFILE["fields"][0], "id": field_id}]

    with pytest.raises(ValidationError):
        ReportProfile.model_validate(invalid)


def test_enum_requires_choices_and_number_unit_requires_conversions():
    invalid_enum = dict(PROFILE)
    invalid_enum["fields"] = [
        {"id": "category", "label": "类别", "type": "enum", "rule": "规则"}
    ]
    with pytest.raises(ValidationError, match="choices"):
        ReportProfile.model_validate(invalid_enum)

    invalid_number = dict(PROFILE)
    invalid_number["fields"] = [
        {
            "id": "length",
            "label": "长度",
            "type": "number",
            "rule": "规则",
            "unit": "mm",
            "unit_conversions": {"cm": 10},
        }
    ]
    with pytest.raises(ValidationError, match="target unit"):
        ReportProfile.model_validate(invalid_number)


def test_load_profile_rejects_unknown_extension(tmp_path):
    path = tmp_path / "profile.txt"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML or JSON"):
        load_profile(path)

