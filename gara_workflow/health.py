"""Measure observed contracts and evidence, without assigning quality scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import (
    WorkflowError,
    git,
    read_tasks,
    repository,
    runtime_dir,
    specification,
)


def report(repo: Path, slug: str) -> dict:
    from .cli import metrics

    repo = repository(repo)
    runtime = runtime_dir(repo, slug)
    artifacts = repo / "specs" / slug
    issue, requirements = specification(artifacts / "SPEC.md")
    tasks = read_tasks(artifacts / "TAREAS.md", repo, issue, requirements)["tasks"]
    state = (
        json.loads((runtime / "state.json").read_text(encoding="utf-8"))
        if (runtime / "state.json").is_file()
        else None
    )
    gates = [gate for task in tasks for gate in task.get("evidence", [])]
    return {
        "repo": str(repo),
        "head": git(repo, "rev-parse", "HEAD"),
        "issue": issue,
        "requirements": len(requirements),
        "covered_requirements": len({r for t in tasks for r in t["requirements"]}),
        "tasks": len(tasks),
        "statuses": {
            s: sum(t["status"] == s for t in tasks)
            for s in ("pending", "running", "blocked", "verified")
        },
        "declared_gates": sum(len(t["acceptance"]) for t in tasks),
        "recorded_gates": len(gates),
        "successful_recorded_gates": sum(g.get("returncode") == 0 for g in gates),
        "state": state.get("status") if state else None,
        "last_update": state.get("updated_at") if state else None,
        "sessions": metrics(runtime),
        "limits": "Los contadores miden evidencia registrada; no prueban suficiencia de las pruebas ni revisión humana.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Salud observada de un flujo Gara.")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(report(args.repo, args.slug), ensure_ascii=False, indent=2))
        return 0
    except (WorkflowError, OSError, ValueError) as error:
        print(f"Error: {error}")
        return 1
