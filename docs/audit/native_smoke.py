"""Read-only native probes; calls real authenticated clients with inherited models."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def probe(engine: str, destination: Path) -> dict:
    from gara_workflow.common import (
        Blocked,
        WorkflowError,
        redact,
        redact_data,
        save_json,
    )
    from gara_workflow.engines import parse_result, stream_process

    question = (
        "Prueba de integración SOLO LECTURA del paquete de skills de Gara en este directorio. "
        "Lee catalog.json y skills/gara-plan/SKILL.md. Explica el modo de ejecución de gara-plan, "
        "sus agentes exactos y cuándo se usa el fallback. No edites archivos ni ejecutes el "
        "workflow, tests, Git, aplicaciones o servicios externos. "
    )
    if engine == "codex":
        argv = [
            "codex",
            "exec",
            "--json",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "-",
        ]
        prompt = (
            question
            + "Delega esa pregunta al agente nativo gara-scout en contexto nuevo y espera su devolución. No lances otros agentes. Si esa capacidad no está disponible, decláralo y resuelve en lectura. "
        )
    else:
        argv = [
            "claude",
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--agent",
            "gara-scout",
        ]
        prompt = question + "Usa tu rol gara-scout; no delegues. "
    prompt += 'Cierra con <!-- gara-result --> {"status":"completed","summary":"respuesta y límites reales"}; usa blocked si no puedes leer o responder. No atribuyas revisión humana ni independencia por tu nombre.'
    try:
        code, lines, stderr = stream_process(argv, ROOT, input_text=prompt, timeout=180)
        result = parse_result(engine, code, lines, stderr)
        save_json(destination / f"{engine}-session.json", redact_data(asdict(result)))
        metadata = {
            "engine": engine,
            "status": result.status,
            "delegation_observations": len(result.delegations),
            "completed_agent_observed": any(
                item.get("status") == "completed" for item in result.delegations
            ),
        }
        if engine == "claude":
            for line in lines:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if (
                    isinstance(event, dict)
                    and event.get("type") == "system"
                    and event.get("subtype") == "init"
                ):
                    metadata["gara_skills_registered"] = len(
                        [
                            name
                            for name in event.get("slash_commands", [])
                            if isinstance(name, str) and name.startswith("gara-")
                        ]
                    )
                    metadata["gara_agents_registered"] = len(
                        [
                            name
                            for name in event.get("agents", [])
                            if isinstance(name, str) and name.startswith("gara-")
                        ]
                    )
                    metadata["skill_tool_available"] = "Skill" in event.get("tools", [])
        return metadata
    except (Blocked, WorkflowError, OSError) as error:
        return {"engine": engine, "status": "blocked", "reason": redact(str(error))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("codex", "claude", "both"), default="both")
    parser.add_argument(
        "--destination", type=Path, default=ROOT / "output/validation/native"
    )
    args = parser.parse_args()
    engines = ("codex", "claude") if args.engine == "both" else (args.engine,)
    observations = [probe(engine, args.destination) for engine in engines]
    report = json.dumps(observations, ensure_ascii=False, indent=2) + "\n"
    args.destination.mkdir(parents=True, exist_ok=True)
    (args.destination / f"{args.engine}-observations.json").write_text(
        report, encoding="utf-8"
    )
    print(report, end="")
    if any(item["status"] != "completed" for item in observations):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
