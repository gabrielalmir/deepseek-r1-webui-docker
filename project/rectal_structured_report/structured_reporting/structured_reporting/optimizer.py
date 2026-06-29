from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .profile import PromptExample, ReportProfile
from .prompt import PromptBundle, compile_default_prompt, validate_prompt_bundle


class PromptCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_prompt: str = Field(
        min_length=1,
        validation_alias=AliasChoices("system_prompt", "optimized_system_prompt"),
    )
    user_prompt: str | None = Field(
        default=None,
        validation_alias=AliasChoices("user_prompt", "optimized_user_prompt"),
    )


class PromptArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    profile_digest: str
    provider: str
    model: str
    base_url: str
    system_prompt: str
    user_prompt: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def bundle(self) -> PromptBundle:
        return PromptBundle(
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt,
        )

    def prompt_digest(self) -> str:
        return self.bundle().digest()


def _candidate_user_prompt_or_default(
    profile: ReportProfile,
    default: PromptBundle,
    user_prompt: str | None,
) -> str:
    if user_prompt is None:
        return default.user_prompt
    try:
        validate_prompt_bundle(
            profile,
            PromptBundle(
                system_prompt=default.system_prompt,
                user_prompt=user_prompt,
            ),
        )
    except ValueError as error:
        if "user prompt" not in str(error):
            raise
        return default.user_prompt
    return user_prompt


def _create_optimizer_runnable(config: Any):
    llm = ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=0,
        max_retries=0,
        timeout=120,
    )
    method = "json_mode" if config.provider == "deepseek" else "json_schema"
    structured = llm.with_structured_output(PromptCandidate, method=method)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是结构化信息抽取提示词设计专家。优化提示词的清晰度，"
                "但不得改变字段、类型、允许值、缺失值规则或 JSON 输出契约。"
                "最终必须只返回一个 JSON 对象，且恰好包含 system_prompt 和 "
                "user_prompt 两个键。user_prompt 必须包含且仅包含一个 "
                "{{report}} 占位符。不要使用 optimized_system_prompt 等其他键名。",
            ),
            (
                "human",
                "Profile:\n{profile_json}\n\n默认 system prompt:\n"
                "{default_system_prompt}\n\n默认 user prompt:\n{default_user_prompt}"
                "\n\n可选示例:\n{examples_json}",
            ),
        ]
    )
    return prompt | structured


def optimize_prompt(
    profile: ReportProfile,
    *,
    config: Any,
    runnable: Any | None = None,
    examples: list[dict[str, Any]] | list[PromptExample] | None = None,
) -> PromptArtifact:
    default = compile_default_prompt(profile)
    selected_examples = examples if examples is not None else profile.examples
    normalized_examples = [
        item.model_dump(mode="json") if isinstance(item, PromptExample) else item
        for item in selected_examples
    ]
    payload = {
        "profile_json": profile.model_dump(mode="json"),
        "default_system_prompt": default.system_prompt,
        "default_user_prompt": default.user_prompt,
        "examples": normalized_examples,
        "examples_json": json.dumps(
            normalized_examples, ensure_ascii=False, indent=2
        ),
    }
    candidate_result = (runnable or _create_optimizer_runnable(config)).invoke(payload)
    candidate = (
        candidate_result
        if isinstance(candidate_result, PromptCandidate)
        else PromptCandidate.model_validate(candidate_result)
    )
    bundle = PromptBundle(
        system_prompt=candidate.system_prompt,
        user_prompt=_candidate_user_prompt_or_default(
            profile,
            default,
            candidate.user_prompt,
        ),
    )
    validate_prompt_bundle(profile, bundle)
    return PromptArtifact(
        version=1,
        profile_digest=profile.digest(),
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        system_prompt=bundle.system_prompt,
        user_prompt=bundle.user_prompt,
    )


def save_prompt_artifact(path: str | Path, artifact: PromptArtifact) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    if destination.suffix.lower() in {".yaml", ".yml"}:
        text = yaml.safe_dump(
            artifact.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        )
    else:
        text = artifact.model_dump_json(indent=2)
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(destination)


def load_prompt_artifact(
    path: str | Path,
    *,
    profile: ReportProfile,
) -> PromptArtifact:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
        artifact = PromptArtifact.model_validate(payload)
    else:
        artifact = PromptArtifact.model_validate_json(text)
    if artifact.profile_digest != profile.digest():
        raise ValueError("prompt artifact belongs to a different profile")
    validate_prompt_bundle(profile, artifact.bundle())
    return artifact
