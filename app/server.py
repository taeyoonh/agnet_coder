#!/usr/bin/env python3
"""Lightweight HTTP server that exposes the agent and static UI."""

from __future__ import annotations

import json
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

try:
    from dotenv import load_dotenv
except ModuleNotFoundError: 
    def load_dotenv(*_args, **_kwargs): 
        return False

from agent import ENGINE_ALIAS_MAP, agent_reply, agent_stream, normalize_engine_name

APP_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = APP_DIR.parent / "public"
SESSIONS: Dict[str, Dict[str, Any]] = {}

load_dotenv()


def _read_body(handler: SimpleHTTPRequestHandler) -> Dict:
    length = int(handler.headers.get("content-length", 0))
    body = handler.rfile.read(length) if length else b"{}"
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


class AgentHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:  
        """Silence default stdout logging to keep CLI tidy."""
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json_response(
        self, payload: Dict, status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        super().end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  
        if self.path.startswith("/api/agent-stream"):
            return self._handle_agent_stream()
        return super().do_GET()

    def do_POST(self) -> None: 
        if self.path == "/api/session":
            return self._handle_session()
        if self.path == "/api/agent":
            return self._handle_agent()
        self._json_response({"error": "Route not found"}, HTTPStatus.NOT_FOUND)


    def _handle_session(self) -> None:
        payload = _read_body(self)
        requested_engine = (payload.get("engine") or "").strip().lower()
        engine_override = normalize_engine_name(requested_engine) if requested_engine else None
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = {
            "history": [],
            "engine": engine_override,
        }
        effective_engine = engine_override or normalize_engine_name(None)
        self._json_response(
            {
                "sessionId": session_id,
                "engine": effective_engine,
                "availableEngines": sorted(ENGINE_ALIAS_MAP.keys()),
            }
        )

    def _handle_agent(self) -> None:
        payload = _read_body(self)
        session_id = payload.get("sessionId")
        message = (payload.get("message") or "").strip()
        if not session_id or session_id not in SESSIONS:
            self._json_response({"error": "Unknown session"}, HTTPStatus.BAD_REQUEST)
            return
        if not message:
            self._json_response({"error": "Message required"}, HTTPStatus.BAD_REQUEST)
            return

        session = SESSIONS[session_id]
        history = list(session["history"])
        requested_engine = (payload.get("engine") or "").strip().lower()
        engine_choice = requested_engine or session.get("engine")
        try:
            agent_message = agent_reply(message, history, engine=engine_choice)
        except Exception as exc: 
            self._json_response(
                {"error": f"Agent failed: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR
            )
            return

        session["history"].append({"role": "user", "content": message})
        assistant_content = (agent_message.get("body") or "")[:1200]
        session["history"].append({"role": "assistant", "content": assistant_content})
        self._json_response(agent_message)

    def _handle_agent_stream(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query or "")
        session_id = (params.get("sessionId") or [""])[0]
        message = ((params.get("message") or [""])[0] or "").strip()
        if not session_id or session_id not in SESSIONS:
            self._json_response({"error": "Unknown session"}, HTTPStatus.BAD_REQUEST)
            return
        if not message:
            self._json_response({"error": "Message required"}, HTTPStatus.BAD_REQUEST)
            return

        session = SESSIONS[session_id]
        history = list(session["history"])
        requested_engine = (params.get("engine") or [""])[0].strip().lower()
        engine_choice = requested_engine or session.get("engine")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        super().end_headers()

        final_body = ""
        try:
            for event in agent_stream(message, history, engine=engine_choice):
                if event.get("stage") == "complete":
                    final_body = event.get("content", "")
                self._sse_write(event)
        except BrokenPipeError:
            return
        except Exception as exc:  
            self._sse_write({"stage": "error", "content": f"Agent failed: {exc}"})
        finally:
            if final_body:
                session["history"].append({"role": "user", "content": message})
                session["history"].append(
                    {"role": "assistant", "content": final_body[:1200]}
                )

    def _sse_write(self, payload: Dict[str, str]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.wfile.write(b"data: ")
        self.wfile.write(data)
        self.wfile.write(b"\n\n")
        self.wfile.flush()


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AgentHandler)
    print(f"Agent UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
