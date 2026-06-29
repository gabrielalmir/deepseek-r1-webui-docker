# 通用结构化报告框架

本项目使用 YAML/JSON Profile 定义字段、类型、约束和领域规则，并通过大语言模型将自由文本报告转换为经过 Pydantic 校验的扁平 JSON。支持：

- 确定性生成默认 system/user prompt。
- 调用大模型生成并保存可审计的优化 prompt。
- 处理单条文本或 Excel 批量报告。
- OpenAI 兼容服务、DeepSeek 和 Ollama。
- 重试、断点续跑、输入/模型/Profile/Prompt 隔离和脱敏错误日志。

## Project 工作流程

本项目把一次结构化报告任务拆成两层文件和两个执行阶段：

```text
Profile（任务定义） -> Prompt（给模型的指令） -> LLM 提取 -> Schema 校验 -> JSON / Excel 输出
```

### 1. Profile：定义“要什么”

Profile 是结构化任务的契约文件，通常是 `.yaml` 或 `.json`。它定义：

- 要输出哪些字段。
- 每个字段的 JSON 键名 `label`。
- 字段类型：`text`、`enum`、`number`、`boolean`、`date`、`list`。
- 枚举允许值、数值范围、单位换算、列表长度等校验规则。
- 每个字段的领域提取规则。
- Excel 中 `null` 如何显示。

例如 `examples/rectal_mri_esmo.yaml` 定义的是“ESMO风险分层”这个结构化任务。它不是 prompt，也不直接发给模型；它先被框架编译成动态 Pydantic Schema，用来约束最终结果。

### 2. Prompt：定义“怎么问模型”

Prompt 是给大语言模型看的具体指令，由 `system_prompt` 和 `user_prompt` 组成。

- 默认 prompt：由框架根据 Profile 确定性生成。
- 优化 prompt：由大模型根据 Profile 和默认 prompt 进一步改写，保存成 Prompt Artifact。

Prompt Artifact 不是 Profile。运行提取时必须这样搭配：

```bash
structured-report extract excel <profile.yaml> \
  --prompt <optimized-prompt.yaml-or-json> \
  ...
```

如果不传 `--prompt`，框架会自动使用 Profile 生成默认 prompt。

### 3. 提取阶段：模型输出必须过 Schema

提取时，框架会：

1. 读取 Profile。
2. 编译动态 Pydantic Schema。
3. 读取默认 prompt 或 `--prompt` 指定的优化 Prompt Artifact。
4. 调用 provider 对应的大语言模型。
5. 用 Schema 校验模型输出，拒绝额外字段、非法枚举值和非法类型。
6. 对数值字段做单位换算。
7. 输出 JSON，或把结果追加写入 Excel。

模型可以生成错误内容，但 Schema 不会放行错误结构。

### 4. Excel 批处理阶段：可恢复、可追踪

Excel 批处理会额外做：

- 从指定工作表和报告列读取数据。
- 每行报告独立调用模型。
- 每条成功结果写入 checkpoint。
- 中断后可复用 checkpoint 继续。
- checkpoint 绑定 Profile、Prompt、模型、Base URL 和输入文件摘要，避免混用旧结果。
- 最终失败的行写入脱敏 error log。

## 命令工作流程

### `structured-report profile validate`

用途：检查 Profile 是否合法。

```bash
structured-report profile validate examples/rectal_mri_esmo.yaml
```

内部流程：

```text
读取 YAML/JSON -> Pydantic 校验 Profile -> 编译动态 Schema -> 输出 profile digest
```

它不会调用模型，也不会处理报告。建议每次新建或修改 Profile 后先运行。

### `structured-report prompt default`

用途：根据 Profile 生成确定性的默认 prompt。

```bash
structured-report prompt default examples/rectal_mri_esmo.yaml \
  --output outputs/rectal-mri-esmo.default-prompt.yaml
```

内部流程：

```text
读取 Profile -> 拼接字段规则和 JSON 契约 -> 校验 {report} 占位符 -> 保存 system/user prompt
```

默认 prompt 可复现，同一个 Profile 每次生成结果一致。

### `structured-report prompt optimize`

用途：调用大模型优化默认 prompt，并保存 Prompt Artifact。

```bash
structured-report prompt optimize examples/rectal_mri_esmo.yaml \
  --provider openai \
  --model gpt-5.4 \
  --output outputs/rectal-mri-esmo.optimized-prompt.yaml
```

内部流程：

```text
读取 Profile -> 生成默认 prompt -> 调用优化模型 -> 校验优化后的 prompt 覆盖全部字段 -> 绑定 profile digest -> 保存 Artifact
```

