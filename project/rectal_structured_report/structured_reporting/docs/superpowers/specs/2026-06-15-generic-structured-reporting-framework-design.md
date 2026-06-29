# 通用结构化报告框架设计

## 目标

将固定的直肠 MRI 七字段工具重构为配置驱动的 Python 框架。用户通过 YAML/JSON Profile 定义扁平字段、类型、约束、基础 prompt 和可选示例，即可生成默认 prompt、保存 LLM 优化 prompt，并处理单条文本或 Excel。

## 架构

- `ReportProfile` 负责版本化配置、字段顺序、缺失值展示和稳定摘要。
- `compile_schema()` 将 Profile 编译为禁止额外键、所有字段必需但可为 `null` 的动态 Pydantic 模型。
- `compile_default_prompt()` 确定性生成 system/user prompt；`optimize_prompt()` 生成与 Profile 摘要绑定的显式 Artifact。
- `ExtractionEngine` 统一模型调用、结构校验、归一化、扩展 validator 和重试。
- `ExcelAdapter` 根据自定义工作表及 ID/报告表头读取数据，并把结果追加到最后一个已有表头之后。
- 新检查点绑定 Profile、Prompt、Provider、模型、Base URL、输入文件摘要，以及每条记录的行号、ID 和报告摘要。

## 数据契约

首版支持 `text`、`enum`、`number`、`boolean`、`date` 和 `list`。JSON 输出键始终使用字段 `label`；可选 `excel_header` 仅控制工作簿表头。数值以 JSON 数字保存，目标单位和换算因子属于字段元数据。证据不足统一为内部 `null`，Excel 展示值由 Profile 配置。

复杂确定性规则只能引用应用启动时注册的 validator 名称，Profile 不允许导入或执行任意 Python。Prompt Artifact 不会自动启用，提取时必须通过参数显式选择，且 Profile 变化后旧 Artifact 会被拒绝。

## 接口

CLI 提供：

- `structured-report profile validate`
- `structured-report prompt default`
- `structured-report prompt optimize`
- `structured-report extract text`
- `structured-report extract excel`

Python API 提供 `load_profile()`、`compile_schema()`、`compile_default_prompt()`、`optimize_prompt()`、`ExtractionEngine` 和 `register_validator()`。

## 范围与迁移

首版仅支持扁平字段、单条文本和 Excel，不包含 Web、CSV、JSONL、嵌套对象或自动 prompt A/B 评估。原七字段规则迁移到 `examples/rectal_mri.yaml`。旧 CLI 参数和旧检查点格式明确不兼容，不进行静默迁移。

## 验收

合法 Profile 可以生成默认 prompt、生成并保存优化 Artifact、处理文本和 Excel；模型输出必须通过动态 Schema；Excel 不覆盖源文件；检查点可安全恢复且不会保存报告全文、API Key 或 Authorization 头。

