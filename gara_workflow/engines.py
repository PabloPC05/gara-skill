"""Adapters for native Codex and Claude CLI JSON streams."""

from __future__ import annotations

import json
import os
import queue
import re
import signal
import subprocess
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .common import (
    GATE_ENVIRONMENT,
    Blocked,
    WorkflowError,
    redact,
    redact_data,
    redacted_tail,
    resolve_command,
    save_json,
)


def gate_environment() -> dict[str, str]:
    """Acceptance commands run outside the client's sandbox: pass no credentials."""
    allowed = {name.upper() for name in GATE_ENVIRONMENT}
    return {
        **{k: v for k, v in os.environ.items() if k.upper() in allowed},
        "PYTHONIOENCODING": "utf-8",
    }


@dataclass
class Result:
    status: str
    summary: str
    session_id: str = ""
    usage: dict = field(default_factory=dict)
    infrastructure: bool = False
    delegations: list[dict] = field(default_factory=list)


def protocol_id(value) -> str:
    return (
        value
        if isinstance(value, str) and re.fullmatch(r"[\w.:-]{1,128}", value, re.ASCII)
        else ""
    )


def observe_delegations(engine: str, event: dict, observed: list[dict]) -> None:
    """Keep provider-observed identities/statuses, never tool prompts or bodies."""
    records = []
    if engine == "codex":
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "collab_tool_call":
            return
        action = item.get("tool")
        if not isinstance(action, str) or action not in {
            "spawn_agent",
            "send_input",
            "wait",
            "close_agent",
        }:
            return
        receivers = item.get("receiver_thread_ids", [])
        states = item.get("agents_states", {})
        if not isinstance(receivers, list) or not isinstance(states, dict):
            return
        for agent in dict.fromkeys(
            protocol_id(value) for value in [*receivers, *states]
        ):
            if not agent:
                continue
            state = states.get(agent)
            status = state.get("status") if isinstance(state, dict) else "unknown"
            if not isinstance(status, str) or status not in {
                "pending_init",
                "running",
                "interrupted",
                "completed",
                "errored",
                "shutdown",
                "not_found",
            }:
                status = "unknown"
            tool_status = item.get("status")
            records.append(
                {
                    "engine": engine,
                    "source": "collab_tool_call",
                    "action": action,
                    "tool_call_id": protocol_id(item.get("id")),
                    "agent_id": agent,
                    "status": status,
                    "tool_status": tool_status
                    if isinstance(tool_status, str)
                    and tool_status in {"in_progress", "completed", "failed"}
                    else "unknown",
                }
            )
    else:
        message = event.get("message")
        content = message.get("content", []) if isinstance(message, dict) else []
        if not isinstance(content, list):
            return
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in (
                "Agent",
                "Task",
            ):
                arguments = block.get("input")
                role = (
                    arguments.get("subagent_type")
                    if isinstance(arguments, dict)
                    else ""
                )
                role = (
                    role
                    if isinstance(role, str)
                    and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", role)
                    else ""
                )
                records.append(
                    {
                        "engine": engine,
                        "source": "tool_use",
                        "action": "spawn_agent",
                        "tool_call_id": protocol_id(block.get("id")),
                        "role": role,
                        "status": "requested",
                    }
                )
            elif block.get("type") == "tool_result":
                call = protocol_id(block.get("tool_use_id"))
                request = next(
                    (
                        item
                        for item in reversed(observed)
                        if item.get("tool_call_id") == call
                        and item.get("source") == "tool_use"
                    ),
                    None,
                )
                if not call or not request:
                    continue
                body = block.get("content")
                texts = (
                    [body]
                    if isinstance(body, str)
                    else [
                        part.get("text", "") for part in body if isinstance(part, dict)
                    ]
                    if isinstance(body, list)
                    else []
                )
                identifiers = set()
                for value in texts:
                    if isinstance(value, str):
                        identifiers.update(
                            re.findall(
                                r"^agentId:[ \t]*([A-Za-z0-9_-]{1,128})(?:[ \t]+\([^\n]*\))?[ \t]*$",
                                value,
                                re.M,
                            )
                        )
                agent = next(iter(identifiers)) if len(identifiers) == 1 else ""
                records.append(
                    {
                        "engine": engine,
                        "source": "tool_result",
                        "action": "spawn_agent",
                        "tool_call_id": call,
                        "role": request.get("role", ""),
                        "agent_id": agent,
                        "status": "failed" if block.get("is_error") else "returned",
                    }
                )
        parent = protocol_id(event.get("parent_tool_use_id"))
        if parent:
            records.append(
                {
                    "engine": engine,
                    "source": "subagent_message",
                    "action": "activity",
                    "tool_call_id": parent,
                    "status": "running",
                }
            )
    for record in records:
        if record not in observed and len(observed) < 1000:
            observed.append(record)


def stop_owned_process(process: subprocess.Popen) -> None:
    """Never raise: this runs while another exception is propagating."""
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=20,
            )
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            # Descendants can outlive the leader and ignore SIGTERM.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        process.wait(timeout=20)
    except (subprocess.TimeoutExpired, OSError):
        try:
            process.kill()
        except OSError:
            pass


