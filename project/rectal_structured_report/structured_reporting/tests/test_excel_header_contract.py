from structured_reporting.profile import ReportProfile
from structured_reporting.schema import compile_schema


def test_excel_header_does_not_change_the_json_output_key():
    profile = ReportProfile.model_validate(
        {
            "version": 1,
            "name": "header-contract",
            "base_prompt": "规则",
            "fields": [
                {
                    "id": "length",
                    "label": "长度",
                    "excel_header": "长度(mm)",
                    "type": "number",
                    "rule": "规则",
                }
            ],
        }
    )

    model = compile_schema(profile)

    assert model.model_validate({"长度": 10}).model_dump(by_alias=True) == {
        "长度": 10.0
    }
    assert profile.fields[0].excel_label == "长度(mm)"
