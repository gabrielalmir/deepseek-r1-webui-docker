# 项目代理工作指南

## 适用范围

本文件适用于当前目录及其所有子目录。后续代理在修改代码、测试、文档或执行批处理任务时，应遵守本指南。

命令行操作始终使用 `rtk` 前缀，例如：

```bash
rtk .venv/bin/python -m pytest -q
rtk rg --files
```

## 项目目标

本项目是通用结构化报告框架。用户通过 YAML/JSON Profile 定义字段、类型、约束、基础 prompt 和可选示例，框架负责生成 prompt、调用大语言模型、校验结构化输出，并处理单条文本或 Excel 批量报告。

主要设计目标：

- Profile 驱动，不把结直肠癌或任何单病种字段写死进框架代码。
- 严格按报告原文提取，不编造、不联想、不自动补全。
- 输出字段稳定，并由动态 Pydantic Schema 验证。
- 缺失、矛盾、模糊或证据不足时使用内部 JSON `null`。
- Excel 展示缺失值由 Profile 的 `missing.excel_value` 控制。
- 保留原始工作簿内容和格式，不覆盖源文件。
- 支持断点续跑、单行重试和最终错误记录。
- 支持 OpenAI 兼容服务、DeepSeek 和 Ollama。

本项目不使用 Node.js。不得为 Excel 处理、命令行或模型调用新增 Node.js 依赖，除非用户明确要求改变技术栈。

旧定制包 `rectal_mri_structuring` 和旧入口 `run_structuring.py` 已删除；不得重新引入。结直肠癌七字段规则仅作为 `examples/rectal_mri.yaml` 示例 Profile 保留。

## 关键文件

- `structured_report.py`：未安装包时可用的命令行入口。
- `structured_reporting/cli.py`：`structured-report` CLI 参数解析与流程编排。
- `structured_reporting/profile.py`：Profile 数据契约、YAML/JSON 加载和摘要。
- `structured_reporting/schema.py`：动态 Pydantic Schema 编译、类型约束和单位换算。
- `structured_reporting/prompt.py`：默认 prompt 生成与 prompt 契约校验。
- `structured_reporting/optimizer.py`：LLM prompt 优化、Artifact 保存/读取。
- `structured_reporting/engine.py`：LangChain 模型调用、结构化输出和重试。
- `structured_reporting/providers.py`：Provider、默认模型、Base URL 和环境变量解析。
- `structured_reporting/excel.py`：`openpyxl` 读写、格式保留和结果追加。
- `structured_reporting/batch.py`：批处理、检查点和错误日志。
- `examples/rectal_mri.yaml`：原直肠 MRI 七字段迁移示例。
- `tests/`：行为回归测试。
- `README.md`：面向使用者的安装、CLI 与 Python API 说明。

## Profile 与输出契约

- Profile 字段必须包含稳定 ASCII `id`、输出键 `label`、字段 `type` 和提取 `rule`。
- `label` 是 JSON 输出键；`excel_header` 仅影响 Excel 表头。
- 首版字段类型为 `text`、`enum`、`number`、`boolean`、`date` 和 `list`。
- 所有字段必须出现在 JSON 中，但值可以是 `null`。
- `number` 字段输出 JSON 数字；目标单位和换算规则放在 Profile 元数据中。
- 不允许 JSON 嵌套、额外键、解释文本、Markdown 代码块或推理过程。
- 复杂确定性规则只能通过 `register_validator()` 注册，并由 Profile 引用注册名称；配置文件不得导入或执行任意 Python。

修改 Profile、Schema 或 Prompt 相关逻辑时，必须同步检查 `profile.py`、`schema.py`、`prompt.py`、`optimizer.py`、示例 Profile 和相关测试。

## Provider 规则

### OpenAI 兼容服务

- Provider 名为 `openai`。
- 默认模型和地址定义在 `structured_reporting/providers.py`。
- 密钥通过 `OPENAI_API_KEY` 读取。
- 结构化输出默认使用 LangChain `json_schema`。

### DeepSeek

- Provider 名为 `deepseek`。
- 使用 `DEEPSEEK_API_KEY`，并兼容 `OPENAI_API_KEY`。
- 当 `OPENAI_BASE_URL` 的主机名为 `api.deepseek.com` 时，应自动解析为 DeepSeek Provider。
- DeepSeek 当前路径使用 `json_mode`。
- JSON Mode 提示词必须明确包含 `JSON`/`json` 和完整字段契约。
- 模型名和接口能力会变化。更改 DeepSeek 默认模型或输出模式前，必须查验官方文档和 `/models` 结果。

