from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .excel import ExcelRecord
from .optimizer import PromptArtifact
from .profile import ReportProfile
from .prompt import PromptBundle
from .providers import ProviderConfig


CHECKPOINT_KIND = "structured-report-checkpoint"
CHECKPOINT_VERSION = 1
METADATA_KEYS = {
    "profile_digest",
    "prompt_digest",
    "provider",
    "model",
    "base_url",
    "input_digest",
}


def file_digest(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_digest(report: str) -> str:
    return hashlib.sha256(report.encode("utf-8")).hexdigest()


def _prompt_digest(prompt: PromptBundle | PromptArtifact) -> str:
    if isinstance(prompt, PromptArtifact):
        return prompt.prompt_digest()
    return prompt.digest()


def build_checkpoint_metadata(
    *,
    profile: ReportProfile,
    prompt: PromptBundle | PromptArtifact,
    config: ProviderConfig,
    input_digest: str,
) -> dict[str, str]:
    return {
        "profile_digest": profile.digest(),
        "prompt_digest": _prompt_digest(prompt),
        "provider": config.provider,
        "model": config.model,
        "base_url": config.base_url,
        "input_digest": input_digest,
    }


def _validate_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
    normalized = {str(key): str(value) for key, value in metadata.items()}
    if set(normalized) != METADATA_KEYS:
        raise ValueError("checkpoint metadata is incomplete")
    return normalized


def _record_key(record: ExcelRecord) -> str:
    material = (
        f"{record.row_number}\0{record.record_id}\0{report_digest(record.report)}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _load_checkpoint(
    path: Path,
    metadata: Mapping[str, str],
    schema: Any,
) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("incompatible checkpoint: invalid JSON") from error
    if payload.get("kind") != CHECKPOINT_KIND:
        raise ValueError("incompatible checkpoint format")
    if payload.get("version") != CHECKPOINT_VERSION:
        raise ValueError("incompatible checkpoint version")
    if payload.get("metadata") != dict(metadata):
        raise ValueError("checkpoint metadata does not match the current run")

    valid: dict[str, dict[str, Any]] = {}
    for key, stored in payload.get("results", {}).items():
        try:
            result = schema.model_validate(stored["result"])
            valid[str(key)] = {
                "row_number": int(stored["row_number"]),
                "record_id": str(stored["record_id"]),
                "report_digest": str(stored["report_digest"]),
                "result": result.model_dump(by_alias=True, mode="json"),
            }
        except Exception:
            continue
    return valid


def _save_checkpoint(
    path: Path,
    metadata: Mapping[str, str],
    results: Mapping[str, Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    payload = {
        "kind": CHECKPOINT_KIND,
        "version": CHECKPOINT_VERSION,
        "metadata": metadata,
        "results": results,
    }
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def _safe_error_message(error: Exception, report: str) -> str:
    message = str(error)
    if report:
        message = message.replace(report, "[REPORT REDACTED]")
    message = re.sub(r"sk-[A-Za-z0-9_-]+", "[API KEY REDACTED]", message)
    return message[:500]


def _append_error(path: Path, record: ExcelRecord, error: Exception) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "row_number": record.row_number,
        "record_id": record.record_id,
        "error_type": type(error).__name__,
        "message": _safe_error_message(error, record.report),
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def process_records(
    records: Sequence[ExcelRecord],
    engine: Any,
    *,
    checkpoint_path: str | Path,
    checkpoint_metadata: Mapping[str, str],
    error_log_path: str | Path | None = None,
    progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, Any]]:
    metadata = _validate_metadata(checkpoint_metadata)
    checkpoint = Path(checkpoint_path)
    stored = _load_checkpoint(checkpoint, metadata, engine.schema)
    output: list[dict[str, Any]] = []
    total = len(records)

    for completed, record in enumerate(records, start=1):
        key = _record_key(record)
        if key in stored:
            result = stored[key]["result"]
        else:
            try:
                result = engine.extract(record.report)
                validated = engine.schema.model_validate(result)
                result = validated.model_dump(by_alias=True, mode="json")
            except Exception as error:
                result = {
                    field.alias: None
                    for field in engine.schema.model_fields.values()
                }
                if error_log_path is not None:
                    _append_error(Path(error_log_path), record, error)
            stored[key] = {
                "row_number": record.row_number,
                "record_id": record.record_id,
                "report_digest": report_digest(record.report),
                "result": result,
            }
            _save_checkpoint(checkpoint, metadata, stored)
        output.append(result)
        if progress is not None:
            progress(completed, total, record.record_id)
    return output
