#!/usr/bin/env python3
"""Deterministic native-protocol fixture. Never used outside temporary tests."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

prompt = sys.stdin.read()
phase = re.search(r"Fase: ([a-z]+);", prompt)[1]
artifacts = Path(re.search(r"^Los artefactos están en (.+)\.$", prompt, re.M)[1])
repo = Path.cwd()
mode = os.environ.get("GARA_FAKE_MODE", "normal")
events = Path(os.environ["GARA_FAKE_EVENTS"])
with events.open("a", encoding="utf-8") as stream:
    stream.write(phase + "\n")


def result(status="completed", summary="Evidencia simulada", error=False):
    marker = "<!-- gara-result --> " + json.dumps(
        {"status": status, "summary": summary}
    )
    if "exec" in sys.argv:
        print(json.dumps({"type": "thread.started", "thread_id": "fixture-codex"}))
        print(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": marker},
                }
            )
        )
        print(
            json.dumps({"type": "turn.failed", "error": {"message": summary}})
            if error
            else json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {"input_tokens": 4, "output_tokens": 2},
                }
            )
        )
    else:
        print(
            json.dumps(
                {"type": "system", "subtype": "init", "session_id": "fixture-claude"}
            )
        )
        print(
            json.dumps(
                {
                    "type": "result",
                    "subtype": "error_during_execution" if error else "success",
                    "is_error": error,
                    "result": marker,
                    "session_id": "fixture-claude",
                    "usage": {"input_tokens": 4, "output_tokens": 2},
                }
            )
        )


def read_block(path, marker):
    block = re.search(
        r"<!-- " + marker + r" -->\s*```json\s*\n(.*?)\n```",
        path.read_text(encoding="utf-8"),
        re.S,
    )
    return json.loads(block[1])


def review_record():
    tasks = read_block(artifacts / "TAREAS.md", "gara-tasks:v1")["tasks"]
    requirements = sorted(
        set(
            re.findall(
                r"^###\s+(R[1-9][0-9]*)\b",
                (artifacts / "SPEC.md").read_text(encoding="utf-8"),
                re.M,
            )
        )
    )
    return {
        "implementation_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "author": {"name": "Fixture de protocolo", "role": "gara-verifier"},
        "requirements": [
            {
                "id": identifier,
                "result": "passed",
                "evidence": "Archivo y aceptaciones ejecutadas por el coordinador temporal.",
            }
            for identifier in requirements
        ],
        "checks": [
            {
                "task": task["id"],
                "gate": index,
                "returncode": 0,
                "summary": "Aceptación local de fixture: " + json.dumps(gate["argv"]),
            }
            for task in tasks
            for index, gate in enumerate(task["acceptance"], 1)
        ],
        "findings": [],
        "limitations": [
            "Cliente simulado; sin subagente ni revisión humana independiente."
        ],
    }


if phase == "build" and mode == "timeout":
    time.sleep(30)
if (
    phase == "build"
    and mode == "quota-once"
    and events.read_text().count("build\n") == 1
):
    result("failed", "429 quota exceeded", True)
    raise SystemExit(1)
if phase == "build" and mode == "permission":
    result("blocked", "Falta autorización")
    raise SystemExit(0)

artifacts.mkdir(parents=True, exist_ok=True)
if phase == "plan":
    (artifacts / "PLAN.md").write_text(
        "# Plan\n\nContrato del ejemplo temporal.\n", encoding="utf-8"
    )
elif phase == "tasks":
    failure = mode == "gate-failure"
    code = "from pathlib import Path; assert Path('feature.txt').read_text() == 'done'"
    if failure:
        code = "raise SystemExit(1)"
    if mode == "env-probe":
        code = (
            "import os; from pathlib import Path; "
            "assert 'GARA_SECRET_PROBE' not in os.environ; "
            "assert Path('feature.txt').read_text() == 'done'"
        )
    if mode == "gate-escape":
        code = "from pathlib import Path; Path('foreign.txt').write_text('bad')"
    tasks = [
        {
            "id": "T1",
            "requirements": ["R1"],
            "depends_on": [],
            "files": ["feature.txt"],
            "briefing": "Crea el archivo con done.",
            "acceptance": [{"argv": ["python", "-c", code], "cwd": ".", "timeout": 10}],
            "status": "verified" if mode == "initial-verified" else "pending",
            "weight": 1,
            "checkpoint": mode == "checkpoint",
        }
    ]
    batches = [["T1"]]
    if mode == "two-batches":
        tasks.append(
            {
                **tasks[0],
                "id": "T2",
                "depends_on": ["T1"],
                "files": ["second.txt"],
                "briefing": "Crea second.txt con done.",
                "acceptance": [
                    {
                        "argv": [
                            "python",
                            "-c",
                            "from pathlib import Path; assert Path('second.txt').read_text() == 'done'",
                        ],
                        "timeout": 10,
                    }
                ],
            }
        )
        batches.append(["T2"])
    contract = {"version": 1, "issue": "GAR-123", "tasks": tasks, "batches": batches}
    (artifacts / "TAREAS.md").write_text(
        "# Tareas\n\n<!-- gara-tasks:v1 -->\n```json\n"
        + json.dumps(contract)
        + "\n```\n",
        encoding="utf-8",
    )
elif phase == "build":
    if mode == "two-batches" and '"id": "T2"' in prompt:
        (repo / "second.txt").write_text("done", encoding="utf-8")
    else:
        (repo / "feature.txt").write_text("done", encoding="utf-8")
    if mode == "build-escape":
        (repo / "foreign.txt").write_text("bad", encoding="utf-8")
    if mode == "contract-change":
        path = artifacts / "TAREAS.md"
        path.write_text(
            path.read_text().replace("Crea el archivo con done.", "Cambia requisitos."),
            encoding="utf-8",
        )
    if mode == "quota-after-write":
        result("failed", "429 quota exceeded", True)
        raise SystemExit(1)
elif phase in {"verify", "review"}:
    path = artifacts / "REVISION.md"
    data = (
        read_block(path, "gara-review:v1")
        if phase == "review"
        else {"version": 1, "issue": "GAR-123"}
    )
    data["verification" if phase == "verify" else "review"] = review_record()
    path.write_text(
        "# Revisión\n\nPrueba local de fixture; no revisión humana.\n\n<!-- gara-review:v1 -->\n```json\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    if phase == "review" and mode == "review-regression":
        (repo / "feature.txt").write_text("broken", encoding="utf-8")
elif phase == "commit":
    if mode == "missing-commit":
        result()
        raise SystemExit(0)
    if mode == "crash-before-commit":
        result("failed", "Interrupción simulada antes del commit", True)
        raise SystemExit(1)
    subprocess.run(
        ["git", "add", "--", "specs", "feature.txt"], check=True, capture_output=True
    )
    if (repo / "second.txt").is_file():
        subprocess.run(
            ["git", "add", "--", "second.txt"], check=True, capture_output=True
        )
    changed = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], capture_output=True
    ).returncode
    if changed:
        # The fake provider models Git effects; the real provider is instructed to use gara-commit.
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "test: Guarda fixture\n\nPORQUÉ\nPrueba aislada.\n\nCÓMO\nRegistra evidencia simulada.\n\nDOCUMENTACIÓN\nArtefactos de fixture.",
            ],
            check=True,
            capture_output=True,
        )
elif phase == "publish":
    implementation_sha = read_block(artifacts / "REVISION.md", "gara-review:v1")[
        "review"
    ]["implementation_sha"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (artifacts / "ENTREGA.md").write_text(
        f"# Entrega simulada\nhttps://github.com/example/gara/pull/1\nIn Review\nImplementation SHA: {implementation_sha}\nSHA: {head}\n",
        encoding="utf-8",
    )
result()