### Ollama

- Provider 名为 `ollama`。
- 默认地址为 `http://localhost:11434/v1`。
- 必须显式传入 `--model`，模型名应与 `ollama list` 一致。
- 不要求用户设置真实 API Key；内部使用占位值。
- 如果 Ollama 地址不是 `localhost`，不得宣称报告数据仅在本机处理。

新增 Provider 时，至少应更新 `ProviderName`、配置解析、CLI choices、结构化输出方式、检查点元数据测试和 README。

## Excel 不变性

- 仅使用 Python `openpyxl` 读写 `.xlsx`。
- 工作表名、ID 列和报告列由用户配置，默认是 `Sheet1`、`patient_id`、`Report`。
- 结果追加到最后一个已有表头之后。
- 不得将输出路径设为输入路径。
- 保留源工作簿已有内容、样式、列宽和行高。
- 新增列使用自动换行和顶部对齐。
- 不要为无关的样式美化重写整个工作簿。

修改 Excel 适配器后，必须验证行数、表头顺序、原始值、样式、列宽、行高和冻结窗格。

## 检查点与错误日志

- 检查点绑定 Profile digest、Prompt digest、provider、model、base_url 和输入文件摘要。
- 不同 Profile、Prompt、Provider、模型、Base URL 或输入文件不得复用同一检查点。
- 每条记录由行号、ID 和报告 SHA-256 摘要识别，避免重复 ID 或报告修改后错误复用。
- 检查点应在每条成功后原子更新，保持中断后可续跑。
- 旧版直肠 MRI 检查点不兼容，应明确报错，不得静默读取。
- 错误日志只记录最终失败的行、ID、错误类型和简短消息。
- 不得把完整报告原文、API Key 或 Authorization 头写入日志、检查点或测试快照。

## 开发规则

- 修改前先阅读相关模块和现有测试，遵循现有边界。
- 优先做最小范围修改，不进行与当前任务无关的重构。
- 行为修改应先增加或调整能够复现问题的测试，再修改实现。
- 继续使用 Pydantic 表达结构化契约，不用字符串拼接或正则替代正式 JSON 解析。
- 不要在代码、README、测试、命令示例或输出文件中硬编码真实 API Key。
- 代码默认使用 ASCII；中文提示词、字段名和文档可保留 Unicode。
- 不得因测试或烟雾运行覆盖已有输出。使用独立的输出、检查点和错误日志路径。
- 除非用户明确要求全量运行，Provider 联调先使用 `--row-limit 1` 或单条文本做烟雾测试。

## 测试要求

测试必须使用合成报告和假模型，不得依赖真实医疗数据或付费 API。

针对性测试示例：

```bash
rtk .venv/bin/python -m pytest -q tests/test_generic_profile.py
rtk .venv/bin/python -m pytest -q tests/test_generic_schema.py
rtk .venv/bin/python -m pytest -q tests/test_generic_engine.py
rtk .venv/bin/python -m pytest -q tests/test_generic_excel.py
```

完成前必须运行完整测试：

```bash
rtk .venv/bin/python -m pytest -q
```

如果修改了 Provider 调用、提示词或结构化输出，在可用且获得授权时，还应使用合成报告进行一次在线最小调用。如果需要验证 Excel 端到端流程，使用新路径和 `--row-limit 1`。

## 运行命令

查看命令帮助：

```bash
rtk .venv/bin/python structured_report.py --help
```

通用烟雾测试模板：

```bash
rtk .venv/bin/python structured_report.py extract excel examples/rectal_mri.yaml \
  --provider deepseek \
  --input '副本直肠癌多中心文本.xlsx' \
  --output 'outputs/provider-smoke.xlsx' \
  --checkpoint 'outputs/provider-smoke.checkpoint.json' \
  --error-log 'outputs/provider-smoke.errors.jsonl' \
  --row-limit 1
```

不要在命令中内联真实密钥。通过环境变量传入凭据。

## 完成检查

在宣布任务完成前，确认：

- 没有重新引入 `rectal_mri_structuring` 或 `run_structuring.py`。
- Profile、Prompt、Schema 和 Excel 表头契约保持一致。
- 输入工作簿不会被覆盖，原始内容和格式保真要求仍然成立。
- Provider 输出方式与对应 API 能力相符。
- 检查点元数据与当前 Profile、Prompt、Provider 和输入文件一致。
- 密钥、完整报告和 Authorization 头没有进入源代码或日志。
- 相关定向测试和完整测试均已通过。
- README 与 CLI 的 Provider、参数和默认值保持一致。
