"""Artifact-driven execution, bounded recovery and independently executed gates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from .common import (
    Blocked,
    ROOT,
    WorkflowError,
    digest,
    git,
    inside,
    read_tasks,
    redact,
    repository,
    runtime_dir,
    save_json,
    specification,
    task_fingerprint,
    write_tasks,
)
from .engines import run_session, stream_process
from .reviews import (
    implementation_files,
    implementation_matches,
    read_review,
    review_instructions,
    validate_record,
)


def changes(repo: Path, base: str = "HEAD") -> set[str]:
    tracked = git(repo, "diff", "--name-only", "-z", base)
    staged = git(repo, "diff", "--cached", "--name-only", "-z", base)
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    return {
        name
        for name in (tracked + "\0" + staged + "\0" + untracked).split("\0")
        if name
    }


def file_hashes(repo: Path, paths: list[str]) -> dict[str, str | None]:
    return {
        name: digest(inside(repo, name)) if inside(repo, name).is_file() else None
        for name in paths
    }


def checkout_lock_path(repo: Path) -> Path:
    """Git resolves this private path separately for each linked worktree."""
    path = Path(git(repo, "rev-parse", "--git-path", "gara-workflow/flow.lock"))
    return (path if path.is_absolute() else repo / path).resolve()


def checkout_hashes(repo: Path, protected: set[str]) -> dict[str, tuple | None]:
    """Include ignored files and symlink targets without following external links."""
    inventory = git(repo, "ls-files", "--cached", "--others", "-z")
    staged = {}
    for entry in git(repo, "ls-files", "--stage", "-z").split("\0"):
        if entry:
            metadata, name = entry.split("\t", 1)
            staged.setdefault(name, []).append(metadata)
    names = protected | {name for name in inventory.split("\0") if name}
    snapshot = {}
    for name in names:
        path = repo / name
        try:
            info = path.lstat()
        except FileNotFoundError:
            snapshot[name] = (None, None, tuple(staged.get(name, [])))
            continue
        if stat.S_ISLNK(info.st_mode):
            content = os.readlink(path)
        elif stat.S_ISREG(info.st_mode):
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            content = hasher.hexdigest()
        else:
            content = "non-regular"
        snapshot[name] = (info.st_mode, content, tuple(staged.get(name, [])))
    return snapshot


@contextmanager
def flow_lock(path: Path):
    """OS-backed locks are released on crashes; an old file is not a stale lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise Blocked(
                "Ya existe una ejecución activa para este checkout."
            ) from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def skill_path(name: str, engine: str) -> Path:
    home = Path.home()
    candidates = [
        home
        / (".agents/skills" if engine == "codex" else ".claude/skills")
        / name
        / "SKILL.md"
    ]
    if engine == "codex":
        candidates.append(home / ".codex/skills" / name / "SKILL.md")
    candidates += [ROOT / "skills" / name / "SKILL.md", ROOT.parent / name / "SKILL.md"]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise Blocked(f"La skill {name} no está instalada ni disponible en el paquete.")


