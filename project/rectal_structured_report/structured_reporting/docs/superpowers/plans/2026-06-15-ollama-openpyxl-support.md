# Ollama and openpyxl Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Ollama OpenAI-compatible provider while replacing the Node.js XLSX adapter with a style-preserving Python openpyxl adapter.

**Architecture:** A new provider configuration module resolves validated OpenAI or Ollama connection settings before constructing the existing LangChain `ChatOpenAI` parser. Checkpoint version 2 binds cached results to provider, model, and base URL. A new openpyxl adapter owns workbook input/output and preserves the source columns, dimensions, and styles while appending the seven output columns.

**Tech Stack:** Python 3, LangChain, `langchain-openai`, Pydantic, openpyxl, pytest.

---

### Task 1: Provider configuration

**Files:**
- Create: `rectal_mri_structuring/providers.py`
- Modify: `rectal_mri_structuring/parser.py`
- Test: `tests/test_providers.py`
- Test: `tests/test_parser.py`

- [x] **Step 1: Write failing provider tests**

Test these exact behaviors:

```python
def test_openai_defaults_require_api_key(monkeypatch): ...
def test_openai_uses_existing_defaults(monkeypatch): ...
def test_ollama_uses_placeholder_key_and_default_url(monkeypatch): ...
def test_ollama_requires_explicit_model(monkeypatch): ...
def test_base_url_trailing_slash_is_removed(monkeypatch): ...
```

The resolved object must expose `provider`, `model`, `base_url`, and `api_key`.

- [x] **Step 2: Run provider tests and verify RED**

Run: `rtk .venv/bin/python -m pytest tests/test_providers.py -q`

Expected: collection fails because `rectal_mri_structuring.providers` does not exist.

- [x] **Step 3: Implement `ProviderConfig` and `resolve_provider_config`**

Use a frozen dataclass. Accepted providers are only `openai` and `ollama`. OpenAI resolves model `gpt-5.4`, `OPENAI_BASE_URL` or `https://apinebula.com/v1`, and requires `OPENAI_API_KEY`. Ollama resolves base URL `http://localhost:11434/v1`, uses key `ollama`, and raises when the caller did not explicitly provide a model.

- [x] **Step 4: Refactor parser construction to accept `ProviderConfig`**

Change `create_live_parser` to accept a `ProviderConfig`, then pass its model, URL, and key to `ChatOpenAI`. Keep `method="json_schema"`, temperature 0, timeout 120, and existing retry behavior.

- [x] **Step 5: Run provider and parser tests and verify GREEN**

Run: `rtk .venv/bin/python -m pytest tests/test_providers.py tests/test_parser.py -q`

Expected: all tests pass.

### Task 2: Checkpoint version 2 isolation

**Files:**
- Modify: `rectal_mri_structuring/batch.py`
- Test: `tests/test_batch.py`

- [x] **Step 1: Write failing checkpoint metadata tests**

Add tests for:

```python
def test_saves_version_two_checkpoint_with_metadata(tmp_path): ...
def test_resumes_matching_version_two_checkpoint(tmp_path): ...
def test_rejects_mismatched_version_two_checkpoint(tmp_path): ...
def test_accepts_legacy_v1_only_for_default_openai(tmp_path): ...
def test_rejects_legacy_v1_for_ollama(tmp_path): ...
```

Use metadata dictionaries with exactly `provider`, `model`, and `base_url`.

- [x] **Step 2: Run batch tests and verify RED**

Run: `rtk .venv/bin/python -m pytest tests/test_batch.py -q`

Expected: metadata assertions fail because current checkpoints are version 1.

- [x] **Step 3: Implement checkpoint metadata validation**

Set `CHECKPOINT_VERSION = 2`. Change `process_rows` to require `checkpoint_metadata`. `_load_checkpoint` must return valid results only after metadata validation. Version 1 is accepted only when metadata equals the default OpenAI triple. `_save_checkpoint` writes version 2, metadata, and results atomically.

- [x] **Step 4: Run batch tests and verify GREEN**

Run the Task 2 pytest command. Expected: all tests pass.

### Task 3: Pure Python openpyxl workbook adapter

**Files:**
- Create: `rectal_mri_structuring/excel.py`
- Create: `tests/test_excel.py`
- Modify: `requirements.txt`

- [x] **Step 1: Add openpyxl dependency**

Append `openpyxl>=3.1,<4` to `requirements.txt` and install it in `.venv`.

- [x] **Step 2: Write failing workbook adapter tests**

Build a temporary source workbook with styled A/B headers, custom A/B widths, custom data row heights, and two source rows. Test:

