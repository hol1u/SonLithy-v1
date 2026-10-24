"""Evaluation orchestration and artifact generation."""

import json
import re
import subprocess
import time
import uuid
from pathlib import Path

from . import __version__
from .tasks import Task, dataset_hash
from .test_runner import run_tests
from .types import GenParams, Message

CODE_BLOCK = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def extract_code(response: str) -> str | None:
    matches = CODE_BLOCK.findall(response)
    return matches[0] if len(matches) == 1 else None


def _attempt(client, task: Task, params: GenParams, previous: dict | None = None) -> dict:
    prompt = (f"Task ID: {task.id}\n{task.prompt}\n\nReturn exactly one fenced python code block "
              f"containing the complete {task.entry_file}.")
    messages = [Message(role="user", content=prompt)]
    if previous is not None:
        messages.append(Message(
            role="user",
            content=("Your previous code failed. Fix it using this test output.\n"
                     f"Previous code:\n```python\n{previous['code'] or ''}\n```\n"
                     f"Test output:\n{previous['output']}"),
        ))
    started = time.monotonic()
    response = client.chat(messages, params=params)
    elapsed = time.monotonic() - started
    code = extract_code(response.content)
    result = {"response": response.content, "code": code,
              "latency_s": response.latency_s or elapsed,
              "prompt_tokens": response.prompt_tokens,
              "completion_tokens": response.completion_tokens}
    if code is None:
        result.update(status="format_error", output="Expected exactly one ```python code block.")
    else:
        result.update(run_tests(task.path, code, task.timeout_s))
    return result


def run_evaluation(
    tasks: list[Task], client, tasks_root: Path, out_dir: Path, *, mode: str,
    samples: int, seed: int, model_config: dict,
) -> Path:
    if mode not in {"single", "repair"}:
        raise ValueError("mode must be 'single' or 'repair'")
    if samples < 1:
        raise ValueError("samples must be at least 1")
    run_dir = Path(out_dir) / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    run_dir.mkdir(parents=True)
    results = []
    for sample in range(samples):
        params = GenParams(seed=seed + sample)
        for task in tasks:
            first = _attempt(client, task, params)
            attempts = [first]
            final = first
            if mode == "repair" and first["status"] != "passed":
                final = _attempt(client, task, params, first)
                attempts.append(final)
            prompt_token_values = [item["prompt_tokens"] for item in attempts
                                   if item["prompt_tokens"] is not None]
            completion_token_values = [item["completion_tokens"] for item in attempts
                                       if item["completion_tokens"] is not None]
            results.append({
                "id": task.id, "sample": sample, "response": final["response"],
                "extracted_code": final["code"], "status": final["status"],
                "test_output": final["output"],
                "prompt_tokens": sum(prompt_token_values) if prompt_token_values else None,
                "completion_tokens": sum(completion_token_values) if completion_token_values else None,
                "latency_s": sum(item["latency_s"] for item in attempts),
                "attempts": attempts,
            })
    with (run_dir / "results.jsonl").open("w", encoding="utf-8") as stream:
        for result in results:
            stream.write(json.dumps(result, sort_keys=True) + "\n")
    solved_single = sum(item["attempts"][0]["status"] == "passed" for item in results)
    solved_after_repair = sum(item["status"] == "passed" for item in results)
    latencies = [item["latency_s"] for item in results]
    token_values = [attempt[key] for item in results for attempt in item["attempts"]
                    for key in ("prompt_tokens", "completion_tokens") if attempt[key] is not None]
    summary = {
        "solved_single": solved_single,
        "solved_after_repair": solved_after_repair,
        "repair_gain": solved_after_repair - solved_single,
        "format_errors": sum(item["status"] == "format_error" for item in results),
        "timeouts": sum(item["status"] == "timeout" for item in results),
        "mean_latency_s": sum(latencies) / len(latencies) if latencies else 0.0,
        "total_tokens": sum(token_values),
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = None
    snapshot = {
        "model": {key: value for key, value in model_config.items() if "key" not in key.lower()},
        "seed": seed, "mode": mode, "samples": samples, "git_commit": git_commit,
        "dataset_hash": dataset_hash(Path(tasks_root)), "harness_version": __version__,
    }
    (run_dir / "config.snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_dir