def stream_process(
    argv: list[str],
    cwd: Path,
    *,
    input_text: str = "",
    timeout: float = 3600,
    env: dict[str, str] | None = None,
) -> tuple[int, list[str], str]:
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    environment = (
        env if env is not None else {**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    process = subprocess.Popen(
        resolve_command(argv, cwd),
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        **options,
    )
    events: queue.Queue = queue.Queue(maxsize=2048)

    def read(pipe, kind):
        try:
            for line in pipe:
                events.put((kind, line))
        finally:
            pipe.close()
            events.put((kind, None))

    def write():
        try:
            process.stdin.write(input_text)
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    for pipe, kind in ((process.stdout, "out"), (process.stderr, "err")):
        threading.Thread(target=read, args=(pipe, kind), daemon=True).start()
    threading.Thread(target=write, daemon=True).start()
    started, finished = time.monotonic(), 0
    lines: deque[str] = deque(maxlen=10000)
    errors: deque[str] = deque(maxlen=1000)
    try:
        while finished < 2:
            if time.monotonic() - started > timeout:
                raise Blocked(
                    "La sesión superó su timeout; reconcilia el checkout antes de reanudar."
                )
            try:
                kind, line = events.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                finished += 1
            elif kind == "out":
                lines.append(line.rstrip())
            else:
                errors.append(line.rstrip())
        return (
            process.wait(timeout=5),
            list(lines),
            redacted_tail("\n".join(errors), 12000),
        )
    except BaseException:
        stop_owned_process(process)
        raise


def parse_result(engine: str, code: int, lines: list[str], stderr: str) -> Result:
    completed, failed, denied = False, False, False
    session, messages, usage, delegations = "", [], {}, []
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        observe_delegations(engine, event, delegations)
        kind = event.get("type")
        if not isinstance(kind, str):
            continue
        identifier = event.get("thread_id", event.get("session_id"))
        if isinstance(identifier, str) and not event.get("parent_tool_use_id"):
            session = identifier
        if engine == "codex":
            if kind == "turn.completed":
                completed = True
                usage = (
                    event.get("usage") if isinstance(event.get("usage"), dict) else {}
                )
            if kind in {"turn.failed", "error"}:
                failed = True
                messages.append(str(event.get("error", event.get("message", "error"))))
            item = event.get("item", {})
            if (
                kind == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "agent_message"
            ):
                if isinstance(item.get("text"), str):
                    messages.append(item["text"])
        else:
            if (
                kind == "permission_denied"
                or event.get("subtype") == "permission_denied"
            ):
                denied = True
            if kind == "result" and not event.get("parent_tool_use_id"):
                completed = True
                failed = (
                    bool(event.get("is_error"))
                    or event.get("subtype", "success") != "success"
                )
                denied = denied or bool(event.get("permission_denials"))
                usage = (
                    event.get("usage") if isinstance(event.get("usage"), dict) else {}
                )
                if "total_cost_usd" in event:
                    usage = {**usage, "cost_usd": event["total_cost_usd"]}
                messages.append(str(event.get("result", event.get("errors", ""))))
    summary = redact(
        "\n".join(messages).strip()
        or stderr.strip()
        or "El cliente no emitió un cierre de sesión válido."
    )
    # Quoted repository text can contain a marker; the closing one is the agent's own.
    markers = re.findall(r"<!-- gara-result -->\s*(\{[^\n]+\})", summary)
    session = redact(session)
    explicit = ""
    if markers:
        try:
            value = json.loads(markers[-1])
            explicit = value.get("status", "") if isinstance(value, dict) else ""
        except json.JSONDecodeError:
            pass
    infra = bool(
        re.search(
            r"rate.?limit|quota|overloaded|connection (?:reset|closed)|\b(?:529|429)\b",
            summary,
            re.I,
        )
    )
    # A completed explicit result that merely quotes a login message is not an auth failure.
    authentication = explicit != "completed" and bool(
        re.search(
            r"not logged in|authentication required|please run /login|invalid api key",
            summary,
            re.I,
        )
    )
    if denied or authentication or explicit == "blocked":
        return Result(
            "blocked", summary, session, redact_data(usage), delegations=delegations
        )
    if code or failed or not completed or explicit == "failed":
        return Result(
            "failed", summary, session, redact_data(usage), infra, delegations
        )
    if explicit != "completed":
        return Result(
            "blocked",
            "Falta el resultado explícito gara-result. " + summary,
            session,
            redact_data(usage),
            delegations=delegations,
        )
    return Result(
        "completed", summary, session, redact_data(usage), delegations=delegations
    )


def run_session(
    engine: str,
    prompt: str,
    cwd: Path,
    log: Path,
    *,
    timeout: float = 3600,
    client: str | None = None,
    config: dict | None = None,
    resume_id: str = "",
) -> Result:
    config = config or {}
    executable = client or config.get("client") or engine
    extra = config.get("args", [])
    if not isinstance(extra, list) or any(not isinstance(arg, str) for arg in extra):
        raise WorkflowError(
            "Los argumentos del cliente deben ser una lista de cadenas."
        )
    if any(
        arg
        in {
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-skip-permissions",
            "--yolo",
        }
        for arg in extra
    ):
        raise WorkflowError("El ejecutor no añade opciones de bypass de permisos.")
    if engine == "codex":
        argv = [executable, "exec"]
        if resume_id:
            argv += ["resume", resume_id]
        argv += ["--json", *extra, "-"]
    elif engine == "claude":
        argv = [executable, "-p", "--output-format", "stream-json", "--verbose", *extra]
        if resume_id:
            argv += ["--resume", resume_id]
    else:
        raise WorkflowError("Motor desconocido.")
    code, lines, stderr = stream_process(argv, cwd, input_text=prompt, timeout=timeout)
    result = parse_result(engine, code, lines, stderr)
    # Raw tool streams can contain credentials; persist the normalized result only.
    save_json(log, redact_data(asdict(result)))
    return result