优化 prompt 不会自动启用。提取时必须通过 `--prompt` 显式选择。

### `structured-report extract text`

用途：处理一条报告文本，输出 JSON。

```bash
structured-report extract text examples/rectal_mri_esmo.yaml \
  --prompt outputs/rectal-mri-esmo.optimized-prompt.yaml \
  --input report.txt \
  --provider openai
```

内部流程：

```text
读取 Profile -> 读取 Prompt Artifact 或生成默认 prompt -> 调用模型 -> Schema 校验 -> 输出 JSON
```

省略 `--input` 时从 stdin 读取报告。

### `structured-report extract excel`

用途：批量处理 Excel 报告，并把结果追加到新工作簿。

```bash
structured-report extract excel examples/rectal_mri_esmo.yaml \
  --prompt outputs/rectal-mri-esmo.optimized-prompt.yaml \
  --input 副本直肠癌多中心文本.xlsx \
  --output outputs/副本直肠癌多中心文本_esmo_direction.xlsx \
  --checkpoint outputs/副本直肠癌多中心文本_esmo_direction.ckpt.json \
  --error-log outputs/result.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai
```

内部流程：

```text
读取 Profile
-> 读取 Prompt Artifact 或生成默认 prompt
-> 校验 checkpoint 元数据
-> 读取 Excel 指定 sheet/id/report 列
-> 逐行调用模型
-> Schema 校验与归一化
-> 每行成功后更新 checkpoint
-> 失败行写入 error log
-> 结果追加到新 Excel
```

注意：`extract excel` 后面的第一个位置参数必须是 Profile；优化 prompt 要放到 `--prompt` 后面。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

安装后使用 `structured-report`。未安装 editable package 时可使用：

```bash
.venv/bin/python structured_report.py --help
```

## Profile

Profile 支持 YAML 和 JSON。每个字段需要稳定的 ASCII `id`、输出 `label`、`type` 和提取 `rule`。

```yaml
version: 1
name: demo
base_prompt: 严格依据报告原文，不要推测。
missing:
  excel_value: None
fields:
  - id: category
    label: 类别
    type: enum
    choices: [A, B]
    rule: 只能选择报告明确出现的类别。
  - id: length
    label: 长度
    type: number
    unit: mm
    unit_conversions: {mm: 1, cm: 10}
    rule: 提取长度并换算为毫米。
```

字段类型包括 `text`、`enum`、`number`、`boolean`、`date` 和 `list`。所有字段必须出现在 JSON 中，但证据不足时值为 `null`。数值保持 JSON 数字，单位属于字段元数据。

验证 Profile：

```bash
structured-report profile validate examples/rectal_mri.yaml
```

## Prompt

生成确定性默认 prompt：

```bash
structured-report prompt default examples/rectal_mri.yaml \
  --output outputs/rectal-mri.default-prompt.yaml
```

使用模型生成候选 prompt：

```bash
export OPENAI_API_KEY='替换为密钥'
structured-report prompt optimize examples/rectal_mri.yaml \
  --provider openai \
  --model gpt-5.4 \
  --output outputs/rectal-mri.optimized-prompt.yaml
```

优化 prompt 不会自动覆盖默认 prompt。提取时必须通过 `--prompt` 显式选择。Artifact 绑定 Profile 摘要，Profile 变化后旧 Artifact 会被拒绝。

## 单条文本

```bash
structured-report extract text examples/rectal_mri.yaml \
  --input report.txt \
  --provider openai
```

省略 `--input` 时从 stdin 读取。使用优化 prompt：

```bash
structured-report extract text examples/rectal_mri.yaml \
  --prompt outputs/rectal-mri.optimized-prompt.yaml < report.txt
```

## Excel 批处理

```bash
structured-report extract excel examples/rectal_mri.yaml \
  --input source.xlsx \
  --output outputs/result.xlsx \
  --checkpoint outputs/result.checkpoint.json \
  --error-log outputs/result.errors.jsonl \
  --sheet-name Sheet1 \
  --id-column patient_id \
  --report-column Report \
  --provider openai
```

结果追加到工作表最后一个已有表头之后，不覆盖源文件。Profile 的 `missing.excel_value` 控制 `null` 在 Excel 中显示为 `None`、其他文本或空白。

检查点绑定 Profile、Prompt、provider、模型、Base URL、输入文件摘要，并按行号、ID 和报告摘要识别记录。旧版直肠 MRI 检查点与新格式不兼容，会明确报错而不会静默复用。

