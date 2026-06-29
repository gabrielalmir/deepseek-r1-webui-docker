import json

import pytest

from structured_reporting.batch import (
    CHECKPOINT_KIND,
    build_checkpoint_metadata,
    process_records,
    report_digest,
)
from structured_reporting.excel import ExcelRecord
from structured_reporting.profile import ReportProfile
from structured_reporting.prompt import compile_default_prompt
from structured_reporting.providers import ProviderConfig
from structured_reporting.schema import compile_schema


def make_profile():
    return ReportProfile.model_validate(
        {
            "version": 1,
            "name": "batch-demo",
            "base_prompt": "规则",
            "fields": [
                {
                    "id": "category",
                    "label": "类别",
                    "type": "enum",
                    "choices": ["A", "B"],
                    "rule": "规则",
                }
            ],
        }
    )


class FakeEngine:
    def __init__(self, responses):
        self.responses = list(responses)
        self.reports = []
        self.schema = compile_schema(make_profile())

    def extract(self, report):
        self.reports.append(report)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def metadata(input_digest="input-a"):
    profile = make_profile()
    return build_checkpoint_metadata(
        profile=profile,
        prompt=compile_default_prompt(profile),
        config=ProviderConfig(
            provider="openai",
            model="model",
            base_url="https://example.test/v1",
            api_key="secret",
        ),
        input_digest=input_digest,
    )


def records():
    return [
        ExcelRecord(row_number=2, record_id="same", report="first"),
        ExcelRecord(row_number=3, record_id="same", report="second"),
    ]


def test_duplicate_ids_are_checkpointed_by_row_and_report_digest(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    engine = FakeEngine([{"类别": "A"}, {"类别": "B"}])

    results = process_records(
        records(), engine, checkpoint_path=checkpoint, checkpoint_metadata=metadata()
    )

    assert results == [{"类别": "A"}, {"类别": "B"}]
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["kind"] == CHECKPOINT_KIND
    assert len(payload["results"]) == 2
    stored = list(payload["results"].values())
    assert {item["row_number"] for item in stored} == {2, 3}
    assert {item["report_digest"] for item in stored} == {
        report_digest("first"),
        report_digest("second"),
    }

    resumed = FakeEngine([])
    assert process_records(
        records(), resumed, checkpoint_path=checkpoint, checkpoint_metadata=metadata()
    ) == results
    assert resumed.reports == []


def test_checkpoint_metadata_change_is_rejected_before_processing(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    process_records(
        records()[:1],
        FakeEngine([{"类别": "A"}]),
        checkpoint_path=checkpoint,
        checkpoint_metadata=metadata("input-a"),
    )

    with pytest.raises(ValueError, match="metadata"):
        process_records(
            records()[:1],
            FakeEngine([]),
            checkpoint_path=checkpoint,
            checkpoint_metadata=metadata("input-b"),
        )


def test_legacy_checkpoint_is_rejected_explicitly(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps({"version": 2, "metadata": {}, "results": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="incompatible checkpoint"):
        process_records(
            [],
            FakeEngine([]),
            checkpoint_path=checkpoint,
            checkpoint_metadata=metadata(),
        )


def test_final_failure_writes_null_and_privacy_safe_error(tmp_path):
    report = "PRIVATE REPORT"
    error_log = tmp_path / "errors.jsonl"

    results = process_records(
        [ExcelRecord(row_number=8, record_id="patient", report=report)],
        FakeEngine([RuntimeError(f"failed for {report} with sk-secret")]),
        checkpoint_path=tmp_path / "checkpoint.json",
        checkpoint_metadata=metadata(),
        error_log_path=error_log,
    )

    assert results == [{"类别": None}]
    text = error_log.read_text(encoding="utf-8")
    assert report not in text
    assert "sk-secret" not in text
    record = json.loads(text)
    assert record["row_number"] == 8
    assert record["record_id"] == "patient"
