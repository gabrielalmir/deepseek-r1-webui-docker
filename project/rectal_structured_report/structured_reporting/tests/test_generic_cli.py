import json
from pathlib import Path

import pytest
import yaml

import structured_reporting.cli as cli_module
from structured_reporting.cli import main
from structured_reporting.excel import ExcelRecord
from structured_reporting.optimizer import PromptArtifact
from structured_reporting.profile import load_profile
from structured_reporting.providers import ProviderConfig


def write_profile(path):
    path.write_text(
        """version: 1
name: cli-demo
base_prompt: 严格依据原文。
fields:
  - id: category
    label: 类别
    type: enum
    choices: [A, B]
    rule: 按原文选择。
""",
        encoding="utf-8",
    )


def fake_config():
    return ProviderConfig(
        provider="openai",
        model="model",
        base_url="https://example.test/v1",
        api_key="secret",
    )


def test_profile_validate_command(tmp_path, capsys):
    profile_path = tmp_path / "profile.yaml"
    write_profile(profile_path)

    assert main(["profile", "validate", str(profile_path)]) == 0

    output = capsys.readouterr().out
    assert "cli-demo" in output
    assert "1 fields" in output


def test_prompt_default_command_writes_json(tmp_path):
    profile_path = tmp_path / "profile.yaml"
    output_path = tmp_path / "prompt.json"
    write_profile(profile_path)

    assert main(
        ["prompt", "default", str(profile_path), "--output", str(output_path)]
    ) == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert "类别" in payload["system_prompt"]
    assert payload["user_prompt"] == "报告原文：\n{report}"


def test_prompt_default_command_writes_yaml_when_requested(tmp_path):
    profile_path = tmp_path / "profile.yaml"
    output_path = tmp_path / "prompt.yaml"
    write_profile(profile_path)

    assert main(
        ["prompt", "default", str(profile_path), "--output", str(output_path)]
    ) == 0

    text = output_path.read_text(encoding="utf-8")
    assert "system_prompt:" in text
    assert not text.lstrip().startswith("{")
    payload = yaml.safe_load(text)
    assert "类别" in payload["system_prompt"]
    assert payload["user_prompt"] == "报告原文：\n{report}"


def test_prompt_optimize_command_saves_artifact(tmp_path, monkeypatch):
    profile_path = tmp_path / "profile.yaml"
    output_path = tmp_path / "optimized.json"
    write_profile(profile_path)
    profile = load_profile(profile_path)

    monkeypatch.setattr(cli_module, "resolve_provider_config", lambda **_: fake_config())
    monkeypatch.setattr(
        cli_module,
        "optimize_prompt",
        lambda profile, **_: PromptArtifact(
            version=1,
            profile_digest=profile.digest(),
            provider="openai",
            model="model",
            base_url="https://example.test/v1",
            system_prompt="提取类别并输出 JSON，不允许额外字段。",
            user_prompt="{report}",
        ),
    )

    assert main(
        [
            "prompt",
            "optimize",
            str(profile_path),
            "--output",
            str(output_path),
        ]
    ) == 0

    artifact = PromptArtifact.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert artifact.profile_digest == profile.digest()


def test_prompt_optimize_command_saves_yaml_artifact(tmp_path, monkeypatch):
    profile_path = tmp_path / "profile.yaml"
    output_path = tmp_path / "optimized.yaml"
    write_profile(profile_path)
    profile = load_profile(profile_path)

    monkeypatch.setattr(cli_module, "resolve_provider_config", lambda **_: fake_config())
    monkeypatch.setattr(
        cli_module,
        "optimize_prompt",
        lambda profile, **_: PromptArtifact(
            version=1,
            profile_digest=profile.digest(),
            provider="openai",
            model="model",
            base_url="https://example.test/v1",
            system_prompt="提取类别并输出 JSON，不允许额外字段。",
            user_prompt="{report}",
        ),
    )

    assert main(
        [
            "prompt",
            "optimize",
            str(profile_path),
            "--output",
            str(output_path),
        ]
    ) == 0

    text = output_path.read_text(encoding="utf-8")
    assert "system_prompt:" in text
    assert not text.lstrip().startswith("{")
    artifact = yaml.safe_load(text)
    assert artifact["profile_digest"] == profile.digest()
    assert artifact["system_prompt"] == "提取类别并输出 JSON，不允许额外字段。"


