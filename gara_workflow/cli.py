"""Command-line interface; installation and diagnostics are available outside Gara."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import signal
import subprocess
import sys
import threading
import time
import tomllib
from contextlib import contextmanager
from pathlib import Path

from .common import (
    Blocked,
    ROOT,
    WorkflowError,
    git,
    redact,
    repository,
    runtime_dir,
)


def configuration(path: str | None) -> dict:
    if path:
        with Path(path).open("rb") as source:
            return tomllib.load(source)
    return {}


def doctor(repo: Path | None, config: dict) -> dict:
    from .common import resolve_command

    engines = {}
    for engine in ("codex", "claude"):
        try:
            command = resolve_command(
                [config.get(engine, {}).get("client", engine), "--version"], Path.cwd()
            )
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            engines[engine] = {
                "available": process.returncode == 0,
                "version": redact(process.stdout.strip()),
                "command": command[:-1],
            }
        except (WorkflowError, OSError, subprocess.TimeoutExpired) as error:
            engines[engine] = {"available": False, "reason": str(error)}
    optional = {
        name: bool(importlib.util.find_spec(module))
        for name, module in (
            ("video_tracking", "cv2"),
            ("curve_fitting", "scipy"),
            ("yaml_validation", "yaml"),
        )
    }
    optional["ffmpeg"] = bool(shutil.which("ffmpeg"))
    from .pdf import find_browser

    optional["pdf_browser"] = str(
        find_browser(config.get("pdf", {}).get("browser")) or ""
    )
    data = {
        "python": sys.version.split()[0],
        "git": bool(shutil.which("git")),
        "engines": engines,
        "optional": optional,
        "authentication": "Se verifica al utilizar cada cliente; no se leen ni copian credenciales.",
    }
    if repo:
        root = repository(repo)
        manifests = {}
        manifest = root / "frontend/package.json"
        if manifest.is_file():
            manifests["frontend"] = json.loads(
                manifest.read_text(encoding="utf-8")
            ).get("scripts", {})
        manifests["backend"] = str(root / "python/pyproject.toml")
        manifests["ci"] = str(root / ".github/workflows/ci.yml")
        data.update(
            repo=str(root), head=git(root, "rev-parse", "HEAD"), manifests=manifests
        )
    return data


def metrics(directory: Path) -> dict:
    rows = []
    for path in sorted(directory.glob("[0-9]*-*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(row, dict) and "status" in row:
            rows.append({"log": path.name, **row})
    totals = {}
    for row in rows:
        for name, value in row.get("usage", {}).items():
            if isinstance(value, (int, float)):
                totals[name] = totals.get(name, 0) + value
    return {
        "sessions": len(rows),
        "statuses": {
            status: sum(row["status"] == status for row in rows)
            for status in ("completed", "blocked", "failed")
        },
        "usage": totals,
        "source": str(directory),
    }


@contextmanager
def terminate_as_interrupt():
    """Turn SIGTERM/SIGHUP/SIGBREAK into KeyboardInterrupt so state is saved and the
    client process group is stopped, exactly as for Ctrl+C."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def handler(signum, frame):
        raise KeyboardInterrupt

    previous = {}
    for name in ("SIGTERM", "SIGHUP", "SIGBREAK"):
        number = getattr(signal, name, None)
        if number is not None:
            try:
                previous[number] = signal.signal(number, handler)
            except (ValueError, OSError):
                pass
    try:
        yield
    finally:
        for number, old in previous.items():
            signal.signal(number, old)


def main(argv: list[str] | None = None) -> int:
    with terminate_as_interrupt():
        return _main(argv)


