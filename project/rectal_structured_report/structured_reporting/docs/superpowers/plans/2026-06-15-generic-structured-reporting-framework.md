# Generic Structured Reporting Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed rectal MRI extraction pipeline with a YAML/JSON profile-driven Python package that generates prompts and extracts validated structured reports from text or Excel.

**Architecture:** `structured_reporting` owns profile loading, dynamic Pydantic schema compilation, prompt compilation/optimization, provider-backed extraction, checkpointing, and Excel orchestration. The old provider module becomes a compatibility re-export while the rectal MRI contract moves into an example profile. A packaged `structured-report` CLI exposes validation, prompt, text extraction, and Excel extraction workflows.

**Tech Stack:** Python 3, Pydantic 2, LangChain, langchain-openai, PyYAML, openpyxl, pytest.

---

### Task 1: Profile model and dynamic schema

**Files:**
- Create: `structured_reporting/profile.py`
- Create: `structured_reporting/schema.py`
- Create: `structured_reporting/validators.py`
- Test: `tests/test_generic_profile.py`
- Test: `tests/test_generic_schema.py`

- [x] Write tests for equivalent YAML/JSON loading, profile digests, field validation, six field types, required nullable keys, extra-key rejection, constraints, unit conversion, and registered validators.
- [x] Run the focused tests and confirm they fail because the package does not exist.
- [x] Implement versioned Pydantic profile models, safe YAML/JSON loading, canonical digests, validator registration, built-in normalization, and runtime model compilation with aliases matching output labels.
- [x] Run the focused tests and the existing schema tests.

### Task 2: Deterministic and optimized prompts

**Files:**
- Create: `structured_reporting/prompt.py`
- Create: `structured_reporting/optimizer.py`
- Test: `tests/test_generic_prompt.py`
- Test: `tests/test_prompt_optimizer.py`

- [x] Write tests for stable default prompts, complete field coverage, one `{report}` placeholder, optimizer artifact metadata, profile binding, and invalid candidate rejection.
- [x] Run the focused tests and confirm the expected missing-module failures.
- [x] Implement `PromptBundle`, deterministic prompt compilation, artifact loading/digests, candidate linting, and provider-backed prompt optimization with an injectable runnable boundary.
- [x] Run the focused tests.

### Task 3: Providers and extraction engine

**Files:**
- Create: `structured_reporting/providers.py`
- Create: `structured_reporting/engine.py`
- Modify: `rectal_mri_structuring/providers.py`
- Test: `tests/test_generic_engine.py`
- Modify: `tests/test_providers.py`

- [x] Write tests for exact report injection, blank reports, retries, dynamic validation, artifact/profile mismatch, and provider-specific structured-output methods.
- [x] Run focused tests and confirm failures.
- [x] Move provider configuration into the generic package, retain legacy re-exports, and implement `ExtractionEngine` plus live LangChain construction.
- [x] Run generic engine, provider, and legacy parser tests.

### Task 4: Excel and checkpointed batch processing

**Files:**
- Create: `structured_reporting/excel.py`
- Create: `structured_reporting/batch.py`
- Test: `tests/test_generic_excel.py`
- Test: `tests/test_generic_batch.py`

- [x] Write tests for custom sheet/header selection, appending after the last header, source formatting preservation, null display values, duplicate IDs, metadata invalidation, report hashes, and privacy-safe errors.
- [x] Run focused tests and confirm failures.
- [x] Implement the configurable openpyxl adapter, input digesting, versioned checkpoint contract, resumable processing, and atomic saves.
- [x] Run focused tests and legacy Excel/batch tests.

### Task 5: CLI, packaging, example, and documentation

**Files:**
- Create: `structured_reporting/cli.py`
- Create: `structured_reporting/__init__.py`
- Create: `structured_report.py`
- Create: `examples/rectal_mri.yaml`
- Create: `pyproject.toml`
- Modify: `requirements.txt`
- Modify: `README.md`
- Test: `tests/test_generic_cli.py`
- Test: `tests/test_rectal_mri_profile.py`

- [x] Write tests for all five command paths and the migrated seven-field profile.
- [x] Run focused tests and confirm failures.
- [x] Implement nested argparse commands, console packaging, profile/prompt file I/O, text/stdin extraction, Excel orchestration, and the complete rectal MRI example.
- [x] Update installation and usage documentation and explicitly document legacy CLI/checkpoint incompatibility.
- [x] Run CLI/example tests, `--help`, all tests, and an offline synthetic end-to-end smoke test.

### Task 6: Final review and verification

- [x] Review the implementation against every approved requirement and inspect the workspace diff/file list.
- [x] Run the complete test suite fresh and verify zero failures.
- [x] Run compile/import checks and a temporary-workbook smoke test without a paid API.
- [x] Record any unavailable online smoke test or Git operation explicitly in the final report.
