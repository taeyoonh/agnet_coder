# AI Agent Coding Coach (MVP)

This repository contains an AI-assisted coding planning prototype that runs
locally with a llama.cpp-backed LLM. The latest build replaces the heuristic
agent with a multi-step LangGraph pipeline (planner → coder → reviewer) so the
model produces higher-quality plans and code snippets.

## Architecture

- **`app/agent/engine.py`** – LangGraph orchestration that forwards chat history
  to a llama.cpp HTTP server. It now chains planner, coder, reviewer nodes and
  streams each stage (SSE) back to the UI for real-time visibility.
- **`app/server.py`** – threaded HTTP server that exposes `/api/session`,
  `/api/agent`, and serves the static frontend.
- **`public/`** – minimal UI written with vanilla JS + CSS that lets you iterate
  on prompts and read the agent's output.

Future work can swap the engine with an OpenAI/Anthropic client, add persistent
vector memory, and stream tokens back to the UI.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install llama.cpp (example on macOS):
   ```bash
   brew install llama.cpp
   ```
3. Start the DeepSeek model with the built-in server:
   ```bash
   llama-server -hf lmstudio-community/DeepSeek-Coder-V2-Lite-Instruct-GGUF:Q4_K_M
   ```
   By default this listens on `http://127.0.0.1:8080`. Export a different URL via
   `LLAMA_SERVER_URL` if needed.
4. Launch the web app:
   ```bash
   python app/server.py
   ```

Then open http://127.0.0.1:8000 in a browser. Each browser tab initializes a new
session so you can keep experiments separate.

## Benchmark runner

You can batch-evaluate prompts/models/agent variants with the built-in runner.

1. Define tasks in `benchmarks/tasks.jsonl` (or the new `benchmarks/tasks_swe.jsonl`
   for larger SWE-style evaluations). Each line is a JSON object with the
   fields: `id`, `prompt`, optional `language`, and `test` (path to a Python
   checker that receives the generated code). Algorithmic checkers now live in
   `benchmarks/algorithm_test/`, while the higher-context SWE exercises reside
   in `benchmarks/swe_benchmark_test/`.
2. Choose an engine:
   - `local-multi`, `local-single` – llama.cpp-backed agents (needs the local
     server running via `LLAMA_SERVER_URL`/`LLAMA_SERVER_MODEL`).
   - `api-multi`, `api-single` – OpenAI-backed agents (requires `OPENAI_API_KEY`).
3. Run the suite:
   ```bash
   python app/run_bench.py \
     --engine local-multi \
     --tasks benchmarks/tasks.jsonl \
     --output results/multi.jsonl
   ```

The runner stores newline-delimited JSON outputs (success, elapsed seconds,
checker logs, raw responses) so you can compute aggregate metrics later. Use
`--limit N` for smoke tests.

### Common run commands (short)
- Local execution agent (no toolchain, just codegen + checker):  
  `python app/run_bench.py --engine local-exec --label exec-loop --output results/exec.jsonl`
- Local self-test agent (agent writes/runs its own tests):  
  `python app/run_bench.py --engine local-selftest --tasks benchmarks/tasks.jsonl --output results/english_selftest.jsonl`
- API self-test (OpenAI):  
  `python app/run_bench.py --engine api-selftest --tasks benchmarks/tasks.jsonl --output results/english_selftest_api.jsonl`
- Smoke run first 5 tasks:  
  `python app/run_bench.py --engine local-multi --limit 5`
- Default output path (if omitted): `results/latest.jsonl`

## Next steps

1. Add LangGraph subgraphs for tool selection + retrieval augmented planning.
2. Persist session history (Redis/Postgres) for multi-device continuity.
3. Add WebSocket streaming so plans render progressively.
4. Package the server as FastAPI / Next.js API routes for production use.
