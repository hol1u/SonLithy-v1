import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from sonlithy_eval.clients import MockClient, OpenAICompatClient
from sonlithy_eval.runner import run_evaluation
from sonlithy_eval.tasks import dataset_hash, load_tasks
from sonlithy_eval.test_runner import run_tests
from sonlithy_eval.types import GenParams, Message

TASKS = Path(__file__).parents[1] / "tasks"


def test_reference_mock_solves_all_tasks_and_snapshot_is_stable(tmp_path):
    tasks = load_tasks(TASKS)
    assert len(tasks) == 20
    assert sum(task.kind == "implement" for task in tasks) == 10
    assert sum(task.kind == "fix_bug" for task in tasks) == 10

    summaries = []
    for _ in range(2):
        run_dir = run_evaluation(
            tasks, MockClient(TASKS), TASKS, tmp_path, mode="single", samples=1,
            seed=7, model_config={"provider": "mock", "api_key": "never-save"},
        )
        summary = json.loads((run_dir / "summary.json").read_text())
        summaries.append({key: value for key, value in summary.items() if key != "mean_latency_s"})
        snapshot = json.loads((run_dir / "config.snapshot.json").read_text())
        assert snapshot["git_commit"]
        assert snapshot["dataset_hash"] == dataset_hash(TASKS)
        assert "api_key" not in snapshot["model"]
        assert summary["solved_single"] == 20
    assert summaries[0] == summaries[1]


def test_wrong_mock_solves_zero_and_missing_code_is_format_error(tmp_path):
    tasks = load_tasks(TASKS)
    wrong_run = run_evaluation(
        tasks, MockClient(TASKS, "wrong"), TASKS, tmp_path, mode="single", samples=1,
        seed=0, model_config={"provider": "mock"},
    )
    assert json.loads((wrong_run / "summary.json").read_text())["solved_single"] == 0
    malformed_run = run_evaluation(
        tasks[:1], MockClient(TASKS, "no_code"), TASKS, tmp_path, mode="single", samples=1,
        seed=0, model_config={"provider": "mock"},
    )
    result = json.loads((malformed_run / "results.jsonl").read_text().splitlines()[0])
    assert result["status"] == "format_error"


def test_repair_mock_improves_score(tmp_path):
    tasks = load_tasks(TASKS)
    run_dir = run_evaluation(
        tasks, MockClient(TASKS, "repair"), TASKS, tmp_path, mode="repair", samples=2,
        seed=0, model_config={"provider": "mock"},
    )
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["repair_gain"] == 40


def test_task_file_changes_dataset_hash(tmp_path):
    import shutil

    copied = tmp_path / "tasks"
    shutil.copytree(TASKS / "implement-01", copied / "implement-01")
    before = dataset_hash(copied)
    metadata = copied / "implement-01" / "task.json"
    metadata.write_text(metadata.read_text() + " ")
    assert dataset_hash(copied) != before


def test_infinite_loop_times_out(tmp_path):
    task = tmp_path / "loop"
    (task / "starter").mkdir(parents=True)
    (task / "tests").mkdir()
    (task / "task.json").write_text(json.dumps({"entry_file": "solution.py"}))
    (task / "tests" / "test_loop.py").write_text("from solution import run\ndef test_loop(): run()\n")
    started = time.monotonic()
    result = run_tests(task, "def run():\n    while True:\n        pass\n", 0.3, mem_limit_mb=None)
    assert result["status"] == "timeout"
    assert time.monotonic() - started < 3


class _QuietHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        pass


def _serve(handler):
    server = _QuietHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_openai_compatible_response_retries_and_does_not_log_key(caplog):
    class Handler(BaseHTTPRequestHandler):
        attempts = 0

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.__class__.attempts += 1
            if self.__class__.attempts < 3:
                self.send_error(503)
                return
            body = json.dumps({
                "choices": [{"message": {"content": "answer"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    Handler.attempts = 0
    server, thread = _serve(Handler)
    try:
        client = OpenAICompatClient(f"http://127.0.0.1:{server.server_port}/v1", "test", "secret-sentinel")
        response = client.chat([Message("user", "hello")], params=GenParams(seed=3))
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    assert response.content == "answer"
    assert response.prompt_tokens == 4
    assert Handler.attempts == 3
    assert "secret-sentinel" not in caplog.text


def test_openai_compatible_client_times_out():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            time.sleep(0.2)
            try:
                self.send_response(200)
                self.end_headers()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, format, *args):
            pass

    server, thread = _serve(Handler)
    try:
        client = OpenAICompatClient(f"http://127.0.0.1:{server.server_port}", "test", timeout_s=0.03)
        try:
            client.chat([Message("user", "hello")], params=GenParams())
        except RuntimeError as error:
            assert "network error" in str(error) or "timed out" in str(error)
        else:
            raise AssertionError("Expected request timeout")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()