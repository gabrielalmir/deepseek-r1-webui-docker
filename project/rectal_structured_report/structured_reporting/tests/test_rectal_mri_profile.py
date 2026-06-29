from pathlib import Path

from structured_reporting.profile import load_profile
from structured_reporting.prompt import compile_default_prompt
from structured_reporting.schema import compile_schema


PROFILE_PATH = Path(__file__).parents[1] / "examples" / "rectal_mri.yaml"


def test_rectal_mri_example_contains_the_complete_seven_field_contract():
    profile = load_profile(PROFILE_PATH)

    assert [field.label for field in profile.fields] == [
        "肿瘤的位置",
        "肿瘤累及长度",
        "肿瘤浸润深度",
        "直肠系膜内淋巴结评估",
        "直肠系膜外淋巴结评估",
        "CRM受累情况",
        "EMVI受累情况",
    ]
    assert profile.fields[1].type == "number"
    assert profile.fields[1].unit == "mm"
    assert profile.missing.excel_value == "None"


def test_rectal_mri_prompt_preserves_domain_thresholds_and_schema():
    profile = load_profile(PROFILE_PATH)
    prompt = compile_default_prompt(profile)

    for text in ["短径大于等于7mm", "距离小于等于1mm", "仅描述“血管增多”"]:
        assert text in prompt.system_prompt
    schema = compile_schema(profile)
    result = schema.model_validate(
        {
            "肿瘤的位置": "中下段",
            "肿瘤累及长度": "6 cm",
            "肿瘤浸润深度": "T3",
            "直肠系膜内淋巴结评估": "有",
            "直肠系膜外淋巴结评估": None,
            "CRM受累情况": "无",
            "EMVI受累情况": None,
        }
    )
    assert result.model_dump(by_alias=True)["肿瘤累及长度"] == 60.0
