# SonLithy Eval

SonLithy Eval is a small Python harness for repeatable coding-task evaluations. It supports a deterministic mock client and an OpenAI-compatible chat-completions endpoint. The `tasks/` corpus contains 20 original draft tasks: 10 implementation exercises and 10 bug fixes.

## Run

```sh
python -m pip install -e '.[test]'
python -m sonlithy_eval run --model-config configs/mock.yaml --tasks tasks/ --mode single --samples 1 --seed 0 --out runs/
pytest
```

An OpenAI-compatible YAML config can provide `provider: openai_compat`, `base_url`, `model`, and optional `timeout_s` or `api_key`. `OPENAI_BASE_URL`, `OPENAI_MODEL`, and `OPENAI_API_KEY` provide environment-variable fallbacks. API keys are not written to run snapshots.

Each run writes `results.jsonl`, `summary.json`, and `config.snapshot.json` to a unique directory. The snapshot records the git commit when available and a SHA-256 digest of all task files.

## Execution warning

Test execution is **not a security boundary**. Model-produced Python can read the copied tests and may access the host filesystem or network. The harness applies a subprocess timeout and, where supported, a memory limit, but does not isolate filesystem or network access. Run model-generated code only in a disposable Codespace or container, and treat it as untrusted.