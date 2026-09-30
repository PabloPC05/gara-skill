"""Generate native distributions and install only files owned by this package."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .common import WorkflowError, digest, inside, save_json


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise WorkflowError(f"Frontmatter inválido: {path}")
    fields = {}
    for line in match[1].splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise WorkflowError(f"Metadatos no escalares: {path}")
        value = value.strip()
        try:
            fields[key] = json.loads(value)
        except json.JSONDecodeError:
            fields[key] = value
    return fields, match[2]


def header(fields: dict) -> str:
    return (
        "---\n"
        + "\n".join(
            f"{name}: {json.dumps(value, ensure_ascii=False)}"
            for name, value in fields.items()
        )
        + "\n---\n"
    )


def _catalog(root: Path) -> dict:
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        raise WorkflowError(
            "La validación del paquete se ejecuta desde el checkout gara-skill."
        )
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def _valid_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and re.fullmatch(r"gara-[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None
        and len(name) <= 64
    )


def _validate_catalog(root: Path, catalog: dict) -> dict:
    agent_names = set()
    for role in catalog["agents"]:
        name = role.get("name")
        if not _valid_name(name) or name in agent_names:
            raise WorkflowError(f"Nombre de agente inválido o duplicado: {name}")
        agent_names.add(name)
        if not inside(root, role["source"]).is_file():
            raise WorkflowError(f"Falta la definición de {name}.")
        tools = role.get("claude_tools")
        if tools is not None and (not isinstance(tools, str) or not tools.strip()):
            raise WorkflowError(f"claude_tools debe ser una cadena o null: {name}")
        if "claude_disallowed_tools" in role:
            denied = role["claude_disallowed_tools"]
            if not (
                isinstance(denied, str)
                and denied.strip()
                or isinstance(denied, list)
                and all(isinstance(tool, str) and tool.strip() for tool in denied)
            ):
                raise WorkflowError(
                    f"claude_disallowed_tools debe ser una cadena o lista: {name}"
                )
            denied_names = (
                {tool.strip() for tool in denied.split(",")}
                if isinstance(denied, str)
                else {tool.strip() for tool in denied}
            )
            if tools and denied_names & {tool.strip() for tool in tools.split(",")}:
                raise WorkflowError(
                    f"Herramientas permitidas y denegadas a la vez: {name}"
                )
    names = set()
    for item in catalog["skills"]:
        name = item["name"]
        if not _valid_name(name) or name in names:
            raise WorkflowError(f"Nombre de skill inválido o duplicado: {name}")
        names.add(name)
        # Older minimal fixtures may omit both fields. New contracts need both.
        if "execution" in item or "agents" in item:
            execution, agents = item.get("execution"), item.get("agents")
            if (
                not isinstance(execution, str)
                or execution not in {"direct", "coordinated"}
                or not isinstance(agents, list)
                or not all(isinstance(agent, str) for agent in agents)
                or len(agents) != len(set(agents))
                or any(agent not in agent_names for agent in agents)
                or (execution == "direct" and agents)
                or (execution == "coordinated" and not agents)
            ):
                raise WorkflowError(f"Contrato de ejecución o agentes inválido: {name}")
        path = root / "skills" / name / "SKILL.md"
        fields, body = frontmatter(path)
        if (
            fields.get("name") != name
            or not isinstance(fields.get("description"), str)
            or not 1 <= len(fields["description"]) <= 1024
        ):
            raise WorkflowError(f"Identidad o descripción inválida: {name}")
        if not body.strip() or "[TODO:" in body:
            raise WorkflowError(f"Skill incompleta: {name}")
        for document in path.parent.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            for reference in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if reference.startswith(("http:", "https:", "#", "mailto:")):
                    continue
                relative = reference.split("#", 1)[0].strip("<>")
                if relative and not (document.parent / relative).exists():
                    raise WorkflowError(
                        f"Referencia inexistente en {document}: {reference}"
                    )
        for script in path.parent.rglob("*.py"):
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
    folders = {path.name for path in (root / "skills").iterdir() if path.is_dir()}
    if names != folders:
        raise WorkflowError("El catálogo y los directorios de skills no coinciden.")
    original = {row["original"] for row in catalog["mapping"]}
    archived = root / "export"
    if archived.exists():
        if not archived.is_dir():
            raise WorkflowError("El archivo histórico export debe ser un directorio.")
        expected = {
            p.relative_to(archived).as_posix()
            for pattern in (
                "skills/*/SKILL.md",
                "commands/*.md",
                "agents/*.md",
                "scripts/*",
            )
            for p in archived.glob(pattern)
            if p.is_file() and p.name != "README.md"
        }
        if not expected.issubset(original):
            raise WorkflowError("El catálogo no cubre todo el paquete original.")
    return {
        "status": "valid",
        "skills": len(names),
        "agents": len(catalog["agents"]),
        "original_components": len(original),
    }


def validate(root: Path) -> dict:
    return _validate_catalog(root, _catalog(root))


def _distribution_payload(root: Path, catalog: dict) -> dict[str, bytes]:
    """Calculate native files from authoritative sources without creating a build."""
    payload: dict[str, bytes] = {}
    for engine in ("codex", "claude"):
        for item in catalog["skills"]:
            folder = root / "skills" / item["name"]
            prefix = f"{engine}/skills/{item['name']}"
            for source in folder.rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    payload[f"{prefix}/{source.relative_to(folder).as_posix()}"] = (
                        source.read_bytes()
                    )
            # Each installed skill is self-contained; shared sources remain authoritative.
            payload[f"{prefix}/references/gara.md"] = (
                root / "profiles/gara.md"
            ).read_bytes()
            for reference in ("artifacts.md", "runtime.md", "delegation.md"):
                if (folder / "references" / reference).is_file():
                    payload[f"{prefix}/references/{reference}"] = (
                        root / "references" / reference
                    ).read_bytes()
            fields, body = frontmatter(folder / "SKILL.md")
            if engine == "claude" and item.get("explicit_only"):
                fields["disable-model-invocation"] = True
            payload[f"{prefix}/SKILL.md"] = (header(fields) + body).encode("utf-8")
            yaml = (
                f"interface:\n  display_name: {json.dumps(item['title'], ensure_ascii=False)}\n"
                f"  short_description: {json.dumps(item['short'], ensure_ascii=False)}\n"
                f"  default_prompt: {json.dumps('Usa $' + item['name'] + ' para trabajar en Gara.', ensure_ascii=False)}\n"
                f"policy:\n  allow_implicit_invocation: {'false' if item.get('explicit_only') else 'true'}\n"
            )
            if engine == "codex":
                payload[f"{prefix}/agents/openai.yaml"] = yaml.encode("utf-8")
            if item["name"] in {"gara-workflow", "gara-pdf", "gara-workflow-health"}:
                for source in (root / "gara_workflow").glob("*.py"):
                    payload[f"{prefix}/scripts/gara_workflow/{source.name}"] = (
                        source.read_bytes()
                    )
        for role in catalog["agents"]:
            body = (root / role["source"]).read_text(encoding="utf-8")
            if engine == "codex":
                fields = {
                    "name": role["name"],
                    "description": role["description"],
                    "developer_instructions": body,
                }
                if role.get("read_only"):
                    fields["sandbox_mode"] = "read-only"
                content = (
                    "\n".join(
                        f"{key} = {json.dumps(value, ensure_ascii=False)}"
                        for key, value in fields.items()
                    )
                    + "\n"
                )
                tomllib.loads(content)
                payload[f"{engine}/agents/{role['name']}.toml"] = content.encode(
                    "utf-8"
                )
            else:
                fields = {
                    "name": role["name"],
                    "description": role["description"],
                    "model": "inherit",
                }
                if role.get("claude_tools") is not None:
                    fields["tools"] = role["claude_tools"]
                if "claude_disallowed_tools" in role:
                    fields["disallowedTools"] = role["claude_disallowed_tools"]
                content = header(fields) + body
                payload[f"{engine}/agents/{role['name']}.md"] = content.encode("utf-8")
    return payload


def _parent_collision(root: Path, target: Path) -> Path | None:
    for parent in target.parents:
        if not parent.is_relative_to(root):
            break
        if parent.exists() and not parent.is_dir():
            return parent
    return None


def _link_collision(root: Path, name: str) -> Path | None:
    target = root / name
    for path in (target, *target.parents):
        if not path.is_relative_to(root):
            break
        if path.is_symlink():
            return path
    return None


def _manifest(root: Path, name: str) -> tuple[Path, dict]:
    if _link_collision(root, name):
        raise WorkflowError(f"Colisión en el manifiesto: {root / name}")
    path = inside(root, name)
    if _parent_collision(root, path) or (path.exists() and not path.is_file()):
        raise WorkflowError(f"Colisión en el manifiesto: {path}")
    if not path.is_file():
        return path, {"files": {}}
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as error:
        raise WorkflowError(f"Manifiesto inválido: {path}") from error
    if not isinstance(old, dict) or not isinstance(old.get("files"), dict):
        raise WorkflowError(f"Manifiesto inválido: {path}")
    for name, expected in old["files"].items():
        inside(root, name)
        if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise WorkflowError(f"Hash inválido en el manifiesto: {path}")
    return path, old


@dataclass(frozen=True)
class _Changes:
    writes: tuple[str, ...]
    removals: tuple[str, ...]


def _preflight(
    destination: Path,
    payload: dict[str, bytes],
    previous: dict[str, str],
    obsolete: set[str],
    *,
    label: str,
) -> _Changes:
    """Check every replacement and removal before either mode may write anything."""
    writes, removals, collisions, edited_obsolete = [], [], [], []
    previous_paths: dict[Path, set[str]] = {}
    for name, expected in previous.items():
        previous_paths.setdefault(destination / name, set()).add(expected)
    desired_paths = {destination / name for name in payload}
    for name, content in payload.items():
        link = _link_collision(destination, name)
        if link:
            collisions.append(str(link))
            continue
        target = inside(destination, name)
        parent = _parent_collision(destination, target)
        if parent:
            collisions.append(str(parent))
            continue
        expected = hashlib.sha256(content).hexdigest()
        if target.exists():
            if not target.is_file():
                collisions.append(str(target))
                continue
            current = digest(target)
            if current not in {expected} | previous_paths.get(target, set()):
                collisions.append(str(target))
                continue
            if current == expected:
                continue
        writes.append(name)
    for name in sorted(obsolete):
        link = _link_collision(destination, name)
        if link:
            edited_obsolete.append(str(link))
            continue
        target = inside(destination, name)
        # Windows treats a case-only rename as one path. Never remove the new file.
        if target in desired_paths:
            continue
        parent = _parent_collision(destination, target)
        if parent:
            edited_obsolete.append(str(parent))
            continue
        if target.exists():
            if not target.is_file() or digest(target) != previous[name]:
                edited_obsolete.append(str(target))
            else:
                removals.append(name)
    if collisions or edited_obsolete:
        details = []
        if collisions:
            details.append("Colisiones: " + ", ".join(sorted(set(collisions))))
        if edited_obsolete:
            details.append(
                "Archivos obsoletos editados: "
                + ", ".join(sorted(set(edited_obsolete)))
            )
        raise WorkflowError(
            f"{'; '.join(details)}; no se ha escrito ni retirado {label}."
        )
    return _Changes(tuple(sorted(writes)), tuple(removals))


def _apply(destination: Path, payload: dict[str, bytes], changes: _Changes) -> None:
    for name in changes.writes:
        target = inside(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload[name])
    for name in changes.removals:
        target = inside(destination, name)
        target.unlink()
        # Empty managed directories may go; unrelated contents always prevent rmdir.
        for parent in target.parents:
            if parent == destination:
                break
            try:
                parent.rmdir()
            except OSError:
                break


def _hashes(payload: dict[str, bytes]) -> dict[str, str]:
    return {
        name: hashlib.sha256(content).hexdigest() for name, content in payload.items()
    }


def _build_preflight(
    root: Path, destination: Path, payload: dict[str, bytes]
) -> tuple[Path, _Changes]:
    if (
        destination == root
        or root.is_relative_to(destination)
        or destination.is_relative_to(root / "skills")
        or destination.is_relative_to(root / "export")
    ):
        raise WorkflowError(
            "El destino de compilación debe ser independiente de las fuentes."
        )
    manifest_path, old = _manifest(destination, ".gara-build.json")
    changes = _preflight(
        destination,
        payload,
        old["files"],
        old["files"].keys() - payload.keys(),
        label="ningún archivo de la distribución compilada",
    )
    return manifest_path, changes


def build(root: Path, destination: Path) -> dict:
    root, destination = root.resolve(), destination.resolve()
    catalog = _catalog(root)
    _validate_catalog(root, catalog)
    payload = _distribution_payload(root, catalog)
    manifest_path, changes = _build_preflight(root, destination, payload)
    _apply(destination, payload, changes)
    hashes = _hashes(payload)
    save_json(manifest_path, {"version": catalog["version"], "files": hashes})
    return {
        "status": "built",
        "destination": str(destination),
        "files": len(payload),
        "skills_per_engine": len(catalog["skills"]),
    }


def _installed_engine(name: str) -> str | None:
    for engine, prefixes in (
        ("codex", (".agents/skills/", ".codex/agents/")),
        ("claude", (".claude/skills/", ".claude/agents/")),
    ):
        if name.startswith(prefixes):
            return engine
    return None


def _installation_payload(
    home: Path, distribution: dict[str, bytes], engines: tuple[str, ...]
) -> tuple[dict[str, bytes], list[str]]:
    payload, reused = {}, []
    legacy_commit = home / ".codex/skills/gara-commit/SKILL.md"
    for name, content in distribution.items():
        engine, kind, relative = name.split("/", 2)
        if engine not in engines:
            continue
        if (
            engine == "codex"
            and kind == "skills"
            and relative.startswith("gara-commit/")
            and legacy_commit.is_file()
        ):
            if not reused:
                reused.append(str(legacy_commit))
            continue
        prefix = (
            ".agents/skills"
            if engine == "codex" and kind == "skills"
            else f".{engine}/{kind}"
        )
        payload[f"{prefix}/{relative}"] = content
    return payload, reused


def install(root: Path, home: Path, engine: str, *, dry_run: bool = False) -> dict:
    root, home = root.resolve(), home.resolve()
    engines = ("codex", "claude") if engine == "both" else (engine,)
    if any(name not in {"codex", "claude"} for name in engines):
        raise WorkflowError("Motor de instalación inválido.")
    catalog = _catalog(root)
    _validate_catalog(root, catalog)
    distribution = _distribution_payload(root, catalog)
    destination = (root / ".build").resolve()
    build_manifest, build_changes = _build_preflight(root, destination, distribution)
    manifest_path, old = _manifest(home, ".gara-workflow/installation.json")
    payload, reused = _installation_payload(home, distribution, engines)
    if "codex" not in engines:
        reused = old.get("reused", [])
    selected = {name for name in old["files"] if _installed_engine(name) in engines}
    obsolete = selected - payload.keys()
    changes = _preflight(
        home,
        payload,
        old["files"],
        obsolete,
        label="ningún archivo de la instalación",
    )
    hashes = {
        name: value for name, value in old["files"].items() if name not in selected
    }
    hashes.update(_hashes(payload))
    result = {
        "status": "dry-run" if dry_run else "installed",
        "engines": engines,
        "home": str(home),
        "files_changed": len(changes.writes),
        "files_removed": len(changes.removals),
        "files_managed": len(hashes),
        "reused": reused,
    }
    if dry_run:
        result.update(
            skills=[row["name"] for row in catalog["skills"]],
            files=sorted(payload),
            files_to_write=list(changes.writes),
            files_to_remove=list(changes.removals),
            files_obsolete=sorted(obsolete),
        )
        return result
    # Installation preflight also finishes before the generated build is changed.
    _apply(destination, distribution, build_changes)
    save_json(
        build_manifest,
        {"version": catalog["version"], "files": _hashes(distribution)},
    )
    _apply(home, payload, changes)
    save_json(
        manifest_path,
        {
            "version": catalog["version"],
            "source": str(root),
            "files": hashes,
            "reused": reused,
        },
    )
    result["note"] = (
        "Abre una sesión nueva para cargar los nuevos directorios de agentes."
    )
    return result
