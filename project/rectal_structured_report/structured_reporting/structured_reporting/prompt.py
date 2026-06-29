from __future__ import annotations

import hashlib
import json
import re
from string import Formatter

from pydantic import BaseModel, ConfigDict

from .profile import FieldDefinition, ReportProfile


class PromptBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    system_prompt: str
    user_prompt: str

    def digest(self) -> str:
        canonical = json.dumps(
            self.model_dump(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _field_type_description(field: FieldDefinition) -> str:
    details = [f"类型 {field.type}"]
    if field.choices:
        details.append(f"允许值：{'、'.join(field.choices)}")
    if field.type == "number":
        if field.unit:
            details.append(f"目标单位 {field.unit}")
        if field.minimum is not None:
            details.append(f"最小值 {field.minimum:g}")
        if field.maximum is not None:
            details.append(f"最大值 {field.maximum:g}")
    if field.pattern:
        details.append(f"格式正则 {field.pattern}")
    if field.type == "list":
        details.append(f"元素类型 {field.item_type}")
        if field.item_choices:
            details.append(f"元素允许值：{'、'.join(field.item_choices)}")
    return "；".join(details)


def validate_prompt_bundle(profile: ReportProfile, bundle: PromptBundle) -> None:
    placeholders = [
        field_name
        for _, field_name, _, _ in Formatter().parse(bundle.user_prompt)
        if field_name is not None
    ]
    if placeholders != ["report"] or bundle.user_prompt.count("{report}") != 1:
        raise ValueError("user prompt must contain exactly one {report} placeholder")
    if "{report}" in bundle.system_prompt:
        raise ValueError("system prompt cannot contain the report placeholder")
    normalized_system = re.sub(r"\s+", "", bundle.system_prompt)
    for field in profile.fields:
        normalized_label = re.sub(r"\s+", "", field.output_label)
        if normalized_label not in normalized_system:
            raise ValueError(f"system prompt does not cover field: {field.output_label}")
    if "json" not in bundle.system_prompt.lower():
        raise ValueError("system prompt must require JSON output")


def compile_default_prompt(profile: ReportProfile) -> PromptBundle:
    field_sections = []
    for index, field in enumerate(profile.fields, start=1):
        field_sections.append(
            f"{index}. 【{field.output_label}】\n"
            f"- {_field_type_description(field)}\n"
            f"- 提取规则：{field.rule}"
        )
    empty_contract = {field.output_label: None for field in profile.fields}
    contract = json.dumps(empty_contract, ensure_ascii=False, indent=2)
    system_prompt = "\n\n".join(
        [
            profile.base_prompt.strip(),
            (
                "只能依据当前报告原文提取信息，禁止编造、联想或自动补全。"
                "缺失、矛盾、模糊或证据不足的字段必须输出 JSON null。"
            ),
            "字段定义：\n" + "\n\n".join(field_sections),
            (
                "最终仅输出一个合法 JSON 对象。所有字段必须出现，不允许嵌套，"
                "不允许额外字段，不要输出 Markdown、解释或推理过程。\n"
                "字段键和空值示例如下：\n"
                + contract
            ),
        ]
    )
    bundle = PromptBundle(
        system_prompt=system_prompt,
        user_prompt="报告原文：\n{report}",
    )
    validate_prompt_bundle(profile, bundle)
    return bundle
