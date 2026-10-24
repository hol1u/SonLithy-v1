"""Task loading and reproducible dataset hashing."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Task:
    id: str
    kind: str
    prompt: str
    entry_file: str
    timeout_s: float
    path: Path


def load_tasks(root: Path) -> list[Task]:
    tasks = []
    for metadata_path in sorted(root.glob("*/task.json")):
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        entry_file = Path(data["entry_file"])
        if entry_file.is_absolute() or ".." in entry_file.parts:
            raise ValueError(f"Unsafe entry_file in {metadata_path}")
        if data["kind"] not in {"implement", "fix_bug"}:
            raise ValueError(f"Unsupported task kind in {metadata_path}")
        task = Task(
            id=data["id"], kind=data["kind"], prompt=data["prompt"],
            entry_file=data["entry_file"], timeout_s=float(data["timeout_s"]),
            path=metadata_path.parent,
        )
        if not (task.path / "starter").is_dir() or not (task.path / "tests").is_dir():
            raise ValueError(f"Task {task.id} must contain starter/ and tests/")
        tasks.append(task)
    if len({task.id for task in tasks}) != len(tasks):
        raise ValueError("Task IDs must be unique")
    return tasks


def dataset_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(file for file in root.rglob("*") if file.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()