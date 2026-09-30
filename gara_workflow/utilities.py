"""Local metrics, Git findings and explicit remote observation."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from pathlib import Path

from .common import WorkflowError, git, redact, save_json


def fixes(repo: Path, destination: Path | None = None) -> dict:
    log = git(repo, "log", "-100", "--format=%H%x1f%s%x1f%b%x1e")
    rows = []
    for record in log.split("\x1e"):
        fields = record.strip().split("\x1f", 2)
        if len(fields) == 3 and re.match(r"fix(?:\([^)]*\))?:", fields[1]):
            bullets = [
                line.strip()[2:]
                for line in fields[2].splitlines()
                if line.strip().startswith("- ")
            ]
            rows.append(
                {
                    "commit": fields[0],
                    "title": redact(fields[1]),
                    "items": [redact(b) for b in bullets],
                    "category": None,
                }
            )
    result = {
        "repo": str(repo),
        "fixes": rows,
        "note": "Las categorías requieren juicio; no se infieren del prefijo Git.",
    }
    if destination:
        save_json(destination, result)
    return result


def sessions(repo: Path) -> dict:
    root = Path(git(repo, "rev-parse", "--git-path", "gara-workflow"))
    root = root if root.is_absolute() else repo / root
    rows = []
    for path in sorted(root.glob("*/state.json")):
        state = json.loads(path.read_text(encoding="utf-8"))
        for row in state.get("sessions", []):
            rows.append({"slug": state["slug"], "engine": state["engine"], **row})
    return {
        "sessions": rows,
        "resume": "Usa resume --slug <slug>; --resume-session reutiliza la sesión de revisión si corresponde.",
        "note": "Se enumeran sesiones del ejecutor; no se cierran ni se inventarían conversaciones de otras aplicaciones.",
    }


def watch_remote(host: str, state_path: str, follow: bool, interval: float) -> dict:
    if not re.fullmatch(
        r"(?:[a-zA-Z0-9_.-]+@)?[a-zA-Z0-9_.:-]+", host
    ) or host.startswith("-"):
        raise WorkflowError("Host SSH inválido.")
    if not state_path.startswith("/") or "\x00" in state_path or "\n" in state_path:
        raise WorkflowError(
            "El archivo de estado remoto debe ser una ruta POSIX absoluta."
        )
    while True:
        process = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=10",
                host,
                "cat -- " + shlex.quote(state_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if process.returncode:
            raise WorkflowError(
                "No se pudo leer el estado remoto: " + redact(process.stderr.strip())
            )
        data = json.loads(process.stdout)
        if not isinstance(data, dict):
            raise WorkflowError("El estado remoto no es un objeto JSON.")
        if not follow or data.get("status") in {"completed", "blocked", "failed"}:
            return data
        print(json.dumps(data, ensure_ascii=False), flush=True)
        time.sleep(interval)
