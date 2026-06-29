# Ollama OpenAI 兼容接口支持设计

## 目标

在不破坏现有 OpenAI 兼容云接口用法的前提下，为直肠癌 MRI 报告结构化工具增加 Ollama 本地接口支持，并将 Excel 读写从 Node.js `@oai/artifact-tool` 迁移到 Python `openpyxl`。两种提供商继续复用相同提示词、Pydantic 输出模型、批处理、重试、断点续跑和 Excel 写回流程。

## 用户接口

新增命令行参数：

```text
--provider openai|ollama
```

默认值为 `openai`，保持现有行为。

### OpenAI 兼容提供商

```bash
export OPENAI_API_KEY='替换为API密钥'

.venv/bin/python run_structuring.py \
  --provider openai \
  --model gpt-5.4 \
  --base-url https://apinebula.com/v1 \
  ...
```

规则：

- `OPENAI_API_KEY` 必须存在。
- 默认模型为 `gpt-5.4`。
- 默认基础地址为 `OPENAI_BASE_URL`，未设置时使用 `https://apinebula.com/v1`。

### Ollama 提供商

```bash
ollama pull qwen3:8b

.venv/bin/python run_structuring.py \
  --provider ollama \
  --model qwen3:8b \
  --base-url http://localhost:11434/v1 \
  ...
```

规则：

- 不要求用户配置 API Key。
- 内部向 OpenAI SDK 传递占位密钥 `ollama`；Ollama 会忽略它。
- 默认基础地址为 `http://localhost:11434/v1`。
- `--model` 必须显式提供，避免错误地把云模型名发送到本地服务。
- 支持用户通过 `--base-url` 指向远程或容器内的 Ollama OpenAI 兼容地址。

## 架构

### 提供商配置

新增独立配置单元，负责把 CLI 输入解析为统一的模型连接配置：

- `provider`
- `model`
- `base_url`
- `api_key`

该单元只负责默认值和验证，不包含 LangChain 调用。

### LangChain 解析器

现有 `ChatOpenAI` 路径继续使用，Ollama 不引入 `langchain-ollama` 依赖。两种提供商都调用 OpenAI 兼容的 `/v1/chat/completions`，并使用 `with_structured_output(RectalMRIExtraction, method="json_schema")`。

Ollama 官方兼容接口支持 `response_format` 和 JSON Schema，因此可以复用当前 Pydantic 结构化输出。温度保持为 0。

### 批处理

批处理、错误日志、字段校验和源行顺序保持不变。

### Excel 适配器

删除 JavaScript `scripts/xlsx_adapter.mjs` 和 Node.js 运行时参数，新增纯 Python `OpenpyxlAdapter`：

- 使用 `openpyxl.load_workbook()` 打开源文件。
- 读取 `Sheet1` 的 A、B 列并验证表头为 `patient_id`、`Report`。
- 保存到独立输出路径，不覆盖源文件。
- 原始 A、B 列的值、样式、列宽和所有既有行高保持不变。
- 在 C-I 列写入 7 个字段。
- 新增表头继承原始表头风格，并使用深蓝填充、白色粗体和自动换行形成稳定的默认样式。
- 新增数据列设置顶部对齐、自动换行和固定适中列宽。
- 冻结窗格设置为 `C2`，同时冻结首行和前两列。
- 输出工作簿保留源文件中 openpyxl 能够往返保存的工作簿属性。

移除：

- `scripts/xlsx_adapter.mjs`
- 根目录 `node_modules` 链接
- CLI 参数 `--node-bin`
- CLI 参数 `--adapter-script`
- README 中所有 Node.js 和 `@oai/artifact-tool` 配置说明

`requirements.txt` 新增 `openpyxl`。

## 检查点隔离

检查点升级为版本 2，并增加元数据：

```json
{
  "version": 2,
  "metadata": {
    "provider": "ollama",
    "model": "qwen3:8b",
    "base_url": "http://localhost:11434/v1"
  },
  "results": {}
}
```

恢复任务时，当前 provider、model、base URL 必须与检查点元数据完全一致。若不一致，程序应在调用模型前停止，并提示用户指定新的检查点文件。这样可以避免云模型结果与本地模型结果混合。

旧版版本 1 检查点没有模型元数据：

- 保持向后兼容，仅允许 `provider=openai`、`model=gpt-5.4`、`base_url=https://apinebula.com/v1` 读取。
- 继续处理后，保存时升级为版本 2。
- Ollama 不得复用版本 1 检查点。

## 地址规范化

- 去除基础地址末尾多余的 `/`。
- 不自动给任意地址追加 `/v1`，避免破坏用户自定义代理路径。
- Ollama 默认地址已经包含 `/v1`。
- README 明确要求 OpenAI 兼容地址必须指向 API 根路径。

## 错误处理

- Ollama 未启动或地址不可达：保留原始连接错误，经有限重试后写入脱敏错误日志。
- 本地模型不存在：保留服务返回的模型错误，提示先运行 `ollama pull <model>`。
- 模型不支持 JSON Schema：按现有行为重试，最终失败；本次功能不增加自由文本 JSON 回退，以避免降低字段格式可靠性。
- provider、模型或地址与检查点不一致：立即失败，不处理任何行。
- OpenAI 模式未设置 API Key：立即提示 `OPENAI_API_KEY is required for provider=openai`。

## 测试

新增测试覆盖：

- CLI 默认 provider 为 `openai`。
- OpenAI 保持现有默认模型与地址。
- Ollama 不要求环境 API Key，并使用内部占位密钥。
- Ollama 缺少显式 `--model` 时失败。
- Ollama 默认地址为 `http://localhost:11434/v1`。
- 自定义基础地址能够传递到 `ChatOpenAI`。
- 版本 2 检查点保存 provider、model、base URL。
- 相同元数据允许恢复；不同元数据拒绝恢复。
- 版本 1 OpenAI 检查点保持兼容；Ollama 拒绝版本 1 检查点。
- 原有 schema、解析器、批处理、CLI 和 Excel 测试继续通过。
- openpyxl 读取时保留 225 条源行及顺序。
- openpyxl 写回后 A、B 列值不变，源列宽和既有行高不变。
- C-I 表头、换行、列宽和 `C2` 冻结窗格符合设计。
- CLI 不再暴露 Node.js 参数，项目代码不再引用 `@oai/artifact-tool`。

## 文档

README 增加：

- Ollama 安装与服务启动说明。
- `ollama pull` 和 `ollama list` 示例。
- Ollama 烟雾测试与全量运行命令。
- 本地模型性能、上下文长度和结构化输出能力提示。
- OpenAI 与 Ollama 检查点不可混用的说明。
- 纯 Python 安装与运行说明，不再要求 Node.js。

## 验收条件

- 现有 OpenAI 命令无需修改仍可运行。
- Ollama 命令无需设置 `OPENAI_API_KEY`。
- Ollama 使用明确的本地模型和 OpenAI 兼容地址。
- 两种提供商都产生相同的 7 列输出格式。
- 不同提供商或模型的检查点不能混用。
- Excel 输入输出完全由 Python `openpyxl` 完成，原始样式和尺寸按设计保留。
- 项目运行不再依赖 Node.js。
- 全部自动测试通过，README 命令与实际 `--help` 一致。
