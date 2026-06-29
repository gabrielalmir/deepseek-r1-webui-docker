from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import ConfigDict, Field, create_model, field_validator

from .profile import FieldDefinition, ReportProfile
from .validators import get_validator


def _literal(values: list[str]) -> Any:
    return Literal.__getitem__(tuple(values))


def _base_annotation(field: FieldDefinition) -> Any:
    if field.type == "text":
        return str
    if field.type == "enum":
        return _literal(field.choices or [])
    if field.type == "number":
        return float
    if field.type == "boolean":
        return bool
    if field.type == "date":
        return date
    if field.type == "list":
        item_types: dict[str, Any] = {
            "text": str,
            "number": float,
            "boolean": bool,
            "date": date,
        }
        item_type = (
            _literal(field.item_choices or [])
            if field.item_type == "enum"
            else item_types[field.item_type or "text"]
        )
        return list[item_type]
    raise ValueError(f"unsupported field type: {field.type}")


def _field_info(field: FieldDefinition) -> Any:
    kwargs: dict[str, Any] = {
        "alias": field.output_label,
        "description": field.rule,
    }
    if field.type == "text":
        kwargs.update(
            pattern=field.pattern,
            min_length=field.min_length,
            max_length=field.max_length,
        )
    elif field.type == "number":
        kwargs.update(ge=field.minimum, le=field.maximum)
    elif field.type == "list":
        kwargs.update(min_length=field.min_items, max_length=field.max_items)
    return Field(..., **{key: value for key, value in kwargs.items() if value is not None})


_NUMBER_WITH_OPTIONAL_UNIT = re.compile(
    r"^\s*(?P<number>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?P<unit>[^\d\s]+)?\s*$"
)


def _normalize_number(value: Any, field: FieldDefinition) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    match = _NUMBER_WITH_OPTIONAL_UNIT.fullmatch(str(value))
    if not match:
        return value
    number = float(match.group("number"))
    unit = match.group("unit")
    if unit is None:
        return number
    conversions = field.unit_conversions or {}
    if unit not in conversions:
        raise ValueError(f"unsupported unit {unit!r} for {field.label}")
    return number * conversions[unit]


def _before_validator(field: FieldDefinition):
    def normalize(cls, value: Any) -> Any:
        if field.type == "number":
            return _normalize_number(value, field)
        return value

    normalize.__name__ = f"normalize_{field.id}"
    return field_validator(field.id, mode="before")(normalize)


def _after_validator(field: FieldDefinition, profile: ReportProfile):
    validators = [get_validator(name) for name in field.validators]

    def validate(cls, value: Any) -> Any:
        result = value
        for validator in validators:
            result = validator(result, field, profile)
        return result

    validate.__name__ = f"validate_{field.id}"
    return field_validator(field.id, mode="after")(validate)


def compile_schema(profile: ReportProfile):
    field_definitions: dict[str, tuple[Any, Any]] = {}
    validators: dict[str, Any] = {}
    for field in profile.fields:
        annotation = _base_annotation(field) | None
        field_definitions[field.id] = (annotation, _field_info(field))
        validators[f"normalize_{field.id}"] = _before_validator(field)
        if field.validators:
            validators[f"validate_{field.id}"] = _after_validator(field, profile)

    model_name = "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", profile.name))
    return create_model(
        f"{model_name or 'Structured'}Report",
        __config__=ConfigDict(extra="forbid", populate_by_name=True),
        __validators__=validators,
        **field_definitions,
    )
