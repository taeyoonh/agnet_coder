"""Benchmark runner that reuses the existing agent pipelines."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  
    def load_dotenv(*_args, **_kwargs): 
        return False

load_dotenv()


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ENGINE_MODULES = {
    "local-multi": "app.agent.engine_local_multi",
    "local-single": "app.agent.engine_local_single",
    "api-multi": "app.agent.engine_api_multi",
    "api-single": "app.agent.engine_api_single",
    "local-exec": "app.agent.engine_local_exec",
    "api-exec": "app.agent.engine_api_exec",
    "local-selftest": "app.agent.engine_local_selftest",
    "api-selftest": "app.agent.engine_api_selftest",
}

CODE_BLOCK_RE = re.compile(r"```(?P<lang>[^\n]*)\n(?P<code>.*?)```", re.DOTALL)


@dataclass(slots=True)
class Task:
    task_id: str
    prompt: str
    language: Optional[str]
    checker: Optional[Path]


def load_tasks(path: Path) -> List[Task]:
    tasks: List[Task] = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            checker = Path(data["test"]).resolve() if data.get("test") else None
            language = data.get("language")
            tasks.append(
                Task(
                    task_id=data["id"],
                    prompt=data["prompt"],
                    language=language.lower() if isinstance(language, str) else None,
                    checker=checker,
                )
            )
    if not tasks:
        raise RuntimeError(f"No tasks loaded from {path}")
    return tasks


def load_agent(engine_name: str) -> Callable[..., Dict[str, str]]:
    module_name = ENGINE_MODULES.get(engine_name)
    if not module_name:
        raise ValueError(f"Unknown engine '{engine_name}'. Choices: {', '.join(ENGINE_MODULES)}")
    module = importlib.import_module(module_name)
    if not hasattr(module, "agent_reply"):
        raise AttributeError(f"{module_name} is missing agent_reply()")
    return module.agent_reply  


def extract_code_block(markdown: str, preferred_language: Optional[str]) -> Optional[str]:
    matches = list(CODE_BLOCK_RE.finditer(markdown))
    if not matches:
        return None

    preferred_language = (preferred_language or "").strip().lower()

    if preferred_language:

        for match in reversed(matches):
            lang = match.group("lang").strip().lower()
            code = match.group("code").strip()
            if lang == preferred_language:
                return code


    return matches[-1].group("code").strip()


def run_checker(checker: Path, code: str) -> Tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="bench-submission-") as tmpdir:
        submission = Path(tmpdir) / "submission.py"
        submission.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(checker), str(submission)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (proc.stdout + proc.stderr).strip()
        success = proc.returncode == 0
        if not output:
            output = "PASS" if success else "checker failed without output"
        return success, output


def write_results(path: Path, results: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for result in results:
            fp.write(json.dumps(result, ensure_ascii=False))
            fp.write("\n")


def run_suite(
    tasks: List[Task],
    agent: Callable[..., Dict[str, str]],
    engine_name: str,
    output_path: Path,
    label: str = "",
) -> None:
    results: List[Dict[str, object]] = []
    total = len(tasks)
    successes = 0

    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{total}] Running task '{task.task_id}'...", flush=True)
        print("  --- Prompt --------------------------------------------------")
        print(task.prompt.strip(), flush=True)
        started = time.perf_counter()
        error: Optional[str] = None
        checker_output = ""
        success = False
        code_block = None

        try:
            response = agent(task.prompt, task=task)
            elapsed = time.perf_counter() - started
            body = response.get("body", "")
            headline = response.get("headline", "")
        except Exception as exc:  
            elapsed = time.perf_counter() - started
            body = ""
            headline = ""
            error = f"agent error: {exc}"
            print(f"  ✖ Agent call failed: {exc}")
        else:

            print("  --- Agent response -------------------------------------------")
            print(body.strip() or "(empty response)", flush=True)

            code_block = extract_code_block(body, task.language)
            if not code_block:
                error = "no code block found in response"
                print("  ✖ Unable to locate code block in agent reply")

            else:
                code_block = code_block.replace("<END-OF-CODE>", "").strip()
                print("  --- Extracted code -------------------------------------------")
                print(code_block or "(code block empty)", flush=True)

                if task.checker and task.checker.exists():
                    success, checker_output = run_checker(task.checker, code_block)
                    print(f"  {'✔' if success else '✖'} Checker -> {checker_output.splitlines()[0]}")
                else:
                    success = True
                    checker_output = "no checker specified"

        if success:
            successes += 1

        result = {
            "task_id": task.task_id,
            "engine": engine_name,
            "label": label,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": round(elapsed, 3),
            "success": success,
            "error": error,
            "checker_output": checker_output,
            "headline": headline,
            "response_body": body,
            "code_block_present": code_block is not None,
        }
        results.append(result)

    write_results(output_path, results)

    print(
        f"\nCompleted {total} tasks with {successes} successes. "
        f"Results stored in {output_path}"
    )


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark tasks against an agent pipeline.")
    parser.add_argument(
        "--tasks",
        type=Path,
        default=Path("benchmarks/tasks.jsonl"),
        help="Path to the JSONL file that lists tasks to run.",
    )
    parser.add_argument(
        "--engine",
        choices=sorted(ENGINE_MODULES.keys()),
        default="local-multi",
        help="Which agent engine implementation to use.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only run the first N tasks (useful for smoke tests).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/latest.jsonl"),
        help="Where to store newline-delimited JSON results.",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="",
        help="Optional run label stored in each result row (e.g., pipeline or experiment name).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    tasks = load_tasks(args.tasks)
    if args.limit:
        tasks = tasks[: args.limit]
    agent = load_agent(args.engine)
    run_suite(tasks, agent, args.engine, args.output, label=args.label)


if __name__ == "__main__":
    main()
