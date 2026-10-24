"""Run task tests in a temporary subprocess workspace."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import resource
except ImportError:
    resource = None

MAX_OUTPUT_BYTES = 12_000


def _limit_memory(mem_limit_mb: int | None):
    if resource is None or mem_limit_mb is None or hasattr(sys, "getandroidapilevel"):
        return None

    def apply_limit() -> None:
        limit = mem_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    return apply_limit


def _truncate(data: bytes) -> str:
    if len(data) <= MAX_OUTPUT_BYTES:
        return data.decode("utf-8", errors="replace")
    return data[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace") + "\n[output truncated]"


def run_tests(task_dir: Path, code: str, timeout_s: float, mem_limit_mb: int | None = 512) -> dict[str, str]:
    task_dir = Path(task_dir)
    metadata = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    entry_file = Path(metadata["entry_file"])
    if entry_file.is_absolute() or ".." in entry_file.parts:
        return {"status": "error", "output": "Unsafe entry_file in task metadata"}
    try:
        with tempfile.TemporaryDirectory(prefix="sonlithy-eval-") as temporary:
            workdir = Path(temporary)
            shutil.copytree(task_dir / "starter", workdir, dirs_exist_ok=True)
            shutil.copytree(task_dir / "tests", workdir / "tests")
            target = workdir / entry_file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                    cwd=workdir, capture_output=True, timeout=timeout_s, check=False,
                    preexec_fn=_limit_memory(mem_limit_mb),
                )
            except subprocess.TimeoutExpired as error:
                output = _truncate((error.stdout or b"") + (error.stderr or b""))
                return {"status": "timeout", "output": output}
            output = _truncate(result.stdout + result.stderr)
            return {"status": "passed" if result.returncode == 0 else "failed", "output": output}
    except Exception as error:
        return {"status": "error", "output": f"Test runner error: {type(error).__name__}: {error}"}