`--checkpoint` 是一个单个 JSON 对象文件，建议使用 `.json` 后缀；错误日志 `--error-log` 才是 JSON Lines，建议使用 `.jsonl` 后缀。

## Provider

- `openai`：读取 `OPENAI_API_KEY` 和可选 `OPENAI_BASE_URL`。
- `deepseek`：读取 `DEEPSEEK_API_KEY`，使用 JSON Object 模式。
- `ollama`：必须传 `--model`，默认地址为 `http://localhost:11434/v1`，无需真实 API Key。

## Python API

核心导入：

```python
from structured_reporting import (
    ExtractionEngine,
    ReportProfile,
    compile_default_prompt,
    compile_schema,
    create_live_engine,
    load_profile,
    optimize_prompt,
    register_validator,
)
```

### 1. 加载 Profile

```python
from structured_reporting import load_profile

profile = load_profile("examples/rectal_mri.yaml")

print(profile.name)
print(profile.digest())
print([field.label for field in profile.fields])
```

`load_profile()` 支持 `.yaml`、`.yml` 和 `.json`。Profile 会被 Pydantic 校验：字段 `id` 必须是稳定 ASCII 标识符，`label` 是 JSON 输出键，`excel_header` 只影响 Excel 表头。

### 2. 编译动态 Schema

```python
from structured_reporting import compile_schema

schema = compile_schema(profile)

result = schema.model_validate({
    "肿瘤的位置": "中下段",
    "肿瘤累及长度": "6 cm",
    "肿瘤浸润深度": "T3",
    "直肠系膜内淋巴结评估": "有",
    "直肠系膜外淋巴结评估": None,
    "CRM受累情况": "无",
    "EMVI受累情况": None,
})

print(result.model_dump(by_alias=True, mode="json"))
```

输出示例：

```python
{
    "肿瘤的位置": "中下段",
    "肿瘤累及长度": 60.0,
    "肿瘤浸润深度": "T3",
    "直肠系膜内淋巴结评估": "有",
    "直肠系膜外淋巴结评估": None,
    "CRM受累情况": "无",
    "EMVI受累情况": None,
}
```

所有字段必填，但值可以是 `None`。额外字段会被拒绝。`number` 字段会按 Profile 中的 `unit_conversions` 做单位换算。

### 3. 注册自定义 Validator

```python
from structured_reporting import register_validator, load_profile, compile_schema

def uppercase_value(value, field, profile):
    if value is None:
        return None
    return str(value).upper()

register_validator("uppercase", uppercase_value)

profile = load_profile("my_profile.yaml")
schema = compile_schema(profile)
```

Profile 中引用：

```yaml
fields:
  - id: name
    label: 名称
    type: text
    rule: 原样提取名称
    validators: [uppercase]
```

Validator 签名固定为：

```python
def validator(value, field, profile):
    return value
```

必须在 `compile_schema(profile)` 或 `create_live_engine(...)` 之前注册。

### 4. 生成默认 Prompt

```python
from structured_reporting import compile_default_prompt

prompt = compile_default_prompt(profile)

print(prompt.system_prompt)
print(prompt.user_prompt)
print(prompt.digest())
```

`user_prompt` 默认是：

```text
报告原文：
{report}
```

系统会检查：

- `user_prompt` 必须且只能包含一个 `{report}`。
- `system_prompt` 必须覆盖所有字段 `label`。
- `system_prompt` 必须要求 JSON 输出。

### 5. 优化 Prompt

```python
from structured_reporting import load_profile, optimize_prompt
from structured_reporting.providers import resolve_provider_config
from structured_reporting.optimizer import save_prompt_artifact

profile = load_profile("examples/rectal_mri.yaml")

config = resolve_provider_config(
    provider="openai",
    model="gpt-5.4",
)

artifact = optimize_prompt(profile, config=config)

save_prompt_artifact(
    "outputs/rectal-mri.optimized-prompt.yaml",
    artifact,
)
```

读取优化 Prompt：

```python
from structured_reporting.optimizer import load_prompt_artifact

artifact = load_prompt_artifact(
    "outputs/rectal-mri.optimized-prompt.yaml",
    profile=profile,
)
```

`save_prompt_artifact()` 支持 `.json`、`.yaml` 和 `.yml`。Artifact 绑定 `profile.digest()`；如果 Profile 改了，旧 Artifact 会被拒绝。

### 6. 单条文本实时提取