class Runner:
    def __init__(
        self,
        repo: Path,
        slug: str,
        engine: str,
        *,
        config: dict | None = None,
        client: str | None = None,
        timeout: float = 3600,
        retry_infra: int = 1,
    ):
        self.repo = repository(repo)
        self.slug, self.engine = slug, engine
        self.artifacts = inside(self.repo, f"specs/{slug}")
        self.runtime = runtime_dir(self.repo, slug)
        self.lock_path = checkout_lock_path(self.repo)
        self.state_path = self.runtime / "state.json"
        self.spec = self.artifacts / "SPEC.md"
        self.plan = self.artifacts / "PLAN.md"
        self.tasks_path = self.artifacts / "TAREAS.md"
        self.config, self.client = config or {}, client
        self.timeout, self.retry_infra = timeout, retry_infra
        self.state: dict = {}
        self.issue, self.requirements = "", set()

    def preflight(self) -> None:
        self.issue, self.requirements = specification(self.spec)
        branch = git(self.repo, "branch", "--show-current")
        default = git(
            self.repo,
            "symbolic-ref",
            "--short",
            "refs/remotes/origin/HEAD",
            check=False,
        ).split("/")[-1]
        if not branch or branch in {"main", "master", default}:
            raise Blocked(
                "Ejecuta el flujo en la rama del issue, no en la rama principal ni en HEAD separado."
            )
        if not re.search(
            rf"(?<![a-z0-9]){re.escape(self.issue)}(?![a-z0-9])", branch, re.I
        ):
            raise Blocked("La rama debe corresponder al issue GAR-N de la SPEC.")
        if self.state_path.is_file():
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if (
                self.state.get("repo") != str(self.repo)
                or self.state.get("branch") != branch
                or self.state.get("issue") != self.issue
                or self.state.get("engine") != self.engine
            ):
                raise Blocked(
                    "La identidad de la ejecución no coincide con el checkout, issue o motor."
                )
            if self.state.get("spec_hash") != digest(self.spec):
                raise Blocked(
                    "Cambió la SPEC autorizada. Prepara una spec nueva antes de reutilizar la ejecución."
                )
            if self.state.get("plan_hash") and (
                not self.plan.is_file() or self.state["plan_hash"] != digest(self.plan)
            ):
                raise Blocked(
                    "Cambió el PLAN cerrado. No se reutilizan sus tareas automáticamente."
                )
            recorded = self.state.get("head")
            process = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repo),
                    "merge-base",
                    "--is-ancestor",
                    recorded,
                    "HEAD",
                ],
                capture_output=True,
            )
            if process.returncode:
                raise Blocked(
                    "HEAD ya no desciende del último commit registrado; reconcilia la rama."
                )
        else:
            foreign = changes(self.repo) - self.artifact_names()
            if foreign:
                raise Blocked(
                    "Hay cambios previos fuera de los artefactos: "
                    + ", ".join(sorted(foreign))
                )
            self.state = {
                "version": 1,
                "repo": str(self.repo),
                "branch": branch,
                "issue": self.issue,
                "slug": self.slug,
                "engine": self.engine,
                "base_head": git(self.repo, "rev-parse", "HEAD"),
                "head": git(self.repo, "rev-parse", "HEAD"),
                "spec_hash": digest(self.spec),
                "completed_phases": [],
                "status": "ready",
                "sequence": 0,
                "verified_files": {},
                "acknowledged_checkpoints": [],
            }
        if self.tasks_path.is_file():
            data = read_tasks(self.tasks_path, self.repo, self.issue, self.requirements)
            if self.artifact_names() & {
                name for task in data["tasks"] for name in task["files"]
            }:
                raise Blocked(
                    "Los artefactos del flujo no pueden ser archivos de implementación asignados."
                )
            if self.state.get("tasks_hash") and self.state[
                "tasks_hash"
            ] != task_fingerprint(data):
                raise Blocked(
                    "Cambió el contrato de tareas. No se reutiliza el horario anterior."
                )
            allowed = self.artifact_names() | {
                name for task in data["tasks"] for name in task["files"]
            }
            foreign = changes(self.repo, self.state["base_head"]) - allowed
            if foreign:
                raise Blocked(
                    "Cambios fuera del alcance de esta ejecución: "
                    + ", ".join(sorted(foreign))
                )

    def artifact_names(self) -> set[str]:
        return {
            f"specs/{self.slug}/{name}"
            for name in ("SPEC.md", "PLAN.md", "TAREAS.md", "REVISION.md", "ENTREGA.md")
        }

    def save(self, status: str | None = None, reason: str = "") -> None:
        if status:
            self.state["status"] = status
        self.state.update(
            head=git(self.repo, "rev-parse", "HEAD"),
            updated_at=time.time(),
            reason=redact(reason),
        )
        save_json(self.state_path, self.state)

    def prompt(self, phase: str, detail: str) -> str:
        names = {
            "commit": "gara-commit",
            "review": "gara-review",
            "publish": "gara-deliver",
        }
        skill = skill_path(names.get(phase, "gara-" + phase), self.engine)
        return f"""Trabaja únicamente en el checkout Gara {self.repo}.
Lee y aplica exactamente la skill {skill}. Fase: {phase}; issue: {self.issue}; slug: {self.slug}.
Los artefactos están en {self.artifacts}.
La invocación run autoriza implementar la SPEC existente.
Lee las instrucciones del checkout y comprueba .ai/state.json contra HEAD. Conserva cambios previos.
Respeta el modo y los permisos reales del entorno. Usa subagentes nativos si están disponibles y
permitidos, hasta tres trabajadores por tanda; de lo contrario trabaja secuencialmente y decláralo.
No invoques otro CLI de agentes ni cambies modelos o configuración global. Una revisión de agentes
no sustituye la revisión humana exigida por Gara. Para implementar comprueba asignación del issue
y criterios vigentes mediante las capacidades disponibles; si no puedes acreditarlos, bloquea.
No envíes trabajos HPC, despliegues, publiques ni modifiques Linear salvo una fase publish explícita.
Si falta una decisión material o un permiso, registra el bloqueo; no inventes una autorización.
No incluyas credenciales, tokens o contenido de .env en salidas ni artefactos.
{detail}
Finaliza con esta marca y JSON de una sola línea, fuera de un bloque de código:
<!-- gara-result --> {{"status":"completed|blocked|failed","summary":"resultado y evidencias"}}
Elige un único valor real para status. Un mensaje sin esta marca bloquea el ejecutor.
"""

    def invalidate_reviews(self) -> None:
        self.state["completed_phases"][:] = [
            phase
            for phase in self.state["completed_phases"]
            if phase not in {"verify", "review", "publish"}
        ]
        self.state.pop("publication_sha", None)
        self.state.pop("delivery_hash", None)

    def check_saved_delivery(self) -> None:
        if "publish" not in self.state["completed_phases"]:
            return
        delivery = self.artifacts / "ENTREGA.md"
        sha = self.state["reviews"]["review"]["record"]["implementation_sha"]
        if (
            self.state.get("publication_sha") != sha
            or not delivery.is_file()
            or self.state.get("delivery_hash") != digest(delivery)
            or not re_delivery(delivery.read_text(encoding="utf-8"), sha)
        ):
            self.state["completed_phases"].remove("publish")
            self.state.pop("publication_sha", None)
            self.state.pop("delivery_hash", None)
            raise Blocked(
                "Cambió la entrega cerrada; reanuda publish para acreditarla."
            )

    def protect_publication(self, head: str, before: dict) -> None:
        delivery = f"specs/{self.slug}/ENTREGA.md"
        after = checkout_hashes(self.repo, self.artifact_names() | set(before))
        unexpected = {
            name
            for name in before.keys() | after.keys()
            if name != delivery and before.get(name) != after.get(name)
        }
        current = git(self.repo, "rev-parse", "HEAD")
        ancestor = subprocess.run(
            ["git", "-C", str(self.repo), "merge-base", "--is-ancestor", head, current],
            capture_output=True,
        )
        if ancestor.returncode:
            self.invalidate_reviews()
            raise Blocked(
                "La entrega cambió el historial validado; vuelve a verificar."
            )
        # Inspect every new commit, including changes undone by a later commit.
        for commit in git(self.repo, "rev-list", f"{head}..{current}").splitlines():
            committed = git(
                self.repo,
                "diff-tree",
                "--root",
                "-m",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                commit,
            )
            unexpected.update(
                name for name in committed.split("\0") if name and name != delivery
            )
        if unexpected:
            self.invalidate_reviews()
            raise Blocked(
                "La entrega modificó archivos cerrados; solo puede escribir ENTREGA.md: "
                + ", ".join(sorted(unexpected))
            )

    def phase(
        self, phase: str, detail: str, allowed: set[str], *, resume_id: str = ""
    ) -> None:
        before_head = git(self.repo, "rev-parse", "HEAD")
        before = file_hashes(self.repo, sorted(changes(self.repo)))
        publication_before = None
        if phase == "publish":
            allowed = {f"specs/{self.slug}/ENTREGA.md"}
            publication_before = checkout_hashes(self.repo, self.artifact_names())
        for attempt in range(self.retry_infra + 1):
            self.state["sequence"] += 1
            sequence = self.state["sequence"]
            self.save("running")
            print(f"{phase}: sesión {sequence}", flush=True)
            log = self.runtime / f"{sequence:04d}-{phase}.json"
            try:
                result = run_session(
                    self.engine,
                    self.prompt(phase, detail),
                    self.repo,
                    log,
                    timeout=self.timeout,
                    client=self.client,
                    config=self.config.get(self.engine, {}),
                    resume_id=resume_id,
                )
            except BaseException:
                if publication_before is not None:
                    self.protect_publication(before_head, publication_before)
                raise
            self.state["last_session"] = {"id": result.session_id, "phase": phase}
            self.state.setdefault("sessions", []).append(
                {
                    "phase": phase,
                    "log": log.name,
                    "id": result.session_id,
                    "status": result.status,
                    "usage": result.usage,
                    "delegations": getattr(result, "delegations", []),
                }
            )
            if publication_before is not None:
                self.protect_publication(before_head, publication_before)
            if git(self.repo, "branch", "--show-current") != self.state["branch"]:
                raise Blocked("La sesión cambió la rama de trabajo.")
            if digest(self.spec) != self.state["spec_hash"]:
                raise Blocked("La sesión modificó la SPEC autorizada.")
            if (
                self.state.get("plan_hash")
                and digest(self.plan) != self.state["plan_hash"]
            ):
                raise Blocked("La sesión modificó el PLAN cerrado.")
            unexpected = changes(self.repo, before_head) - allowed
            unexpected = {
                name
                for name in unexpected
                if file_hashes(self.repo, [name])[name] != before.get(name, "absent")
            }
            if unexpected:
                raise Blocked(
                    "La sesión modificó archivos no asignados: "
                    + ", ".join(sorted(unexpected))
                )
            if result.status == "completed":
                self.save()
                return
            if result.infrastructure and attempt < self.retry_infra:
                current = file_hashes(self.repo, sorted(changes(self.repo)))
                if (
                    current == before
                    and git(self.repo, "rev-parse", "HEAD") == before_head
                ):
                    continue
                raise Blocked(
                    "Falló la infraestructura después de modificar el checkout; reconcilia antes de repetir."
                )
            if result.status == "blocked":
                raise Blocked(result.summary)
            raise WorkflowError(result.summary)

    def gates(self, tasks: list[dict]) -> None:
        before_head = git(self.repo, "rev-parse", "HEAD")
        before = file_hashes(self.repo, sorted(changes(self.repo)))
        contract = read_tasks(self.tasks_path, self.repo, self.issue, self.requirements)
        allowed = self.artifact_names() | {
            name for task in contract["tasks"] for name in task["files"]
        }
        for task in tasks:
            evidence = []
            for number, gate in enumerate(task["acceptance"], 1):
                cwd = inside(self.repo, gate.get("cwd", "."))
                if not cwd.is_dir():
                    raise Blocked(
                        f"No existe el directorio de validación de {task['id']}."
                    )
                print(f"{task['id']}: validación {number}", flush=True)
                code, lines, stderr = stream_process(
                    gate["argv"], cwd, timeout=gate.get("timeout", 600)
                )
                record = {
                    "argv": gate["argv"],
                    "cwd": gate.get("cwd", "."),
                    "returncode": code,
                    "stdout": redact("\n".join(lines)[-10000:]),
                    "stderr": redact(stderr),
                    "time": time.time(),
                }
                evidence.append(record)
                task["evidence"] = evidence
                unexpected = changes(self.repo, before_head) - allowed
                unexpected = {
                    name
                    for name in unexpected
                    if file_hashes(self.repo, [name])[name]
                    != before.get(name, "absent")
                }
                if unexpected or git(self.repo, "rev-parse", "HEAD") != before_head:
                    raise Blocked(
                        "Un comando de aceptación modificó el historial o archivos fuera del contrato."
                    )
                if (
                    digest(self.spec) != self.state["spec_hash"]
                    or digest(self.plan) != self.state["plan_hash"]
                ):
                    raise Blocked(
                        "Un comando de aceptación modificó SPEC.md o PLAN.md."
                    )
                if (
                    task_fingerprint(
                        read_tasks(
                            self.tasks_path, self.repo, self.issue, self.requirements
                        )
                    )
                    != self.state["tasks_hash"]
                ):
                    raise Blocked(
                        "Un comando de aceptación modificó el contrato de tareas."
                    )
                if code:
                    task["status"] = "blocked"
                    raise WorkflowError(
                        f"Falló la aceptación de {task['id']}: {redact(stderr or record['stdout'])}"
                    )
            task["status"] = "verified"
            self.state["verified_files"][task["id"]] = file_hashes(
                self.repo, task["files"]
            )

    def commit(self, detail: str, allowed: set[str]) -> None:
        """A provider success message cannot replace an observed clean commit."""
        data = read_tasks(self.tasks_path, self.repo, self.issue, self.requirements)
        files = {name for task in data["tasks"] for name in task["files"]}
        before = file_hashes(self.repo, sorted(files))
        self.phase("commit", detail, allowed)
        if before != file_hashes(self.repo, sorted(files)):
            raise Blocked("La fase de commit modificó implementación ya validada.")
        if (
            task_fingerprint(
                read_tasks(self.tasks_path, self.repo, self.issue, self.requirements)
            )
            != self.state["tasks_hash"]
        ):
            raise Blocked("La fase de commit modificó el contrato de tareas.")
        if changes(self.repo) & allowed:
            raise Blocked("La fase de commit dejó cambios autorizados sin registrar.")

    def build(self, data: dict, acknowledge: bool) -> None:
        by_id = {task["id"]: task for task in data["tasks"]}
        if self.state.get("checkpoint"):
            if not acknowledge:
                raise Blocked(
                    f"Checkpoint {self.state['checkpoint']}: reanuda con --ack-checkpoint tras revisarlo."
                )
            self.state["acknowledged_checkpoints"].append(self.state.pop("checkpoint"))
        for task in data["tasks"]:
            known = self.state["verified_files"].get(task["id"])
            if task["status"] == "verified" and (
                not known or known != file_hashes(self.repo, task["files"])
            ):
                task["status"] = "running" if known else "pending"
                if "build" in self.state["completed_phases"]:
                    self.state["completed_phases"].remove("build")
                self.invalidate_reviews()
                self.state["committed_batches"] = []
        write_tasks(self.tasks_path, data)
        committed = self.state.setdefault("committed_batches", [])
        for batch in data["batches"]:
            checkpoint = ",".join(batch)
            selected = [
                by_id[name] for name in batch if by_id[name]["status"] != "verified"
            ]
            if selected:
                self.invalidate_reviews()
            if not selected and checkpoint in committed:
                if (
                    any(by_id[name].get("checkpoint") for name in batch)
                    and checkpoint not in self.state["acknowledged_checkpoints"]
                ):
                    self.state["checkpoint"] = checkpoint
                    raise Blocked(
                        f"Checkpoint {checkpoint}: reanuda con --ack-checkpoint tras revisarlo."
                    )
                continue
            # Interrupted code can already satisfy acceptance. Validate before rerunning its author.
            recovery = [task for task in selected if task["status"] == "running"]
            for task in recovery:
                try:
                    self.gates([task])
                except Blocked:
                    raise
                except WorkflowError:
                    task["status"] = "pending"
            selected = [task for task in selected if task["status"] != "verified"]
            if selected:
                for task in selected:
                    task["status"] = "running"
                write_tasks(self.tasks_path, data)
                allowed = {f"specs/{self.slug}/TAREAS.md"} | {
                    name for task in selected for name in task["files"]
                }
                detail = (
                    "Implementa únicamente esta tanda: "
                    + json.dumps(selected, ensure_ascii=False)
                    + "\nEl ejecutor ejecutará la aceptación y escribirá los estados. No marques verificado ni crees commits todavía."
                )
                self.phase("build", detail, allowed)
                current = read_tasks(
                    self.tasks_path, self.repo, self.issue, self.requirements
                )
                if task_fingerprint(current) != self.state["tasks_hash"]:
                    raise Blocked(
                        "La construcción cambió el briefing, los archivos o la aceptación de las tareas."
                    )
                try:
                    self.gates(selected)
                finally:
                    write_tasks(self.tasks_path, data)
            write_tasks(self.tasks_path, data)
            allowed = self.artifact_names() | {
                name for task in data["tasks"] for name in task["files"]
            }
            self.save()
            self.commit(
                "Prepara commits atómicos solo para los cambios autorizados de esta tanda y los artefactos del flujo. "
                "Usa el validador gara-commit; corrige un rechazo, nunca lo eludas. Conserva el staging ajeno.",
                allowed,
            )
            if checkpoint not in committed:
                committed.append(checkpoint)
            self.save()
            if (
                any(by_id[name].get("checkpoint") for name in batch)
                and checkpoint not in self.state["acknowledged_checkpoints"]
            ):
                self.state["checkpoint"] = checkpoint
                raise Blocked(
                    f"Checkpoint {checkpoint}: revisión humana pendiente. Reanuda con --ack-checkpoint."
                )
        if "build" not in self.state["completed_phases"]:
            self.state["completed_phases"].append("build")
        self.save()

    def check_saved_reviews(self, data: dict) -> None:
        saved = self.state.get("reviews", {})
        closed = {
            phase
            for phase in ("verify", "review")
            if phase in self.state["completed_phases"]
        }
        if closed - saved.keys():
            # Older state files only recorded existence of REVISION.md.
            self.invalidate_reviews()
            return
        if not closed:
            return
        try:
            report = read_review(self.artifacts / "REVISION.md", self.issue)
            for phase in closed:
                record = validate_record(
                    report, phase, self.repo, self.requirements, data["tasks"]
                )
                if record != saved[phase]["record"]:
                    raise Blocked("Cambió la evidencia de una revisión cerrada.")
        except Blocked:
            self.invalidate_reviews()
            raise

    def reviews(self, data: dict, allowed: set[str], resume_last: bool) -> None:
        self.check_saved_reviews(data)
        revision = self.artifacts / "REVISION.md"
        # A correction in review needs one bounded fresh verification and review.
        for repetition in range(2):
            repeat = False
            for phase in ("verify", "review"):
                if phase in self.state["completed_phases"]:
                    continue
                previous_verification = (
                    read_review(revision, self.issue)["verification"]
                    if phase == "review"
                    else None
                )
                previous_session = self.state.get("last_session", {})
                resume_id = (
                    previous_session.get("id", "")
                    if resume_last and previous_session.get("phase") == phase
                    else ""
                )
                self.phase(
                    phase,
                    "Revisa contra la SPEC, el PLAN y las pruebas. Trabaja con contexto fresco; "
                    "corrige solo fallos del alcance. Para correcciones usa gara-commit después "
                    "de validar, antes de asociar el informe al SHA; no publiques. "
                    + review_instructions(phase),
                    allowed,
                    resume_id=resume_id,
                )
                session = self.state["sessions"][-1]
                fresh = read_tasks(
                    self.tasks_path, self.repo, self.issue, self.requirements
                )
                if task_fingerprint(fresh) != self.state["tasks_hash"]:
                    raise Blocked("La revisión cambió el contrato cerrado de tareas.")
                try:
                    self.gates(data["tasks"])
                finally:
                    write_tasks(self.tasks_path, data)
                report = read_review(revision, self.issue)
                changed = False
                if phase == "review":
                    if report["verification"] != previous_verification:
                        self.invalidate_reviews()
                        raise Blocked(
                            "La revisión sobrescribió la evidencia de verificación."
                        )
                    validate_record(
                        report,
                        "verify",
                        self.repo,
                        self.requirements,
                        data["tasks"],
                        current_implementation=False,
                    )
                    changed = not implementation_matches(
                        self.repo,
                        previous_verification["implementation_sha"],
                        implementation_files(data["tasks"]),
                    )
                    if changed:
                        self.invalidate_reviews()
                record = validate_record(
                    report, phase, self.repo, self.requirements, data["tasks"]
                )
                closed_hash = digest(revision)
                self.save()
                self.commit(
                    "Registra los cambios y la evidencia de revisión con gara-commit. "
                    "Conserva exactamente REVISION.md ya validado. Si no hay cambios, informa "
                    "de ello; nunca generes un commit vacío.",
                    allowed,
                )
                if digest(revision) != closed_hash:
                    raise Blocked(
                        "La fase de commit cambió la evidencia de revisión cerrada."
                    )
                validate_record(
                    report, phase, self.repo, self.requirements, data["tasks"]
                )
                self.state.setdefault("reviews", {})[phase] = {
                    "record": record,
                    "provider_session_id": session["id"],
                    "delegations": session["delegations"],
                    "independence": "unverified",
                }
                if changed:
                    self.invalidate_reviews()
                    self.save()
                    if repetition:
                        raise Blocked(
                            "La revisión volvió a corregir código tras el repaso; reanuda "
                            "para verificar y revisar la nueva implementación."
                        )
                    repeat = True
                    break
                self.state["completed_phases"].append(phase)
                self.save()
            if not repeat:
                return

    def run(
        self,
        *,
        dry_run: bool = False,
        publish: bool = False,
        acknowledge: bool = False,
        resume_last: bool = False,
    ) -> dict:
        self.preflight()
        plan = {
            "repo": str(self.repo),
            "issue": self.issue,
            "slug": self.slug,
            "engine": self.engine,
            "phases": ["plan", "tasks", "build", "verify", "review"]
            + (["publish"] if publish else []),
            "runtime": str(self.runtime),
            "completed": self.state["completed_phases"],
        }
        if dry_run:
            for name in (
                "gara-plan",
                "gara-tasks",
                "gara-build",
                "gara-verify",
                "gara-review",
                "gara-commit",
            ):
                skill_path(name, self.engine)
            return {"status": "dry-run", **plan}
        with flow_lock(self.lock_path):
            # Check again under the lock, so a concurrent process cannot overwrite fresh state.
            self.preflight()
            try:
                self.save("running")
                for phase, path in (("plan", self.plan), ("tasks", self.tasks_path)):
                    if phase not in self.state["completed_phases"]:
                        self.phase(
                            phase,
                            f"Escribe {path.name} con el contrato documentado de gara-workflow. "
                            "No implementes código en esta fase.",
                            self.artifact_names(),
                        )
                        if not path.is_file() or path.stat().st_size == 0:
                            raise Blocked(f"La fase {phase} no produjo su artefacto.")
                        if "\n## Bloqueado" in path.read_text(encoding="utf-8"):
                            raise Blocked(f"{path.name} contiene un bloqueo pendiente.")
                        if phase == "plan":
                            self.state["plan_hash"] = digest(path)
                        else:
                            data = read_tasks(
                                path, self.repo, self.issue, self.requirements
                            )
                            self.state["tasks_hash"] = task_fingerprint(data)
                        self.state["completed_phases"].append(phase)
                        self.save()
                data = read_tasks(
                    self.tasks_path, self.repo, self.issue, self.requirements
                )
                self.build(data, acknowledge)
                allowed = self.artifact_names() | {
                    name for task in data["tasks"] for name in task["files"]
                }
                self.reviews(data, allowed, resume_last)
                self.check_saved_delivery()
                if publish and "publish" not in self.state["completed_phases"]:
                    report = read_review(self.artifacts / "REVISION.md", self.issue)
                    reviewed = validate_record(
                        report, "review", self.repo, self.requirements, data["tasks"]
                    )
                    implementation_sha = reviewed["implementation_sha"]
                    self.phase(
                        "publish",
                        "El usuario eligió --publish: comprueba autorización y estado del issue, "
                        "publica esta rama, abre o reutiliza su PR y entrega el trabajo en In Review. "
                        "Escribe únicamente ENTREGA.md con URL de PR, SHA y estado observado del issue. "
                        f"Incluye la línea Implementation SHA: {implementation_sha}. "
                        "La implementación y SPEC, PLAN, TAREAS y REVISION están cerrados; "
                        "si necesitan cambios, bloquea y vuelve a construcción/verificación. "
                        "No hagas merge ni te autoapruebes; sigue las excepciones solo si hay instrucción explícita vigente.",
                        {f"specs/{self.slug}/ENTREGA.md"},
                    )
                    delivery = self.artifacts / "ENTREGA.md"
                    if not delivery.is_file() or not re_delivery(
                        delivery.read_text(encoding="utf-8"), implementation_sha
                    ):
                        raise Blocked(
                            "La entrega no contiene URL de PR, In Review y el SHA de implementación revisado."
                        )
                    self.state["publication_sha"] = implementation_sha
                    self.state["delivery_hash"] = digest(delivery)
                    self.state["completed_phases"].append("publish")
                self.save("completed")
                return {
                    "status": "completed",
                    **plan,
                    "completed": list(self.state["completed_phases"]),
                    "head": self.state["head"],
                }
            except Blocked as error:
                self.save("blocked", str(error))
                raise
            except (WorkflowError, OSError, KeyboardInterrupt) as error:
                self.save(
                    "failed",
                    str(error) or "Interrumpido; reconcilia antes de reanudar.",
                )
                raise


def re_delivery(text: str, implementation_sha: str = "") -> bool:
    return bool(
        re.search(r"https://github\.com/[^\s/]+/gara/pull/[0-9]+", text)
        and "In Review" in text
        and (
            not implementation_sha
            or re.search(
                rf"^Implementation SHA:\s*`?{re.escape(implementation_sha)}`?\s*$",
                text,
                re.M | re.I,
            )
        )
    )
