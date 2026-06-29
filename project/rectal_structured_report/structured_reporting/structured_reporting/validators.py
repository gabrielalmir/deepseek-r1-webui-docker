from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .profile import FieldDefinition, ReportProfile


Validator = Callable[[Any, FieldDefinition, ReportProfile], Any]
_VALIDATORS: dict[str, Validator] = {}


def register_validator(name: str, validator: Validator) -> None:
    normalized = name.strip()
    if not normalized:
        raise ValueError("validator name cannot be empty")
    if not callable(validator):
        raise TypeError("validator must be callable")
    _VALIDATORS[normalized] = validator


def get_validator(name: str) -> Validator:
    try:
        return _VALIDATORS[name]
    except KeyError as error:
        raise ValueError(f"unknown validator: {name}") from error

