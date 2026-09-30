"""Filesystem, Git and task contracts. The runtime has no third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TASK_BLOCK = re.compile(r"<!-- gara-tasks:v1 -->\s*```json\s*\n(.*?)\n```", re.S)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
ISSUE = re.compile(r"GAR-[1-9][0-9]*\Z")
STATUSES = {"pending", "running", "blocked", "verified"}


class WorkflowError(Exception):
    """A reported failure, rather than an unhandled exception."""


class Blocked(WorkflowError):
    """Progress requires a decision, a prerequisite or reconciliation."""


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".gara-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def save_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sensitive_field(name: str) -> bool:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
    return normalized in {
        "token",
        "secret",
        "password",
        "passwd",
        "passphrase",
        "api_key",
        "apikey",
        "authorization",
        "credentials",
        "cookie",
        "set_cookie",
        "private_key",
    } or normalized.endswith(
        (
            "_token",
            "_secret",
            "_password",
            "_passwd",
            "_api_key",
            "_access_key",
            "_private_key",
        )
    )


def redact_data(value: Any, *, _depth: int = 0) -> Any:
    """Scrub structured fields as well as strings before persisting provider data."""
    if _depth > 32:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if sensitive_field(str(key))
            else redact_data(item, _depth=_depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_data(item, _depth=_depth + 1) for item in value]
    if isinstance(value, str):
        return _redact_text(value, _depth)
    return value


def _redact_text(text: str, depth: int) -> str:
    # A summary can contain an embedded JSON object or a JSON-encoded JSON string.
    # Decode complete fragments to preserve structure, including escaped quotes.
    if depth < 16:
        decoder = json.JSONDecoder()
        pieces, cursor = [], 0
        while match := re.search(r'[\[{"]', text[cursor:]):
            start = cursor + match.start()
            try:
                value, length = decoder.raw_decode(text[start:])
            except (ValueError, RecursionError):
                pieces.append(text[cursor : start + 1])
                cursor = start + 1
                continue
            pieces.append(text[cursor:start])
            pieces.append(
                json.dumps(redact_data(value, _depth=depth + 1), ensure_ascii=False)
            )
            cursor = start + length
        pieces.append(text[cursor:])
        text = "".join(pieces)
    text = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED]", text)

    def quoted(match: re.Match) -> str:
        if not sensitive_field(match["key"]):
            return match[0]
        value = match["value"]
        quote = re.match(r"\\*[\"']", value)
        replacement = quote[0] + "[REDACTED]" + quote[0] if quote else "[REDACTED]"
        return match["prefix"] + replacement

    # Also handle incomplete/non-JSON logging syntax and escaped field delimiters.
    text = re.sub(
        r"(?P<prefix>(?P<q>\\*[\"'])(?P<key>[A-Za-z_][A-Za-z0-9_-]*)(?P=q)\s*[:=]\s*)"
        r"(?P<value>(?P<vq>\\*[\"'])(?:(?!(?<!\\)(?P=vq)).)*(?<!\\)(?P=vq)|[^\s,;}\]]+)",
        quoted,
        text,
        flags=re.S,
    )

    def assignment(match: re.Match) -> str:
        if not sensitive_field(match["key"]):
            return match[0]
        if (
            match["key"].lower() == "authorization"
            and match["value"].lower() == "bearer"
        ):
            return match[0]
        return match["key"] + match["separator"] + "[REDACTED]"

    return re.sub(
        r"(?P<key>\b[A-Za-z_][A-Za-z0-9_-]*)(?P<separator>\s*[=:]\s*)"
        r"(?P<value>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;]+)",
        assignment,
        text,
    )


def redact(text: str) -> str:
    return _redact_text(text, 0)


def git(repo: Path, *args: str, check: bool = True) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and process.returncode:
        raise WorkflowError(
            redact(process.stderr.strip()) or "Git no pudo completar la operación."
        )
    return process.stdout.rstrip("\r\n")


def repository(location: Path, *, gara: bool = True) -> Path:
    root = Path(git(location, "rev-parse", "--show-toplevel")).resolve()
    remotes = git(root, "remote", "-v", check=False)
    if (
        gara
        and root.name.lower() != "gara"
        and not re.search(r"(?:/|:|\\)gara(?:\.git)?(?:\s|$)", remotes, re.I)
    ):
        raise Blocked(
            "El checkout no está identificado como Gara por su raíz o remoto."
        )
    return root


def inside(root: Path, relative: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or any(char in relative for char in '\\\x00:*?<>|"')
    ):
        raise WorkflowError("Las rutas del contrato deben ser relativas y usar '/'.")
    path = Path(relative)
    if (
        path.is_absolute()
        or ".." in path.parts
        or any(part.lower() == ".git" for part in path.parts)
    ):
        raise WorkflowError(f"Ruta fuera del contrato: {relative}")
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise WorkflowError(f"Ruta fuera del checkout: {relative}")
    return target


def runtime_dir(repo: Path, slug: str) -> Path:
    if not SLUG.fullmatch(slug):
        raise WorkflowError("El slug debe usar minúsculas, números y guiones.")
    path = Path(git(repo, "rev-parse", "--git-path", f"gara-workflow/{slug}"))
    return (path if path.is_absolute() else repo / path).resolve()


def specification(path: Path) -> tuple[str, set[str]]:
    if not path.is_file():
        raise Blocked(f"Falta {path.name}; ejecuta gara-spec primero.")
    text = path.read_text(encoding="utf-8")
    header = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    if not header or not re.search(r"^approved:\s*true\s*$", header[1], re.M):
        raise Blocked(
            "La SPEC debe registrar approved: true tras la autorización del usuario."
        )
    match = re.search(r'^issue:\s*["\']?(GAR-[0-9]+)["\']?\s*$', header[1], re.M)
    if not match or not ISSUE.fullmatch(match[1]):
        raise Blocked("La SPEC debe identificar un issue GAR-N.")
    requirements = set(re.findall(r"^###\s+(R[1-9][0-9]*)\b", text, re.M))
    if not requirements:
        raise Blocked(
            "La SPEC debe contener requisitos con encabezados '### R1 — ...'."
        )
    if re.search(r"^##\s+Bloqueado\b", text, re.M):
        raise Blocked("La SPEC contiene decisiones bloqueantes pendientes.")
    return match[1], requirements


def read_tasks(path: Path, repo: Path, issue: str, requirements: set[str]) -> dict:
    if not path.is_file():
        raise Blocked("Falta TAREAS.md; ejecuta gara-tasks primero.")
    match = TASK_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        raise WorkflowError("TAREAS.md no contiene el contrato gara-tasks:v1.")
    try:
        data = json.loads(match[1])
    except json.JSONDecodeError as error:
        raise WorkflowError(f"JSON de tareas inválido: {error}") from error
    validate_tasks(data, repo, issue, requirements)
    return data


def validate_tasks(data: dict, repo: Path, issue: str, requirements: set[str]) -> None:
    if (
        not isinstance(data, dict)
        or data.get("version") != 1
        or data.get("issue") != issue
    ):
        raise WorkflowError("Versión o issue del contrato de tareas incorrecto.")
    tasks, batches = data.get("tasks"), data.get("batches")
    if (
        not isinstance(tasks, list)
        or not tasks
        or not isinstance(batches, list)
        or not batches
    ):
        raise WorkflowError("El contrato necesita tareas y tandas no vacías.")
    ids, covered = set(), set()
    for task in tasks:
        if not isinstance(task, dict):
            raise WorkflowError("Cada tarea debe ser un objeto.")
        identifier = task.get("id")
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"T[1-9][0-9]*", identifier)
            or identifier in ids
        ):
            raise WorkflowError("IDs de tarea inválidos o duplicados.")
        ids.add(identifier)
        refs = task.get("requirements")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(r, str) or r not in requirements for r in refs)
        ):
            raise WorkflowError(f"{identifier}: requisitos inexistentes o vacíos.")
        covered.update(refs)
        if not isinstance(task.get("briefing"), str) or not task["briefing"].strip():
            raise WorkflowError(f"{identifier}: falta un briefing ejecutable.")
        if not isinstance(task.get("status"), str) or task["status"] not in STATUSES:
            raise WorkflowError(f"{identifier}: estado inválido.")
        if type(task.get("checkpoint", False)) is not bool:
            raise WorkflowError(f"{identifier}: checkpoint debe ser booleano.")
        if type(task.get("weight", 1)) is not int or task.get("weight", 1) not in (
            1,
            2,
            4,
        ):
            raise WorkflowError(f"{identifier}: weight debe ser 1, 2 o 4.")
        if (
            not isinstance(task.get("depends_on"), list)
            or not isinstance(task.get("files"), list)
            or not task["files"]
        ):
            raise WorkflowError(
                f"{identifier}: faltan dependencias o archivos asignados."
            )
        if any(not isinstance(dep, str) for dep in task["depends_on"]):
            raise WorkflowError(f"{identifier}: dependencias inválidas.")
        for name in task["files"]:
            target = inside(repo, name)
            if target.is_dir():
                raise WorkflowError(
                    f"{identifier}: asigna archivos concretos, no directorios."
                )
        acceptance = task.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance:
            raise WorkflowError(f"{identifier}: falta aceptación ejecutable.")
        for gate in acceptance:
            if (
                not isinstance(gate, dict)
                or not isinstance(gate.get("argv"), list)
                or not gate["argv"]
            ):
                raise WorkflowError(f"{identifier}: acceptance requiere argv.")
            if any(
                not isinstance(arg, str) or not arg or "\x00" in arg
                for arg in gate["argv"]
            ):
                raise WorkflowError(f"{identifier}: argumentos inválidos.")
            inside(repo, gate.get("cwd", "."))
            if (
                type(gate.get("timeout", 600)) is not int
                or gate.get("timeout", 600) < 1
            ):
                raise WorkflowError(f"{identifier}: timeout inválido.")
    if covered != requirements:
        raise WorkflowError("Hay requisitos de la SPEC sin tarea ni prueba asignada.")
    by_id = {t["id"]: t for t in tasks}
    scheduled = set()
    for batch in batches:
        if not isinstance(batch, list) or not batch or len(batch) > 3:
            raise WorkflowError("Cada tanda admite de una a tres tareas.")
        paths: set[Path] = set()
        weight = 0
        for identifier in batch:
            if (
                not isinstance(identifier, str)
                or identifier not in ids
                or identifier in scheduled
                or batch.count(identifier) > 1
            ):
                raise WorkflowError(
                    "Una tarea falta, se repite o no existe en el horario."
                )
            task = by_id[identifier]
            if any(dep not in scheduled for dep in task["depends_on"]):
                raise WorkflowError(
                    f"{identifier}: dependencia inexistente, cíclica o todavía no programada."
                )
            targets = {inside(repo, name) for name in task["files"]}
            if any(
                a == b or a.is_relative_to(b) or b.is_relative_to(a)
                for a in targets
                for b in paths
            ):
                raise WorkflowError(
                    "Dos tareas de una tanda escriben rutas que colisionan."
                )
            paths.update(targets)
            weight += task.get("weight", 1)
        if weight > 4:
            raise WorkflowError("La carga de una tanda supera 4.")
        scheduled.update(batch)
    if scheduled != ids:
        raise WorkflowError("Hay tareas sin programar.")


def write_tasks(path: Path, data: dict) -> None:
    text = path.read_text(encoding="utf-8")
    block = (
        "<!-- gara-tasks:v1 -->\n```json\n"
        + json.dumps(data, ensure_ascii=False, indent=2)
        + "\n```"
    )
    atomic_write(path, TASK_BLOCK.sub(lambda _: block, text, count=1))


def task_fingerprint(data: dict) -> str:
    contract = dict(data)
    contract["tasks"] = [
        {k: v for k, v in task.items() if k not in {"status", "evidence"}}
        for task in data["tasks"]
    ]
    return hashlib.sha256(
        json.dumps(contract, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def resolve_command(argv: list[str], cwd: Path) -> list[str]:
    """Avoid passing prompts/arguments through cmd.exe or PowerShell shims."""
    executable = argv[0]
    if executable in {"python", "python3", "py"}:
        for name in (".venv", "venv"):
            for relative in (f"{name}/Scripts/python.exe", f"{name}/bin/python"):
                candidate = cwd / relative
                if candidate.is_file():
                    return [str(candidate), *argv[1:]]
        return [sys.executable, *argv[1:]]
    path = Path(executable)
    if not path.is_absolute() and ("/" in executable or "\\" in executable):
        path = cwd / path
    found = str(path) if path.is_file() else shutil.which(executable)
    if not found and os.name == "nt":
        # WinGet updates PATH for new shells, which may not include this process yet.
        if executable == "claude" and os.environ.get("LOCALAPPDATA"):
            packages = Path(os.environ["LOCALAPPDATA"]) / "Microsoft/WinGet/Packages"
            found = next(
                (
                    str(p)
                    for p in packages.glob("Anthropic.ClaudeCode_*/claude.exe")
                    if p.is_file()
                ),
                None,
            )
        elif executable in {"codex", "npm", "npx"} and os.environ.get("APPDATA"):
            candidate = Path(os.environ["APPDATA"]) / "npm" / f"{executable}.cmd"
            found = str(candidate) if candidate.is_file() else None
    if not found:
        raise Blocked(f"No se encuentra el ejecutable {executable}.")
    path = Path(found).resolve()
    if path.suffix.lower() == ".py":
        return [sys.executable, str(path), *argv[1:]]
    if path.suffix.lower() in {".ps1", ".cmd", ".bat"}:
        module = {
            "codex": "@openai/codex/bin/codex.js",
            "npm": "npm/bin/npm-cli.js",
            "npx": "npm/bin/npx-cli.js",
        }.get(path.stem.lower())
        node = shutil.which("node")
        if node and module:
            for parent in (path.parent, Path(node).parent):
                script = parent / "node_modules" / module
                if script.is_file():
                    return [node, str(script), *argv[1:]]
        raise Blocked(
            f"El wrapper {path.name} necesita un ejecutable nativo o su entrada Node; no se interpolan argumentos en un shell."
        )
    return [str(path), *argv[1:]]
