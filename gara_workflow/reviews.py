"""Structured review evidence tied to committed implementation, not report commits."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from pathlib import Path

from .common import Blocked, git, inside

REVIEW_BLOCK = re.compile(r"<!-- gara-review:v1 -->\s*```json\s*\n(.*?)\n```", re.S)
RECORDS = {"verify": "verification", "review": "review"}


def implementation_files(tasks: list[dict]) -> list[str]:
    return sorted({name for task in tasks for name in task["files"]})


def implementation_matches(repo: Path, sha: str, files: list[str]) -> bool:
    """Allow later documentation commits while requiring a real, ancestral SHA."""
    if not isinstance(sha, str) or not re.fullmatch(
        r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", sha
    ):
        return False
    resolved = git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}", check=False)
    if resolved.lower() != sha.lower():
        return False
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, "HEAD"],
        capture_output=True,
    )
    if ancestor.returncode:
        return False
    tree = git(repo, "ls-tree", "-r", "-z", sha, "--", *files)
    recorded = {}
    for entry in tree.split("\0"):
        if entry:
            metadata, name = entry.split("\t", 1)
            mode, kind, blob = metadata.split()
            recorded[name] = (mode, kind, blob)
    present = {name for name in files if os.path.lexists(inside(repo, name))}
    if recorded.keys() != present:
        return False
    for name, (mode, kind, blob) in recorded.items():
        path = repo / name
        info = path.lstat()
        if kind != "blob":
            return False
        if mode == "120000" and stat.S_ISLNK(info.st_mode):
            hashed = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "--stdin"],
                input=os.fsencode(os.readlink(path)),
                capture_output=True,
            )
            observed = hashed.stdout.decode("ascii", errors="replace").strip()
        elif mode in {"100644", "100755"} and stat.S_ISREG(info.st_mode):
            observed = git(repo, "hash-object", f"--path={name}", "--", name)
        else:
            return False
        # Direct blob hashing does not trust assume-unchanged flags in the index.
        if observed != blob:
            return False
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet", sha, "--", *files],
        capture_output=True,
    )
    return diff.returncode == 0


def read_review(path: Path, issue: str) -> dict:
    if not path.is_file():
        raise Blocked("Falta REVISION.md con el contrato gara-review:v1.")
    text = path.read_text(encoding="utf-8")
    blocks = list(REVIEW_BLOCK.finditer(text))
    if len(blocks) != 1 or text.count("<!-- gara-review:v1 -->") != 1:
        raise Blocked("REVISION.md necesita un único bloque JSON gara-review:v1.")
    try:
        data = json.loads(blocks[0][1])
    except json.JSONDecodeError as error:
        raise Blocked(f"JSON de revisión inválido: {error}") from error
    if (
        not isinstance(data, dict)
        or type(data.get("version")) is not int
        or data["version"] != 1
        or data.get("issue") != issue
        or not {"version", "issue", "verification"} <= data.keys()
        or data.keys() - {"version", "issue", "verification", "review"}
    ):
        raise Blocked(
            "Versión, issue o registros del contrato de revisión incorrectos."
        )
    return data


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_record(
    data: dict,
    phase: str,
    repo: Path,
    requirements: set[str],
    tasks: list[dict],
    *,
    current_implementation: bool = True,
) -> dict:
    key = RECORDS[phase]
    record = data.get(key)
    fields = {
        "implementation_sha",
        "author",
        "requirements",
        "checks",
        "findings",
        "limitations",
    }
    if not isinstance(record, dict) or record.keys() != fields:
        raise Blocked(f"El registro {key} carece de la evidencia mínima documentada.")
    author = record["author"]
    if (
        not isinstance(author, dict)
        or not {"name", "role"} <= author.keys()
        or author.keys() - {"name", "role", "session_id"}
        or any(not nonempty(author.get(field)) for field in author)
    ):
        raise Blocked(f"{key} debe declarar nombre y rol del autor.")
    covered = record["requirements"]
    if not isinstance(covered, list):
        raise Blocked(f"{key} debe cubrir los requisitos con resultados y evidencia.")
    ids = []
    for requirement in covered:
        if (
            not isinstance(requirement, dict)
            or not nonempty(requirement.get("id"))
            or requirement.get("result") != "passed"
            or not nonempty(requirement.get("evidence"))
        ):
            raise Blocked(f"{key} contiene un requisito sin resultado satisfactorio.")
        ids.append(requirement["id"])
    if len(ids) != len(set(ids)) or set(ids) != requirements:
        raise Blocked(f"{key} no cubre exactamente los requisitos de la SPEC.")
    checks = record["checks"]
    expected = {
        (task["id"], gate)
        for task in tasks
        for gate in range(1, len(task["acceptance"]) + 1)
    }
    if not isinstance(checks, list):
        raise Blocked(f"{key} necesita resultados de las aceptaciones ejecutadas.")
    observed = []
    for check in checks:
        if (
            not isinstance(check, dict)
            or not nonempty(check.get("task"))
            or type(check.get("gate")) is not int
            or type(check.get("returncode")) is not int
            or check["returncode"] != 0
            or not nonempty(check.get("summary"))
        ):
            raise Blocked(f"{key} contiene una aceptación sin resultado verificable.")
        observed.append((check["task"], check["gate"]))
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise Blocked(f"{key} debe identificar una vez cada tarea y aceptación.")
    for task in tasks:
        evidence = task.get("evidence", [])
        if (
            task.get("status") != "verified"
            or not isinstance(evidence, list)
            or len(evidence) != len(task["acceptance"])
            or any(
                not isinstance(entry, dict) or entry.get("returncode") != 0
                for entry in evidence
            )
        ):
            raise Blocked(f"{key} no coincide con las aceptaciones del coordinador.")
    findings = record["findings"]
    if not isinstance(findings, list):
        raise Blocked(f"{key} debe registrar hallazgos, aunque la lista sea vacía.")
    for finding in findings:
        if (
            not isinstance(finding, dict)
            or not isinstance(finding.get("severity"), str)
            or finding.get("severity") not in {"low", "medium", "high", "critical"}
            or not isinstance(finding.get("status"), str)
            or finding.get("status") not in {"resolved", "accepted"}
            or not nonempty(finding.get("summary"))
            or not nonempty(finding.get("evidence"))
        ):
            raise Blocked(f"{key} contiene un hallazgo sin cierre y evidencia.")
    limitations = record["limitations"]
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not nonempty(value) for value in limitations)
    ):
        raise Blocked(f"{key} debe declarar sus limitaciones.")
    if current_implementation and not implementation_matches(
        repo, record["implementation_sha"], implementation_files(tasks)
    ):
        raise Blocked(f"El SHA de {key} no acredita la implementación actual.")
    return record


def review_instructions(phase: str) -> str:
    key = RECORDS[phase]
    preserve = (
        "Conserva exactamente el registro verification y añade o actualiza review. "
        if phase == "review"
        else "Añade o actualiza verification; una review anterior puede quedar como evidencia histórica. "
    )
    return (
        "Escribe REVISION.md con un único bloque <!-- gara-review:v1 --> seguido de ```json. "
        'El objeto raíz usa {"version":1,"issue":"GAR-N","verification":{...},"review":{...}}; '
        "review es opcional hasta su fase. "
        + preserve
        + f"El registro {key} requiere implementation_sha (SHA completo de un commit real y ancestro de HEAD "
        "con la implementación actual; registra primero las correcciones de código), "
        'author:{"name":"autor real declarado","role":"rol utilizado"} (session_id opcional), '
        'requirements:[{"id":"R1","result":"passed","evidence":"evidencia concreta"}], '
        'checks:[{"task":"T1","gate":1,"returncode":0,"summary":"comando y resultado observado"}], '
        'findings:[] o [{"severity":"low|medium|high|critical","status":"resolved|accepted",'
        '"summary":"hallazgo","evidence":"reproducción y cierre"}], '
        'limitations:["límites de la comprobación y revisión humana pendiente"]. '
        "Cubre todos los requisitos y cada aceptación de cada tarea una vez. "
        "El informe registra autoría declarada; no acredita independencia ni revisión humana. "
        "No añadas afirmaciones de independencia al JSON. Un commit posterior solo documental "
        "no exige cambiar el SHA de implementación."
    )
