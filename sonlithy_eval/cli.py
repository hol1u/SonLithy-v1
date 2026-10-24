"""Command-line entry point."""

import argparse
import os
from pathlib import Path

import yaml

from .clients import MockClient, OpenAICompatClient
from .runner import run_evaluation
from .tasks import load_tasks


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="sonlithy-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--model-config", required=True, type=Path)
    run_parser.add_argument("--tasks", default=Path("tasks/"), type=Path)
    run_parser.add_argument("--mode", choices=("single", "repair"), default="single")
    run_parser.add_argument("--samples", type=int, default=1)
    run_parser.add_argument("--seed", type=int, default=0)
    run_parser.add_argument("--out", default=Path("runs/"), type=Path)
    args = parser.parse_args(argv)

    config = yaml.safe_load(args.model_config.read_text(encoding="utf-8")) or {}
    provider = config.get("provider", config.get("type", "openai_compat"))
    if provider == "mock":
        client = MockClient(args.tasks, config.get("behavior", "reference"))
    elif provider in {"openai", "openai_compat"}:
        base_url = config.get("base_url") or os.getenv("OPENAI_BASE_URL")
        model = config.get("model") or os.getenv("OPENAI_MODEL")
        if not base_url or not model:
            parser.error("OpenAI-compatible config requires base_url and model")
        client = OpenAICompatClient(
            base_url=base_url,
            model=model,
            api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY"),
            timeout_s=float(config.get("timeout_s", 30)),
        )
    else:
        parser.error(f"Unsupported model provider: {provider}")
    tasks = load_tasks(args.tasks)
    run_dir = run_evaluation(
        tasks, client, args.tasks, args.out, mode=args.mode, samples=args.samples,
        seed=args.seed, model_config=config,
    )
    print(run_dir)


if __name__ == "__main__":
    main()