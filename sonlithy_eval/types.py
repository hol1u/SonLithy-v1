"""Shared model API types."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class GenParams:
    temperature: float = 0.0
    max_tokens: int = 2048
    seed: int | None = None


@dataclass(frozen=True)
class ChatResponse:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_s: float = 0.0
    finish_reason: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, object]


class ModelClient(Protocol):
    def chat(
        self,
        messages: list[Message],
        *,
        tools: list[ToolSpec] | None = None,
        params: GenParams,
    ) -> ChatResponse: ...