```python
def test_reads_source_rows_in_order(tmp_path): ...
def test_rejects_missing_sheet_or_headers(tmp_path): ...
def test_write_preserves_source_values_styles_widths_and_heights(tmp_path): ...
def test_write_appends_headers_and_results_with_expected_format(tmp_path): ...
def test_write_freezes_first_row_and_two_source_columns(tmp_path): ...
```

Expected output must have `freeze_panes == "C2"`, C-I widths set to 22, wrapped/top-aligned result cells, and styled output headers.

- [x] **Step 3: Run Excel tests and verify RED**

Run: `rtk .venv/bin/python -m pytest tests/test_excel.py -q`

Expected: collection fails because `rectal_mri_structuring.excel` does not exist.

- [x] **Step 4: Implement `OpenpyxlAdapter`**

Implement `read(input_path)` and `write(input_path, output_path, headers, result_rows)`. Load and save normal workbooks, validate `Sheet1`, preserve A/B cells and dimensions, write C-I, style output headers with `1F4E78` fill and white bold font, set C-I width to 22, apply wrapped top alignment, set `freeze_panes = "C2"`, and create output directories.

- [x] **Step 5: Run Excel tests and verify GREEN**

Run the Task 3 pytest command. Expected: all tests pass.

### Task 4: CLI integration and Node.js removal

**Files:**
- Modify: `rectal_mri_structuring/cli.py`
- Modify: `tests/test_cli.py`
- Delete: `scripts/xlsx_adapter.mjs`
- Delete: `node_modules`

- [x] **Step 1: Write failing CLI tests**

Test that `--provider` defaults to `openai`, accepts `ollama`, OpenAI keeps current defaults, Ollama requires explicit `--model`, Ollama succeeds without `OPENAI_API_KEY`, and the parser receives the resolved provider configuration. Assert `--node-bin` and `--adapter-script` are rejected as unknown arguments.

- [x] **Step 2: Run CLI tests and verify RED**

Run: `rtk .venv/bin/python -m pytest tests/test_cli.py -q`

Expected: new provider assertions fail and Node parameters remain accepted.

- [x] **Step 3: Integrate provider and openpyxl adapter**

Add `--provider` with choices `openai`, `ollama`. Change `--model` and `--base-url` defaults to `None` so provider resolution can distinguish explicit values. Resolve configuration in `main`, construct `OpenpyxlAdapter`, pass checkpoint metadata into `run_pipeline`, and remove Node-related constants, imports, subprocess code, and arguments.

- [x] **Step 4: Delete JavaScript and node_modules link**

Remove `scripts/xlsx_adapter.mjs` with `apply_patch`. Remove the root `node_modules` symlink only after confirming it is a symlink to the bundled runtime and is not needed by another project file.

- [x] **Step 5: Run CLI and full tests and verify GREEN**

Run:

```bash
rtk .venv/bin/python -m pytest tests/test_cli.py -q
rtk .venv/bin/python -m pytest -q
```

Expected: all tests pass.

### Task 5: Documentation and regression workbook

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-06-12-rectal-mri-llm-structuring.md`
- Create during verification: `/tmp/openpyxl-regression.xlsx`

- [x] **Step 1: Rewrite setup documentation as Python-only**

Remove Node.js and artifact-tool sections and parameters. Document `openpyxl`, `--provider`, OpenAI setup, Ollama startup, `ollama pull`, `ollama list`, Ollama smoke/full commands, and checkpoint isolation.

- [x] **Step 2: Verify CLI help matches README**

Run: `rtk .venv/bin/python run_structuring.py --help`

Expected: help contains `--provider` and no Node-related arguments.

- [x] **Step 3: Run a no-model workbook regression using existing checkpoint results**

Load the existing version 1 OpenAI checkpoint with default OpenAI metadata, skip all 225 model calls, and write `/tmp/openpyxl-regression.xlsx`. Verify the source workbook hash remains unchanged.

- [x] **Step 4: Inspect regression workbook with openpyxl**

Verify 226 rows, 9 columns, exact headers, source-column equality, original A/B widths, all original row heights, C-I width 22, and `freeze_panes == "C2"`. Scan all seven result columns against existing schema rules.

- [x] **Step 5: Run final verification**

Run:

```bash
rtk .venv/bin/python -m pytest -q
rtk rg -n "artifact-tool|xlsx_adapter|node-bin|adapter-script|Node.js" . -g '!docs/superpowers/plans/2026-06-12-rectal-mri-llm-structuring.md' -g '!docs/superpowers/specs/2026-06-15-ollama-openai-compatible-support-design.md' -g '!*.xlsx' -g '!.venv/**'
```

Expected: tests pass and no active code or README Node.js references remain.
