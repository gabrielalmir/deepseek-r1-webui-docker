from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .batch import (
    build_checkpoint_metadata,
    file_digest,
    process_records,
)
from .engine import create_live_engine
from .excel import ExcelAdapter
from .optimizer import (
    load_prompt_artifact,
    optimize_prompt,
    save_prompt_artifact,
)
from .profile import load_profile
from .prompt import compile_default_prompt
from .providers import resolve_provider_config
from .schema import compile_schema


PROMPT_ARTIFACT_KEYS = {
    "profile_digest",
    "provider",
    "model",
    "base_url",
    "system_prompt",
    "user_prompt",
}


def _add_provider_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider", choices=("openai", "deepseek", "ollama"), default="openai"
    )
    parser.add_argument("--model")
    parser.add_argument("--base-url")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="structured-report",
        description="Generate prompts and extract profile-driven structured reports.",
    )
    groups = parser.add_subparsers(dest="group", required=True)

    profile_group = groups.add_parser("profile", help="Validate report profiles")
    profile_commands = profile_group.add_subparsers(dest="command", required=True)
    validate = profile_commands.add_parser("validate")
    validate.add_argument("profile", type=Path)

    prompt_group = groups.add_parser("prompt", help="Generate report prompts")
    prompt_commands = prompt_group.add_subparsers(dest="command", required=True)
    default = prompt_commands.add_parser("default")
    default.add_argument("profile", type=Path)
    default.add_argument("--output", type=Path)
    optimize = prompt_commands.add_parser("optimize")
    optimize.add_argument("profile", type=Path)
    optimize.add_argument("--output", required=True, type=Path)
    optimize.add_argument("--examples", type=Path)
    _add_provider_arguments(optimize)

    extract_group = groups.add_parser("extract", help="Extract structured reports")
    extract_commands = extract_group.add_subparsers(dest="command", required=True)
    text = extract_commands.add_parser("text")
    text.add_argument("profile", type=Path)
    text.add_argument("--input", type=Path)
    text.add_argument("--prompt", type=Path)
    text.add_argument("--max-retries", type=int, default=3)
    _add_provider_arguments(text)

    excel = extract_commands.add_parser("excel")
    excel.add_argument("profile", type=Path)
    excel.add_argument("--input", required=True, type=Path)
    excel.add_argument("--output", required=True, type=Path)
    excel.add_argument("--checkpoint", required=True, type=Path)
    excel.add_argument("--error-log", type=Path)
    excel.add_argument("--prompt", type=Path)
    excel.add_argument("--sheet-name", default="Sheet1")
    excel.add_argument("--id-column", default="patient_id")
    excel.add_argument("--report-column", default="Report")
    excel.add_argument("--row-limit", type=int)
    excel.add_argument("--max-retries", type=int, default=3)
    _add_provider_arguments(excel)
    return parser


def _provider_config(args: argparse.Namespace):
    return resolve_provider_config(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
    )


def _selected_prompt(profile, path: Path | None):
    if path is None:
        return compile_default_prompt(profile)
    return load_prompt_artifact(path, profile=profile)


def _write_json_or_print(path: Path | None, payload: Any) -> None:
    if path is None:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if path.suffix.lower() in {".yaml", ".yml"}:
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_examples(path: Path | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    if isinstance(payload, dict):
        payload = payload.get("examples")
    if not isinstance(payload, list):
        raise ValueError("examples file must contain a list")
    return payload


def _load_mapping_file(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _load_profile_for_cli(path: Path, parser: argparse.ArgumentParser):
    try:
        return load_profile(path)
    except ValidationError as error:
        payload = _load_mapping_file(path)
        if payload is not None and PROMPT_ARTIFACT_KEYS.issubset(payload):
            parser.error(
                "The first argument must be a Profile file, but this file looks "
                "like a prompt artifact. Pass the Profile as the positional "
                "argument and the optimized prompt with --prompt.\n"
                f"Example: structured-report extract excel examples/rectal_mri_esmo.yaml "
                f"--prompt {path} --input <input.xlsx> --output <output.xlsx> "
                f"--checkpoint <checkpoint.json>"
            )
        parser.error(f"Invalid Profile file {path}: {error}")
    except ValueError as error:
        parser.error(f"Invalid Profile file {path}: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    profile = _load_profile_for_cli(args.profile, parser)

    if args.group == "profile":
        compile_schema(profile)
        print(
            f"Valid profile: {profile.name} ({len(profile.fields)} fields) "
            f"digest={profile.digest()}"
        )
        return 0

    if args.group == "prompt" and args.command == "default":
        bundle = compile_default_prompt(profile)
        _write_json_or_print(args.output, bundle.model_dump())
        return 0

    if args.group == "prompt" and args.command == "optimize":
        artifact = optimize_prompt(
            profile,
            config=_provider_config(args),
            examples=_load_examples(args.examples),
        )
        save_prompt_artifact(args.output, artifact)
        print(f"Saved optimized prompt: {args.output}")
        return 0

    prompt = _selected_prompt(profile, args.prompt)
    config = _provider_config(args)
    engine = create_live_engine(
        profile,
        config=config,
        prompt=prompt,
        max_retries=args.max_retries,
    )

    if args.command == "text":
        report = (
            args.input.read_text(encoding="utf-8")
            if args.input is not None
            else sys.stdin.read()
        )
        print(json.dumps(engine.extract(report), ensure_ascii=False, indent=2))
        return 0

    if args.row_limit is not None and args.row_limit < 1:
        raise ValueError("row_limit must be at least 1")
    adapter = ExcelAdapter(
        sheet_name=args.sheet_name,
        id_column=args.id_column,
        report_column=args.report_column,
    )
    rows = adapter.read(args.input)
    if args.row_limit is not None:
        rows = rows[: args.row_limit]
    metadata = build_checkpoint_metadata(
        profile=profile,
        prompt=prompt,
        config=config,
        input_digest=file_digest(args.input),
    )

    def show_progress(completed: int, total: int, record_id: str) -> None:
        print(f"[{completed}/{total}] {record_id}", file=sys.stderr, flush=True)

    results = process_records(
        rows,
        engine,
        checkpoint_path=args.checkpoint,
        checkpoint_metadata=metadata,
        error_log_path=args.error_log,
        progress=show_progress,
    )
    adapter.write(
        args.input,
        args.output,
        profile=profile,
        rows=rows,
        results=results,
    )
    print(f"Completed {len(rows)} reports: {args.output}")
    return 0