def _main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Skills y flujo verificable para Gara."
    )
    parser.add_argument(
        "command",
        choices=(
            "doctor",
            "run",
            "resume",
            "status",
            "watch",
            "metrics",
            "reset",
            "fixes",
            "sessions",
            "install",
            "validate",
            "package",
        ),
    )
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--slug")
    parser.add_argument(
        "--engine", choices=("codex", "claude", "both"), default="codex"
    )
    parser.add_argument("--config")
    parser.add_argument(
        "--client",
        help="Ejecutable nativo o script Python del cliente; útil para pruebas aisladas.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--ack-checkpoint", action="store_true")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma reset: borra el estado privado de la ejecución.",
    )
    parser.add_argument(
        "--resume-session",
        action="store_true",
        help="Reutilizar la última sesión solo si su fase permite reanudación.",
    )
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--retry-infra", type=int, default=1)
    parser.add_argument(
        "--home", type=Path, help="Home de instalación; por defecto, el usuario actual."
    )
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--host", help="Host SSH explícito para watch.")
    parser.add_argument(
        "--remote-state", help="Archivo JSON remoto de estado para watch."
    )
    args = parser.parse_args(argv)
    try:
        config = configuration(args.config)
        if args.timeout <= 0 or args.retry_infra < 0 or args.interval <= 0:
            raise WorkflowError("Timeout, intervalo o número de reintentos inválidos.")
        if args.command == "doctor":
            result = doctor(args.repo, config)
        elif args.command in {"install", "package", "validate"}:
            from .packaging import build, install, validate

            if args.command == "validate":
                result = validate(ROOT)
            elif args.command == "package":
                result = build(ROOT, args.destination or ROOT / ".build")
            else:
                result = install(
                    ROOT, args.home or Path.home(), args.engine, dry_run=args.dry_run
                )
        else:
            if args.command == "watch" and args.host:
                if not args.remote_state:
                    raise WorkflowError("watch --host necesita --remote-state.")
                from .utilities import watch_remote

                result = watch_remote(
                    args.host, args.remote_state, args.follow, args.interval
                )
            else:
                repo = repository(args.repo or Path.cwd())
                if args.command == "fixes":
                    from .utilities import fixes

                    result = fixes(repo, args.destination)
                elif args.command == "sessions":
                    from .utilities import sessions

                    result = sessions(repo)
                else:
                    if not args.slug:
                        raise WorkflowError("Este comando requiere --slug.")
                    if args.command in {"run", "resume"}:
                        if args.engine == "both":
                            raise WorkflowError(
                                "Cada ejecución elige un motor; both es para instalar."
                            )
                        from .runner import Runner

                        runner = Runner(
                            repo,
                            args.slug,
                            args.engine,
                            config=config,
                            client=args.client,
                            timeout=args.timeout,
                            retry_infra=args.retry_infra,
                        )
                        if args.command == "resume" and not runner.state_path.is_file():
                            raise Blocked(
                                "No existe una ejecución previa que reanudar."
                            )
                        result = runner.run(
                            dry_run=args.dry_run,
                            publish=args.publish,
                            acknowledge=args.ack_checkpoint,
                            resume_last=args.resume_session,
                        )
                    elif args.command == "reset":
                        from .runner import checkout_lock_path, flow_lock

                        if not args.yes:
                            raise Blocked(
                                "reset borra el estado privado de la ejecución (no toca specs/); "
                                "repite con --yes tras reconciliar el checkout."
                            )
                        target = runtime_dir(repo, args.slug)
                        with flow_lock(checkout_lock_path(repo)):
                            existed = target.is_dir()
                            if existed:
                                shutil.rmtree(target)
                        result = {
                            "status": "reset",
                            "slug": args.slug,
                            "removed": existed,
                        }
                    elif args.command == "metrics":
                        result = metrics(runtime_dir(repo, args.slug))
                    else:
                        path = runtime_dir(repo, args.slug) / "state.json"
                        if not path.is_file():
                            raise Blocked("No existe un estado de ejecución.")
                        while True:
                            result = json.loads(path.read_text(encoding="utf-8"))
                            if (
                                args.command != "watch"
                                or not args.follow
                                or result.get("status")
                                in {"completed", "blocked", "failed"}
                            ):
                                break
                            print(json.dumps(result, ensure_ascii=False), flush=True)
                            time.sleep(args.interval)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Blocked as error:
        print(
            json.dumps(
                {"status": "blocked", "reason": redact(str(error))}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        return 2
    except (
        WorkflowError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {"status": "failed", "reason": redact(str(error))}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print(
            "Interrumpido; el estado permite reconciliar y reanudar.", file=sys.stderr
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
