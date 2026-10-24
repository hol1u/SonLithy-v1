"""Deterministic mock and OpenAI-compatible HTTP clients."""

import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .types import ChatResponse, GenParams, Message, ToolSpec


class MockClient:
    def __init__(self, tasks_root: Path, behavior: str = "reference") -> None:
        if behavior not in {"reference", "wrong", "no_code", "repair"}:
            raise ValueError(f"Unknown mock behavior: {behavior}")
        self.tasks_root = tasks_root
        self.behavior = behavior
        self.calls: dict[str, int] = {}

    def chat(
        self, messages: list[Message], *, tools: list[ToolSpec] | None = None,
        params: GenParams,
    ) -> ChatResponse:
        del tools, params
        joined = "\n".join(message.content for message in messages)
        task_id_match = re.search(r"Task ID: ([A-Za-z0-9_-]+)", joined)
        if task_id_match is None:
            raise ValueError("MockClient requires a Task ID in the prompt")
        task_id = task_id_match.group(1)
        call_number = self.calls.get(task_id, 0)
        self.calls[task_id] = call_number + 1
        if self.behavior == "no_code":
            return ChatResponse(content="I cannot provide a solution.", finish_reason="stop")
        if self.behavior == "wrong" or (self.behavior == "repair" and call_number % 2 == 0):
            code = "raise AssertionError('deliberately incorrect mock solution')\n"
        else:
            reference_path = self.tasks_root / task_id / "reference" / "solution.py"
            code = reference_path.read_text(encoding="utf-8")
        return ChatResponse(content=f"```python\n{code.rstrip()}\n```", finish_reason="stop")


class OpenAICompatClient:
    def __init__(
        self, base_url: str, model: str, api_key: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s

    def chat(
        self, messages: list[Message], *, tools: list[ToolSpec] | None = None,
        params: GenParams,
    ) -> ChatResponse:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
        }
        if params.seed is not None:
            payload["seed"] = params.seed
        if tools:
            payload["tools"] = [
                {"type": "function", "function": {"name": tool.name,
                 "description": tool.description, "parameters": tool.parameters}}
                for tool in tools
            ]
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.base_url}/chat/completions", data=json.dumps(payload).encode("utf-8"),
            headers=headers, method="POST",
        )
        started = time.monotonic()
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout_s) as response:
                    data = json.loads(response.read().decode("utf-8"))
                choice = data["choices"][0]
                usage = data.get("usage") or {}
                return ChatResponse(
                    content=choice["message"]["content"] or "",
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    latency_s=time.monotonic() - started,
                    finish_reason=choice.get("finish_reason"),
                )
            except HTTPError as error:
                if error.code >= 500 and attempt < 2:
                    continue
                raise RuntimeError(f"Model server returned HTTP {error.code}") from None
            except (URLError, TimeoutError, OSError) as error:
                if attempt < 2:
                    continue
                if isinstance(error, TimeoutError):
                    raise RuntimeError("Model request timed out") from None
                raise RuntimeError("Model request failed due to a network error") from None
        raise RuntimeError("Model request failed")