#!/usr/bin/env python3
"""Create policy-compliant commits only inside the Gara repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


TYPES = ("feat", "fix", "refactor", "perf", "test", "style", "docs", "build", "ci", "chore")
CODE_TYPES = {"feat", "fix", "refactor", "perf"}
DOC_NAMES = {"readme.md", "readme", "architecture.md", "api.md"}
STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less", ".styl"}
CODE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".java", ".go", ".rs"}
BUILD_NAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "vite.config.js",
    "vite.config.ts",
    "webpack.config.js",
    "tsconfig.json",
}
MAINTENANCE_NAMES = {".gitignore", ".gitattributes", ".editorconfig", ".prettierignore"}
ENV_PATTERN = re.compile(
    r"(?:process\.env\.|import\.meta\.env\.|VITE_[A-Z0-9_]+|CESGA_[A-Z0-9_]+|"
    r"ALPHAFOLD_COMMAND|MAX_OUTPUT_FILE_BYTES|USE_MOCK)"
)
API_PATTERN = re.compile(
    r"(?:\b(?:router|app)\.(?:get|post|put|patch|delete|use)\s*\(|"
    r"\bfetch\s*\(|\baxios\.(?:get|post|put|patch|delete)\s*\(|"
    r"\bexport\s+(?:default\s+)?(?:async\s+)?(?:function|class|const)\b)"
)
ARCHITECTURE_PATH_PATTERN = re.compile(
    r"(?:^|/)(?:routes|services|config|api|store|src/components)(?:/|$)"
)


class PolicyError(Exception):
    """Raised when staged changes do not satisfy the commit policy."""


@dataclass(frozen=True)
class StagedChange:
    path: str
    category: str


@dataclass(frozen=True)
class Analysis:
    changes: tuple[StagedChange, ...]
    documentation_paths: tuple[str, ...]
    documentation_reasons: tuple[str, ...]
    inferred_type: str | None


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if check and process.returncode != 0:
        message = process.stderr.strip() or process.stdout.strip() or "git devolvio un error."
        raise PolicyError(message)
    return process


def repository_root(location: Path) -> Path:
    process = git(location, "rev-parse", "--show-toplevel", check=False)
    if process.returncode != 0:
        raise PolicyError("El comando debe ejecutarse dentro de un repositorio Git.")
    root = Path(process.stdout.strip()).resolve()
    origin = git(root, "config", "--get", "remote.origin.url", check=False).stdout.strip().lower()
    origin_is_gara = bool(re.search(r"(?:/|:|\\)gara(?:\.git)?/?$", origin))
    if root.name.lower() != "gara" and not origin_is_gara:
        raise PolicyError("Este comando solo puede ejecutarse dentro del repositorio 'gara'.")
    return root


def cached_paths(root: Path, diff_filter: str = "ACDMRTUXB") -> list[str]:
    output = git(root, "diff", "--cached", "--name-only", "-z", f"--diff-filter={diff_filter}").stdout
    return [path.replace("\\", "/") for path in output.split("\0") if path]


def staged_paths(root: Path) -> list[str]:
    paths = cached_paths(root)
    if not paths:
        raise PolicyError("No hay archivos en staging; indexe una unidad logica antes de commitear.")
    return paths


def is_documentation(path: str) -> bool:
    lower = path.lower()
    name = Path(lower).name
    return (
        name in DOC_NAMES
        or name.startswith("readme.")
        or Path(lower).suffix == ".md"
        or "/docs/" in f"/{lower}/"
    )


def classify_path(path: str) -> str:
    lower = path.lower()
    name = Path(lower).name
    suffix = Path(lower).suffix
    if is_documentation(path):
        return "docs"
    if lower.startswith(".github/") or name.startswith("dockerfile") or name in {"docker-compose.yml", "docker-compose.yaml", ".gitlab-ci.yml"}:
        return "ci"
    if name in BUILD_NAMES:
        return "build"
    if name in MAINTENANCE_NAMES:
        return "chore"
    if "/test/" in f"/{lower}/" or ".test." in name or ".spec." in name:
        return "test"
    if suffix in STYLE_EXTENSIONS:
        return "style"
    return "code"


def added_or_removed_diff(root: Path) -> str:
    return git(root, "diff", "--cached", "--unified=0", "--no-ext-diff", "--").stdout


def detect_documentation_reasons(paths: Sequence[str], diff: str) -> tuple[str, ...]:
    source_paths = [path for path in paths if classify_path(path) == "code"]
    changed_lines = "\n".join(
        line for line in diff.splitlines() if (line.startswith("+") or line.startswith("-")) and not line.startswith(("+++", "---"))
    )
    reasons: list[str] = []
    lower_paths = [path.lower() for path in paths]
    if any(Path(path).name.lower().startswith(".env") for path in paths) or ENV_PATTERN.search(changed_lines):
        reasons.append("variables de entorno o configuracion operativa")
    if any("/routes/" in f"/{path}/" or "/api/" in f"/{path}/" for path in lower_paths) and API_PATTERN.search(changed_lines):
        reasons.append("API publica o endpoints")
    if any(Path(path).name.lower() in {"config.js", "config.ts"} for path in source_paths) and API_PATTERN.search(changed_lines):
        reasons.append("configuracion publica")
    return tuple(dict.fromkeys(reasons))


def validate_atomicity(changes: Sequence[StagedChange]) -> None:
    categories = {change.category for change in changes if change.category not in {"docs", "test"}}
    if "code" in categories and "style" in categories:
        raise PolicyError(
            "El staging mezcla logica funcional con estilos. Indexe y confirme cada proposito por separado."
        )
    independent = categories - {"code", "build"}
    if len(independent) > 1 or ("code" in categories and independent):
        listed = ", ".join(sorted(categories))
        raise PolicyError(
            f"El staging mezcla categorias independientes ({listed}). Indexe archivos por unidad logica."
        )
    if "build" in categories and independent:
        raise PolicyError("Los cambios de build no pueden mezclarse con otra categoria independiente.")


def infer_type(changes: Sequence[StagedChange]) -> str | None:
    categories = {change.category for change in changes}
    primary = categories - {"docs", "test"}
    if not primary and "test" in categories:
        return "test"
    if not primary:
        return "docs"
    if primary == {"style"}:
        return "style"
    if primary == {"ci"}:
        return "ci"
    if primary == {"build"}:
        return "build"
    if primary == {"chore"}:
        return "chore"
    return None


def analyze(root: Path) -> Analysis:
    paths = staged_paths(root)
    changes = tuple(StagedChange(path, classify_path(path)) for path in paths)
    validate_atomicity(changes)
    documentation_paths = tuple(change.path for change in changes if change.category == "docs")
    reasons = list(detect_documentation_reasons(paths, added_or_removed_diff(root)))
    structural_paths = cached_paths(root, "ADR")
    if any(
        classify_path(path) == "code" and ARCHITECTURE_PATH_PATTERN.search(path.lower())
        for path in structural_paths
    ):
        reasons.append("arquitectura o modulos publicos")
    reasons = list(dict.fromkeys(reasons))
    if reasons and not documentation_paths:
        joined = ", ".join(reasons)
        raise PolicyError(
            f"El cambio afecta a {joined}, pero no hay README.md ni archivos docs/ en staging."
        )
    return Analysis(changes, documentation_paths, tuple(reasons), infer_type(changes))


def validate_type(requested: str | None, analysis: Analysis) -> str:
    if analysis.inferred_type:
        if requested and requested != analysis.inferred_type:
            raise PolicyError(
                f"El staging se clasifica como '{analysis.inferred_type}', no como '{requested}'."
            )
        return analysis.inferred_type
    if not requested:
        raise PolicyError(
            "El staging contiene codigo: indique --type feat, fix, refactor o perf segun su intencion."
        )
    if requested not in CODE_TYPES:
        raise PolicyError(
            "Los cambios de codigo deben clasificarse como feat, fix, refactor o perf; "
            "separe tests, estilos o build si constituyen el proposito principal."
        )
    return requested


def validate_required_documentation(kind: str, analysis: Analysis) -> None:
    if kind == "feat" and not analysis.documentation_paths:
        raise PolicyError(
            "\x1b[31m¡Atención! Estás añadiendo una funcionalidad pero no has incluido "
            "cambios en la documentación.\x1b[0m"
        )


def validate_title(title: str) -> str:
    cleaned = title.strip()
    if any(cleaned.lower().startswith(f"{kind}:") for kind in TYPES):
        raise PolicyError("Pase solo la descripcion en --title; el prefijo lo genera la skill.")
    if not cleaned:
        raise PolicyError("La descripcion corta no puede estar vacia.")
    if len(cleaned) > 50:
        raise PolicyError("La descripcion corta excede los 50 caracteres.")
    if cleaned.endswith("."):
        raise PolicyError("La descripcion corta no debe terminar en punto.")
    first_letter = next((character for character in cleaned if character.isalpha()), "")
    if not first_letter or not first_letter.isupper():
        raise PolicyError("La descripcion corta debe comenzar con mayuscula.")
    return cleaned


def validate_text(label: str, value: str, minimum: int = 1) -> str:
    cleaned = value.strip()
    if len(cleaned) < minimum:
        raise PolicyError(f"El bloque {label} debe contener una explicacion suficiente.")
    return cleaned


def build_message(kind: str, title: str, why: str, how: Iterable[str], docs: Sequence[str]) -> str:
    bullets = [f"- {validate_text('CÓMO', item)}" for item in how]
    if not bullets:
        raise PolicyError("Debe proporcionar al menos una decision tecnica con --how.")
    documentation = "\n".join(f"- {path}" for path in docs) if docs else "N/A"
    return (
        f"{kind}: {title}\n\n"
        f"PORQUÉ:\n{validate_text('PORQUÉ', why, minimum=20)}\n\n"
        f"CÓMO:\n" + "\n".join(bullets) + "\n\n"
        f"DOCUMENTACIÓN:\n{documentation}"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Valida y crea commits narrativos atomicos para Gara.")
    result.add_argument("--repo", default=".", help="Ruta dentro del checkout de Gara (por defecto: .).")
    result.add_argument("--type", choices=TYPES, help="Tipo semantico; obligatorio para cambios de codigo.")
    result.add_argument("--title", required=True, help="Descripcion sin prefijo, maximo 50 caracteres.")
    result.add_argument("--why", required=True, help="Contexto o limitacion que motiva el cambio.")
    result.add_argument("--how", action="append", required=True, help="Decision tecnica; repetir para varias viñetas.")
    result.add_argument("--dry-run", action="store_true", help="Validar y mostrar el mensaje sin ejecutar commit.")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args(argv)
    try:
        root = repository_root(Path(args.repo).resolve())
        analysis = analyze(root)
        kind = validate_type(args.type, analysis)
        validate_required_documentation(kind, analysis)
        message = build_message(
            kind,
            validate_title(args.title),
            args.why,
            args.how,
            analysis.documentation_paths,
        )
        print(f"Repositorio: {root}")
        print("Staging validado: " + ", ".join(f"{item.path} [{item.category}]" for item in analysis.changes))
        if analysis.documentation_reasons:
            print("Documentacion requerida por: " + ", ".join(analysis.documentation_reasons))
        print("\nMensaje de commit:\n")
        print(message)
        if args.dry_run:
            print("\nValidacion completada; --dry-run impide crear el commit.")
            return 0
        commit = git(root, "commit", "-m", message, check=False)
        if commit.returncode != 0:
            raise PolicyError(commit.stderr.strip() or commit.stdout.strip() or "No se pudo crear el commit.")
        print("\n" + commit.stdout.strip())
        return 0
    except PolicyError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