def test_extract_text_command_reads_file_and_prints_json(tmp_path, monkeypatch, capsys):
    profile_path = tmp_path / "profile.yaml"
    report_path = tmp_path / "report.txt"
    write_profile(profile_path)
    report_path.write_text("synthetic report", encoding="utf-8")
    captured = {}

    class FakeEngine:
        def extract(self, report):
            captured["report"] = report
            return {"类别": "A"}

    monkeypatch.setattr(cli_module, "resolve_provider_config", lambda **_: fake_config())
    monkeypatch.setattr(cli_module, "create_live_engine", lambda *_, **__: FakeEngine())

    assert main(
        [
            "extract",
            "text",
            str(profile_path),
            "--input",
            str(report_path),
        ]
    ) == 0

    assert captured["report"] == "synthetic report"
    assert json.loads(capsys.readouterr().out) == {"类别": "A"}


def test_prompt_artifact_in_profile_position_gives_actionable_error(
    tmp_path, capsys
):
    artifact_path = tmp_path / "optimized.prompt.json"
    artifact_path.write_text(
        json.dumps(
            {
                "version": 1,
                "profile_digest": "digest",
                "provider": "openai",
                "model": "model",
                "base_url": "https://example.test/v1",
                "system_prompt": "类别 JSON 不允许额外字段",
                "user_prompt": "{report}",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as error:
        main(["extract", "text", str(artifact_path)])

    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert "looks like a prompt artifact" in stderr
    assert "--prompt" in stderr


def test_extract_excel_command_orchestrates_batch_and_write(
    tmp_path, monkeypatch
):
    profile_path = tmp_path / "profile.yaml"
    source = tmp_path / "source.xlsx"
    output = tmp_path / "output.xlsx"
    checkpoint = tmp_path / "checkpoint.json"
    write_profile(profile_path)
    source.write_bytes(b"source")
    captured = {}
    rows = [ExcelRecord(row_number=2, record_id="1", report="report")]

    class FakeAdapter:
        def __init__(self, **kwargs):
            captured["adapter_kwargs"] = kwargs

        def read(self, path):
            captured["read_path"] = Path(path)
            return rows

        def write(self, input_path, output_path, **kwargs):
            captured["write"] = (Path(input_path), Path(output_path), kwargs)

    class FakeEngine:
        schema = object()

    monkeypatch.setattr(cli_module, "ExcelAdapter", FakeAdapter)
    monkeypatch.setattr(cli_module, "resolve_provider_config", lambda **_: fake_config())
    monkeypatch.setattr(cli_module, "create_live_engine", lambda *_, **__: FakeEngine())
    monkeypatch.setattr(cli_module, "file_digest", lambda _: "input-digest")
    monkeypatch.setattr(cli_module, "build_checkpoint_metadata", lambda **_: {"meta": "data"})
    monkeypatch.setattr(
        cli_module,
        "process_records",
        lambda records, engine, **kwargs: [{"类别": "B"}],
    )

    assert main(
        [
            "extract",
            "excel",
            str(profile_path),
            "--input",
            str(source),
            "--output",
            str(output),
            "--checkpoint",
            str(checkpoint),
            "--sheet-name",
            "Data",
            "--id-column",
            "case_id",
            "--report-column",
            "text",
        ]
    ) == 0

    assert captured["adapter_kwargs"] == {
        "sheet_name": "Data",
        "id_column": "case_id",
        "report_column": "text",
    }
    assert captured["write"][2]["results"] == [{"类别": "B"}]
