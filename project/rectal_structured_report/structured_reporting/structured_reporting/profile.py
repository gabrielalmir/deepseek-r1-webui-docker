from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


FieldType = Literal["text", "enum", "number", "boolean", "date", "list"]
ListItemType = Literal["text", "enum", "number", "boolean", "date"]


class MissingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    excel_value: str | None = "None"


class PromptExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: str
    output: dict[str, Any]


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    label: str = Field(min_length=1)
    type: FieldType
    rule: str = Field(min_length=1)
    excel_header: str | None = None
    choices: list[str] | None = None
    pattern: str | None = None
    min_length: int | None = Field(default=None, ge=0)
    max_length: int | None = Field(default=None, ge=0)
    minimum: float | None = None
    maximum: float | None = None
    unit: str | None = None
    unit_conversions: dict[str, float] | None = None
    item_type: ListItemType | None = None
    item_choices: list[str] | None = None
    min_items: int | None = Field(default=None, ge=0)
    max_items: int | None = Field(default=None, ge=0)
    validators: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_type_constraints(self) -> "FieldDefinition":
        if self.type == "enum" and not self.choices:
            raise ValueError("enum fields require non-empty choices")
        if self.type == "list" and self.item_type is None:
            raise ValueError("list fields require item_type")
        if self.type == "list" and self.item_type == "enum" and not self.item_choices:
            raise ValueError("enum list items require non-empty item_choices")
        if self.unit is not None:
            if self.type != "number":
                raise ValueError("unit is only supported for number fields")
            conversions = self.unit_conversions or {}
            if conversions.get(self.unit) != 1:
                raise ValueError("unit_conversions must include the target unit with factor 1")
            if any(factor <= 0 for factor in conversions.values()):
                raise ValueError("unit conversion factors must be positive")
        if self.minimum is not None and self.maximum is not None:
            if self.minimum > self.maximum:
                raise ValueError("minimum cannot exceed maximum")
        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                raise ValueError("min_length cannot exceed max_length")
        if self.min_items is not None and self.max_items is not None:
            if self.min_items > self.max_items:
                raise ValueError("min_items cannot exceed max_items")
        return self

    @property
    def output_label(self) -> str:
        return self.label

    @property
    def excel_label(self) -> str:
        return self.excel_header or self.label


class ReportProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    name: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_.-]*$")
    language: str = "zh-CN"
    base_prompt: str = Field(min_length=1)
    missing: MissingConfig = Field(default_factory=MissingConfig)
    fields: list[FieldDefinition] = Field(min_length=1)
    examples: list[PromptExample] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_fields(self) -> "ReportProfile":
        ids = [field.id for field in self.fields]
        labels = [field.label for field in self.fields]
        output_labels = [field.output_label for field in self.fields]
        excel_labels = [field.excel_label for field in self.fields]
        if len(ids) != len(set(ids)):
            raise ValueError("field ids must be unique")
        if len(labels) != len(set(labels)):
            raise ValueError("field labels must be unique")
        if len(output_labels) != len(set(output_labels)):
            raise ValueError("output labels must be unique")
        if len(excel_labels) != len(set(excel_labels)):
            raise ValueError("Excel headers must be unique")
        return self

    def digest(self) -> str:
        canonical = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_profile(path: str | Path) -> ReportProfile:
    source = Path(path)
    suffix = source.suffix.lower()
    text = source.read_text(encoding="utf-8")
    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        raise ValueError("profile must be a YAML or JSON file")
    if not isinstance(payload, dict):
        raise ValueError("profile root must be an object")
    return ReportProfile.model_validate(payload)
