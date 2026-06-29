# Rectal MRI LLM Structuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a resumable LangChain pipeline that extracts seven evidence-bound rectal MRI features from 225 reports and appends them to a copy of the original workbook.

**Architecture:** A Python package owns the constrained Pydantic schema, normalization, LangChain invocation, batch checkpointing, and workbook orchestration. A small JavaScript adapter using the bundled `@oai/artifact-tool` performs the required XLSX import/export without changing the original two columns. Tests replace the live model and XLSX adapter at boundaries so clinical rules, retries, and resume behavior are deterministic.

**Tech Stack:** Python 3, LangChain, `langchain-openai`, Pydantic, pytest, Node.js, `@oai/artifact-tool`.

---

### Task 1: Schema and deterministic normalization

**Files:**
- Create: `rectal_mri_structuring/__init__.py`
- Create: `rectal_mri_structuring/schema.py`
- Test: `tests/test_schema.py`

- [x] **Step 1: Write failing schema tests**

Test that only approved categorical values are accepted, `6.0cm` becomes `60mm`, `23.7mm` remains `23.7mm`, and absent or invalid lengths become `None`.

- [x] **Step 2: Run the schema tests and verify RED**

Run: `rtk /Users/chenjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/test_schema.py -q`

Expected: collection fails because `rectal_mri_structuring.schema` does not exist.

- [x] **Step 3: Implement the constrained Pydantic model**

Define `RectalMRIExtraction` with aliases matching the seven Chinese output headers. Add a field validator that normalizes the length to `数字mm` and rejects values that cannot represent tumor involved length. Add `as_row()` to return values in workbook column order.

- [x] **Step 4: Run schema tests and verify GREEN**

Run the Task 1 pytest command. Expected: all tests pass.

### Task 2: Prompt and LangChain parser

**Files:**
- Create: `rectal_mri_structuring/prompt.py`
- Create: `rectal_mri_structuring/parser.py`
- Test: `tests/test_parser.py`

- [x] **Step 1: Write failing parser tests**

Use a fake structured runnable to verify that the exact report is passed to the model, empty reports return seven `None` values without a model call, and transient exceptions are retried before succeeding.

- [x] **Step 2: Run parser tests and verify RED**

Run: `rtk /Users/chenjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/test_parser.py -q`

Expected: collection fails because the parser module does not exist.

- [x] **Step 3: Implement prompt construction and parser**

Create the full Chinese medical system prompt from the approved design. Build `ChatOpenAI(model="gpt-5.4", base_url=..., api_key=..., temperature=0)` and call `with_structured_output(RectalMRIExtraction)`. Implement bounded exponential backoff and return all-`None` for blank reports.

- [x] **Step 4: Run parser tests and verify GREEN**

Run the Task 2 pytest command. Expected: all tests pass.

### Task 3: Resumable batch processor

**Files:**
- Create: `rectal_mri_structuring/batch.py`
- Test: `tests/test_batch.py`

- [x] **Step 1: Write failing batch tests**

Test that rows are processed in order, completed checkpoint entries are skipped, failures receive seven `None` values, and error records contain row number and patient ID but not report text.

- [x] **Step 2: Run batch tests and verify RED**

Run: `rtk /Users/chenjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/test_batch.py -q`

Expected: collection fails because the batch module does not exist.

- [x] **Step 3: Implement JSON checkpoint processing**

Store a versioned JSON object keyed by patient ID with the seven output values. Save atomically after each processed row. On restart, accept only checkpoint rows containing all seven valid keys. Write a separate privacy-safe JSON Lines error log.

- [x] **Step 4: Run batch tests and verify GREEN**

Run the Task 3 pytest command. Expected: all tests pass.

### Task 4: XLSX adapter and orchestration CLI

**Files:**
- Create: `scripts/xlsx_adapter.mjs`
- Create: `rectal_mri_structuring/cli.py`
- Create: `run_structuring.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Write failing orchestration tests**

Use a fake adapter and parser to verify that exactly 225 source rows are retained, the seven headers follow `patient_id` and `Report`, the source path is never used as the output path, and the result rows align by source row rather than sort order.

- [x] **Step 2: Run CLI tests and verify RED**

Run: `rtk /Users/chenjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest tests/test_cli.py -q`

Expected: collection fails because the CLI module does not exist.

- [x] **Step 3: Implement the artifact-tool XLSX adapter**

Support `read` and `write` commands. `read` imports the workbook and writes a JSON representation of `Sheet1!A1:B226`. `write` imports the original workbook, writes headers to `C1:I1`, writes result rows to `C2:I226`, applies readable widths, wrapping and a frozen header, then exports to a distinct output path.

- [x] **Step 4: Implement the CLI**

Accept input, output, checkpoint, error log, model, base URL, retry count, and optional row limit. Require `OPENAI_API_KEY`, invoke the adapter through the bundled Node runtime, process rows, and write the output workbook.

- [x] **Step 5: Run CLI tests and verify GREEN**

Run the Task 4 pytest command. Expected: all tests pass.

### Task 5: Dependency check and live API smoke test

**Files:**
- Create: `requirements.txt`
- Modify only if needed: parser compatibility code

- [x] **Step 1: Record minimum runtime dependencies**

List `langchain`, `langchain-openai`, `pydantic`, and `pytest` without embedding credentials.

- [x] **Step 2: Check imports in the bundled Python runtime**

Run a one-line import check for LangChain, `langchain_openai`, Pydantic, and pytest.

Expected: imports succeed. If LangChain is unavailable, install the recorded dependencies only after requesting network approval.

- [x] **Step 3: Run all unit tests**

Run: `rtk /Users/chenjun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest -q`

Expected: all tests pass.

- [x] **Step 4: Run one live report as a smoke test**

Set `OPENAI_BASE_URL=https://apinebula.com/v1`, use the provided key only as an ephemeral environment variable, process one synthetic row, and inspect the seven returned values.

Expected: a validated flat extraction is returned. The smoke test uses a synthetic report without patient information. If the provider rejects structured-output mode, switch the parser to LangChain's JSON/Pydantic output parser fallback and repeat the smoke test.

### Task 6: Full workbook processing and verification

**Files:**
- Create: `outputs/rectal_mri_structured_gpt-5.4.xlsx`
- Create: `outputs/rectal_mri_structured_gpt-5.4.checkpoint.json`
- Create only on failures: `outputs/rectal_mri_structured_gpt-5.4.errors.jsonl`

- [x] **Step 1: Process all 225 reports**

Run the CLI with the source workbook, `gpt-5.4`, the approved base URL, checkpoint path, and distinct output path. Keep retry and checkpoint behavior enabled.

- [x] **Step 2: Validate workbook content**

Use `@oai/artifact-tool` inspection to confirm 226 rows, 9 columns, exact header order, and source-column equality. Scan categorical values against allowed sets and length values against `^(None|[0-9]+(?:\\.[0-9]+)?mm)$`.

- [x] **Step 3: Render and visually inspect the sheet**

Render representative top and lower ranges, confirm headers and long report text are legible, and repair only material layout issues.

- [x] **Step 4: Run final verification**

Run all tests again, inspect the final workbook, and confirm the source workbook checksum is unchanged.

Expected: all tests pass, no invalid cells are found, and the final workbook opens successfully.
