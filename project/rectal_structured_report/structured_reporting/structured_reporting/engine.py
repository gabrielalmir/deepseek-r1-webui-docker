from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

from .optimizer import PromptArtifact
from .profile import ReportProfile
from .prompt import PromptBundle, compile_default_prompt, validate_prompt_bundle
from .providers import ProviderConfig
from .schema import compile_schema


def _resolve_prompt(
    profile: ReportProfile,
    prompt: PromptBundle | PromptArtifact | None,
) -> PromptBundle:
    if prompt is None:
        return compile_default_prompt(profile)
    if isinstance(prompt, PromptArtifact):
        if prompt.profile_digest != profile.digest():
            raise ValueError("prompt artifact belongs to a different profile")
        bundle = prompt.bundle()
    else:
        bundle = prompt
    validate_prompt_bundle(profile, bundle)
    return bundle


class ExtractionEngine:
    def __init__(
        self,
        profile: ReportProfile,
        *,
        runnable: Any,
        prompt: PromptBundle | PromptArtifact | None = None,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        schema: Any | None = None,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        self.profile = profile
        self.prompt = _resolve_prompt(profile, prompt)
        self.schema = schema or compile_schema(profile)
        self.runnable = runnable
        self.max_retries = max_retries
        self.sleep = sleep

    def extract(self, report: str | None) -> dict[str, Any]:
        if report is None or not str(report).strip():
            return {field.output_label: None for field in self.profile.fields}

        payload = {"report": str(report)}
        for attempt in range(self.max_retries):
            try:
                result = self.runnable.invoke(payload)
                validated = (
                    result
                    if isinstance(result, self.schema)
                    else self.schema.model_validate(result)
                )
                return validated.model_dump(by_alias=True, mode="json")
            except Exception:
                if attempt + 1 >= self.max_retries:
                    raise
                self.sleep(float(2**attempt))
        raise RuntimeError("unreachable")


def create_live_engine(
    profile: ReportProfile,
    *,
    config: ProviderConfig,
    prompt: PromptBundle | PromptArtifact | None = None,
    max_retries: int = 3,
) -> ExtractionEngine:
    bundle = _resolve_prompt(profile, prompt)
    schema = compile_schema(profile)
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=bundle.system_prompt),
            HumanMessagePromptTemplate.from_template(bundle.user_prompt),
        ]
    )
    llm = ChatOpenAI(
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        temperature=0,
        max_retries=0,
        timeout=120,
    )
    method = "json_mode" if config.provider == "deepseek" else "json_schema"
    structured = llm.with_structured_output(schema, method=method)
    return ExtractionEngine(
        profile,
        runnable=chat_prompt | structured,
        prompt=bundle,
        max_retries=max_retries,
        schema=schema,
    )

