"""Verify resolved audit guards in temporaries, without models or remote services."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))


@contextlib.contextmanager
def fixture():
    from test_workflow import Execution

    case = Execution()
    case.setUp()
    try:
        yield case
    finally:
        case.doCleanups()


def publish_mutation():
    from gara_workflow.common import Blocked, git
    from gara_workflow.engines import run_session

    with fixture() as case:

        def client(*args, **kwargs):
            result = run_session(*args, **kwargs)
            if "Fase: publish;" in args[1]:
                (case.repo / "feature.txt").write_text("broken", encoding="utf-8")
            return result

        blocked = False
        with patch("gara_workflow.runner.run_session", side_effect=client):
            try:
                case.runner().run(publish=True)
            except Blocked:
                blocked = True
        data = case.state()
        return {
            "resolved": blocked
            and not {"verify", "review", "publish"}.intersection(
                data["completed_phases"]
            ),
            "workflow_status": data["status"],
            "feature_after_publish": (case.repo / "feature.txt").read_text(),
            "phases_marked_complete": data["completed_phases"],
            "dirty_after_completion": bool(git(case.repo, "status", "--porcelain")),
        }


def empty_review():
    from gara_workflow.common import Blocked
    from gara_workflow.engines import run_session

    with fixture() as case:

        def client(*args, **kwargs):
            result = run_session(*args, **kwargs)
            if "Fase: verify;" in args[1] or "Fase: review;" in args[1]:
                revision = case.repo / "specs" / case.slug / "REVISION.md"
                revision.write_text("", encoding="utf-8")
            return result

        blocked = False
        with patch("gara_workflow.runner.run_session", side_effect=client):
            try:
                case.runner().run()
            except Blocked:
                blocked = True
        revision = case.repo / "specs" / case.slug / "REVISION.md"
        return {
            "resolved": blocked and "review" not in case.state()["completed_phases"],
            "workflow_status": case.state()["status"],
            "revision_bytes": revision.stat().st_size,
            "review_marked_complete": "review" in case.state()["completed_phases"],
        }


def checkout_locks():
    from gara_workflow.common import Blocked
    from gara_workflow.runner import Runner, flow_lock

    with fixture() as case:
        first = case.runner().lock_path
        second = Runner(case.repo, "gar-123-segunda-spec", "codex").lock_path
        blocked = False
        with flow_lock(first):
            try:
                with flow_lock(second):
                    pass
            except Blocked:
                blocked = True
        return {
            "resolved": first == second and blocked,
            "same_checkout_two_slug_locks_acquired": not blocked,
        }


def issue_branch_prefix():
    from gara_workflow.common import Blocked

    with fixture() as case:
        spec = case.repo / "specs" / case.slug / "SPEC.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("GAR-123", "GAR-12"),
            encoding="utf-8",
        )
        blocked = False
        try:
            case.runner().run(dry_run=True)
        except Blocked:
            blocked = True
        return {
            "resolved": blocked and not case.events.exists(),
            "preflight_status": "blocked" if blocked else "dry-run",
            "spec_issue": "GAR-12",
            "branch_issue": "GAR-123",
            "model_called": case.events.exists(),
        }


def json_redaction():
    from dataclasses import asdict

    from gara_workflow.common import redact, save_json
    from gara_workflow.engines import parse_result

    synthetic = "FAKE_AUDIT_SECRET_VALUE"
    quoted = json.dumps({"api_key": synthetic, "token": synthetic})
    marker = "<!-- gara-result --> " + json.dumps(
        {"status": "completed", "summary": quoted}
    )
    lines = [
        json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": marker},
            }
        ),
        json.dumps({"type": "turn.completed", "usage": {}}),
    ]
    result = parse_result("codex", 0, lines, "")
    with tempfile.TemporaryDirectory(prefix="gara-audit-redaction-") as directory:
        logfile = Path(directory) / "normalized.json"
        save_json(logfile, asdict(result))
        log_redacted = synthetic not in logfile.read_text(encoding="utf-8")
    return {
        "resolved": log_redacted and synthetic not in redact(quoted),
        "plain_assignment_redacted": synthetic not in redact("API_KEY=" + synthetic),
        "json_value_redacted": synthetic not in redact(quoted),
        "normalized_summary_log_redacted": log_redacted,
        "uses_synthetic_values_only": True,
    }


def package_source(root: Path):
    skill = root / "skills" / "gara-probe"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: "gara-probe"\ndescription: "Fixture de auditoría."\n---\n'
        "# Fixture\n\nAnaliza exclusivamente los datos temporales.\n",
        encoding="utf-8",
    )
    (root / "profiles").mkdir()
    (root / "profiles" / "gara.md").write_text("# Perfil fixture\n", encoding="utf-8")
    (root / "roles").mkdir()
    (root / "roles" / "gara-probe.md").write_text("# Rol fixture\n", encoding="utf-8")
    catalog = {
        "version": "0.1.0",
        "skills": [
            {
                "name": "gara-probe",
                "title": "Fixture",
                "short": "Fixture temporal para comprobar la instalación",
                "explicit_only": False,
            }
        ],
        "agents": [
            {
                "name": "gara-probe",
                "description": "Rol fixture",
                "read_only": True,
                "claude_tools": "Read",
                "source": "roles/gara-probe.md",
            }
        ],
        "mapping": [],
    }
    (root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    return catalog


def obsolete_installation():
    from gara_workflow.packaging import install

    with tempfile.TemporaryDirectory(prefix="gara-audit-install-") as directory:
        root, home = Path(directory) / "source", Path(directory) / "home"
        catalog = package_source(root)
        install(root, home, "claude")
        catalog["agents"] = []
        (root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        install(root, home, "claude")
        remaining = (home / ".claude/agents/gara-probe.md").is_file()
        return {
            "resolved": not remaining,
            "removed_role_still_installed": remaining,
            "removed_role_absent_from_distribution": not (
                root / ".build/claude/agents/gara-probe.md"
            ).exists(),
        }


def install_dry_run():
    from gara_workflow.common import WorkflowError
    from gara_workflow.packaging import install

    with tempfile.TemporaryDirectory(prefix="gara-audit-preflight-") as directory:
        root, home = Path(directory) / "source", Path(directory) / "home"
        package_source(root)
        target = home / ".claude/agents/gara-probe.md"
        target.parent.mkdir(parents=True)
        target.write_text("Archivo ajeno.", encoding="utf-8")
        preview_blocked = False
        try:
            install(root, home, "claude", dry_run=True)
        except WorkflowError:
            preview_blocked = True
        collision = False
        try:
            install(root, home, "claude")
        except WorkflowError:
            collision = True
        return {
            "resolved": preview_blocked
            and collision
            and not (root / ".build").exists(),
            "dry_run_status": "blocked" if preview_blocked else "dry-run",
            "actual_install_detects_collision": collision,
            "foreign_file_preserved": target.read_text(encoding="utf-8")
            == "Archivo ajeno.",
        }


def main():
    observations = {}
    for probe in (
        publish_mutation,
        empty_review,
        checkout_locks,
        issue_branch_prefix,
        json_redaction,
        obsolete_installation,
        install_dry_run,
    ):
        with contextlib.redirect_stdout(io.StringIO()):
            observations[probe.__name__] = probe()
    report = json.dumps(observations, ensure_ascii=False, indent=2) + "\n"
    if len(sys.argv) == 3 and sys.argv[1] == "--output":
        Path(sys.argv[2]).write_text(report, encoding="utf-8")
    print(report, end="")
    if not all(item["resolved"] for item in observations.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