```python
from structured_reporting import load_profile, create_live_engine
from structured_reporting.providers import resolve_provider_config
from structured_reporting.optimizer import load_prompt_artifact

profile = load_profile("examples/rectal_mri.yaml")

config = resolve_provider_config(
    provider="openai",
    model="gpt-5.4",
)

prompt_artifact = load_prompt_artifact(
    "outputs/rectal-mri.optimized-prompt.yaml",
    profile=profile,
)

engine = create_live_engine(
    profile,
    config=config,
    prompt=prompt_artifact,
    max_retries=3,
)

result = engine.extract("直肠中下段病灶，累及长度约6cm。")
print(result)
```

如果不传 `prompt`，会自动使用 `compile_default_prompt(profile)`。

### 7. 离线或测试用 ExtractionEngine

```python
from structured_reporting import ExtractionEngine, load_profile

class FakeRunnable:
    def invoke(self, payload):
        assert payload == {"report": "测试报告"}
        return {
            "肿瘤的位置": "中段",
            "肿瘤累及长度": "4 cm",
            "肿瘤浸润深度": None,
            "直肠系膜内淋巴结评估": None,
            "直肠系膜外淋巴结评估": None,
            "CRM受累情况": None,
            "EMVI受累情况": None,
        }

profile = load_profile("examples/rectal_mri.yaml")
engine = ExtractionEngine(profile, runnable=FakeRunnable())

print(engine.extract("测试报告"))
```

这个方式适合单元测试，不调用真实模型。

### 8. Excel 批处理 API

```python
from structured_reporting import (
    compile_default_prompt,
    create_live_engine,
    load_profile,
)
from structured_reporting.batch import (
    build_checkpoint_metadata,
    file_digest,
    process_records,
)
from structured_reporting.excel import ExcelAdapter
from structured_reporting.providers import resolve_provider_config

input_path = "source.xlsx"
output_path = "outputs/result.xlsx"

profile = load_profile("examples/rectal_mri.yaml")
prompt = compile_default_prompt(profile)

config = resolve_provider_config(
    provider="openai",
    model="gpt-5.4",
)

engine = create_live_engine(
    profile,
    config=config,
    prompt=prompt,
    max_retries=3,
)

adapter = ExcelAdapter(
    sheet_name="Sheet1",
    id_column="patient_id",
    report_column="Report",
)

rows = adapter.read(input_path)

metadata = build_checkpoint_metadata(
    profile=profile,
    prompt=prompt,
    config=config,
    input_digest=file_digest(input_path),
)

results = process_records(
    rows,
    engine,
    checkpoint_path="outputs/result.checkpoint.json",
    checkpoint_metadata=metadata,
    error_log_path="outputs/result.errors.jsonl",
)

adapter.write(
    input_path,
    output_path,
    profile=profile,
    rows=rows,
    results=results,
)
```

检查点会绑定 Profile、Prompt、provider、模型、Base URL、输入文件摘要、行号、ID 和报告摘要，避免模型、prompt 或输入变化后误用旧结果。

### 9. Provider 配置

```python
from structured_reporting.providers import resolve_provider_config
```

OpenAI：

```python
config = resolve_provider_config(provider="openai", model="gpt-5.4")
```

DeepSeek：

```python
config = resolve_provider_config(provider="deepseek", model="deepseek-v4-pro")
```

Ollama：

```python
config = resolve_provider_config(provider="ollama", model="qwen3:8b")
```

如果 `OPENAI_BASE_URL` 是 `https://api.deepseek.com/v1`，`provider="openai"` 会自动解析为 DeepSeek 模式。

### 10. 常见工作流

```python
from structured_reporting import (
    compile_default_prompt,
    create_live_engine,
    load_profile,
)
from structured_reporting.optimizer import load_prompt_artifact
from structured_reporting.providers import resolve_provider_config

profile = load_profile("examples/rectal_mri.yaml")

try:
    prompt = load_prompt_artifact(
        "outputs/rectal-mri.optimized-prompt.yaml",
        profile=profile,
    )
except FileNotFoundError:
    prompt = compile_default_prompt(profile)

config = resolve_provider_config(provider="openai", model="gpt-5.4")
engine = create_live_engine(profile, config=config, prompt=prompt)

result = engine.extract("报告原文……")
print(result)
```

核心原则：Profile 定义结构，Prompt 控制模型行为，Schema 做最终裁判。模型可以写错，Schema 不能放行。

## 测试

```bash
.venv/bin/python -m pytest -q
```

`examples/rectal_mri.yaml` 是原七字段直肠 MRI 项目的迁移示例。旧定制包 `rectal_mri_structuring`、旧入口 `run_structuring.py`、旧命令参数和旧检查点格式均已移除；请统一使用 `structured-report` 或 `structured_reporting` Python API。
