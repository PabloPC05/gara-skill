from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import signal
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gara_workflow.common import (
    Blocked,
    ROOT,
    WorkflowError,
    git,
    inside,
    read_tasks,
    redact,
    runtime_dir,
    task_fingerprint,
    validate_tasks,
)
from gara_workflow.cli import main as cli_main
from gara_workflow.cli import terminate_as_interrupt
from gara_workflow.engines import parse_result, stream_process
from gara_workflow.runner import Runner, flow_lock


def contract():
    return {
        "version": 1,
        "issue": "GAR-123",
        "tasks": [
            {
                "id": "T1",
                "requirements": ["R1"],
                "depends_on": [],
                "files": ["feature.txt"],
                "briefing": "Implementa el caso.",
                "acceptance": [{"argv": ["python", "-c", "assert 1 + 1 == 2"]}],
                "status": "pending",
                "weight": 1,
            }
        ],
        "batches": [["T1"]],
    }


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_valid_contract(self):
        validate_tasks(contract(), self.root, "GAR-123", {"R1"})

    def invalid(self, data):
        with self.assertRaises(WorkflowError):
            validate_tasks(data, self.root, "GAR-123", {"R1"})

    def test_duplicate_task_in_batch(self):
        data = contract()
        data["batches"] = [["T1", "T1"]]
        self.invalid(data)

    def test_unknown_dependency(self):
        data = contract()
        data["tasks"][0]["depends_on"] = ["T9"]
        self.invalid(data)

    def test_same_batch_dependency_rejected(self):
        data = contract()
        second = copy.deepcopy(data["tasks"][0])
        second.update(id="T2", files=["b.txt"], depends_on=["T1"])
        data["tasks"].append(second)
        data["batches"] = [["T1", "T2"]]
        self.invalid(data)

    def test_file_collision_rejected(self):
        data = contract()
        second = copy.deepcopy(data["tasks"][0])
        second["id"] = "T2"
        data["tasks"].append(second)
        data["batches"] = [["T1", "T2"]]
        self.invalid(data)

    def test_load_limit(self):
        data = contract()
        data["tasks"][0]["weight"] = 4
        second = copy.deepcopy(data["tasks"][0])
        second.update(id="T2", files=["b.txt"])
        data["tasks"].append(second)
        data["batches"] = [["T1", "T2"]]
        self.invalid(data)

    def test_uncovered_requirement(self):
        with self.assertRaises(WorkflowError):
            validate_tasks(contract(), self.root, "GAR-123", {"R1", "R2"})

    def test_empty_acceptance(self):
        data = contract()
        data["tasks"][0]["acceptance"] = []
        self.invalid(data)

    def test_acceptance_that_cannot_fail_is_rejected(self):
        for argv in (
            ["true"],
            [":"],
            ["python", "-c", "pass"],
            ["python3", "-c", ""],
            ["py", "-c", "'ok'"],
        ):
            with self.subTest(argv=argv):
                data = contract()
                data["tasks"][0]["acceptance"] = [{"argv": argv}]
                self.invalid(data)

    def test_real_python_acceptance_is_accepted(self):
        data = contract()
        data["tasks"][0]["acceptance"] = [
            {"argv": ["python", "-c", "import sys; sys.exit(0)"]},
            {"argv": ["python", "-m", "unittest"], "timeout": 3600},
        ]
        validate_tasks(data, self.root, "GAR-123", {"R1"})

    def test_tasks_cannot_assign_hooks_client_settings_or_secrets(self):
        for name in (
            ".claude/settings.json",
            ".codex/config.toml",
            ".husky/pre-commit",
            ".env",
            ".env.local",
            "HUSKY~1/pre-commit",
        ):
            with self.subTest(name=name):
                data = contract()
                data["tasks"][0]["files"] = [name]
                self.invalid(data)
        data = contract()
        data["tasks"][0]["files"] = [".env.example", ".github/workflows/ci.yml"]
        validate_tasks(data, self.root, "GAR-123", {"R1"})

    def test_acceptance_cwd_cannot_enter_protected_directories(self):
        data = contract()
        data["tasks"][0]["acceptance"][0]["cwd"] = ".claude"
        self.invalid(data)

    def test_acceptance_timeout_has_an_upper_bound(self):
        data = contract()
        data["tasks"][0]["acceptance"][0]["timeout"] = 3601
        self.invalid(data)

    def test_malformed_nested_types_report_failure(self):
        for key in ("requirements", "depends_on", "files", "status"):
            with self.subTest(key=key):
                data = contract()
                data["tasks"][0][key] = [{}]
                self.invalid(data)
        data = contract()
        data["batches"] = [[{}]]
        self.invalid(data)

    def test_paths_cannot_escape_or_use_globs(self):
        for name in (
            "../secret",
            ".git/config",
            ".GIT/config",
            ".git./config",
            ".git /config",
            "GIT~1/config",
            "C:/secret",
            "a\\b",
            "src/*",
            "src/../x",
        ):
            with self.subTest(name=name), self.assertRaises(WorkflowError):
                inside(self.root, name)

    def test_fingerprint_excludes_execution_state(self):
        a = contract()
        b = copy.deepcopy(a)
        b["tasks"][0].update(status="verified", evidence=[{"returncode": 0}])
        self.assertEqual(task_fingerprint(a), task_fingerprint(b))
        b["tasks"][0]["briefing"] = "Otra implementación."
        self.assertNotEqual(task_fingerprint(a), task_fingerprint(b))


class Protocols(unittest.TestCase):
    def test_codex_requires_provider_close_and_marker(self):
        lines = [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "agent_message",
                        "text": '<!-- gara-result --> {"status":"completed","summary":"ok"}',
                    },
                }
            )
        ]
        self.assertEqual(parse_result("codex", 0, lines, "").status, "failed")
        lines.append('{"type":"turn.completed","usage":{"input_tokens":2}}')
        self.assertEqual(parse_result("codex", 0, lines, "").status, "completed")

    def test_missing_marker_blocks(self):
        self.assertEqual(
            parse_result("codex", 0, ['{"type":"turn.completed"}'], "").status,
            "blocked",
        )

    def test_claude_permission_denial_blocks_despite_success(self):
        event = {
            "type": "result",
            "subtype": "success",
            "permission_denials": [{"tool_name": "Bash"}],
            "result": '<!-- gara-result --> {"status":"completed"}',
        }
        self.assertEqual(
            parse_result("claude", 0, [json.dumps(event)], "").status, "blocked"
        )

    def test_quota_is_recoverable_infrastructure(self):
        self.assertTrue(
            parse_result("codex", 1, [], "429 quota exceeded").infrastructure
        )

    def test_missing_authentication_is_prerequisite_block(self):
        self.assertEqual(
            parse_result("claude", 1, [], "Not logged in · Please run /login").status,
            "blocked",
        )

    def test_json_marker_handles_nested_summary(self):
        event = {
            "type": "result",
            "subtype": "success",
            "result": '<!-- gara-result --> {"status":"completed","summary":{"checks":1}}',
        }
        self.assertEqual(
            parse_result("claude", 0, [json.dumps(event)], "").status, "completed"
        )

    def test_invalid_stream_is_failure(self):
        self.assertEqual(
            parse_result("claude", 0, ["broken", "[]"], "").status, "failed"
        )

    def test_sensitive_strings_redacted(self):
        clean = redact(
            "Authorization: Bearer private-token\nMY_API_KEY=private\nsk-1234567890123456789"
        )
        self.assertNotIn("private", clean)
        self.assertNotIn("sk-123", clean)

    def test_arguments_are_passed_literally(self):
        argument = 'spaces $() ` " & | ;'
        code, out, err = stream_process(
            ["python", "-c", "import sys; print(sys.argv[1])", argument], ROOT
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, [argument])

    def test_timeout_stops_only_owned_process(self):
        with self.assertRaises(Blocked):
            stream_process(
                ["python", "-c", "import time; time.sleep(30)"], ROOT, timeout=0.2
            )


class Execution(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-flow-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "gara"
        self.repo.mkdir()
        self.events = self.root / "events.txt"
        self.client = ROOT / "tests/fixtures/fake_client.py"
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "README.md").write_text("Fixture temporal.\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "test: Inicio fixture")
        git(self.repo, "checkout", "-b", "fixture/gar-123-ejemplo")
        self.slug = "gar-123-ejemplo"
        artifacts = self.repo / "specs" / self.slug
        artifacts.mkdir(parents=True)
        (artifacts / "SPEC.md").write_text(
            "---\nissue: GAR-123\napproved: true\n---\n# Spec\n### R1 — Archivo verificable\nLa implementación crea feature.txt.\n",
            encoding="utf-8",
        )
        self.environment = patch.dict(
            os.environ,
            {"GARA_FAKE_EVENTS": str(self.events), "GARA_FAKE_MODE": "normal"},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def runner(self, engine="codex", timeout=20):
        return Runner(
            self.repo,
            self.slug,
            engine,
            client=str(self.client),
            timeout=timeout,
            confirm_contract=False,
        )

    def phases(self):
        return self.events.read_text().splitlines() if self.events.is_file() else []

    def state(self):
        return json.loads(
            (runtime_dir(self.repo, self.slug) / "state.json").read_text()
        )

    def snapshot(self):
        return {
            p.relative_to(self.repo).as_posix(): p.read_bytes()
            for p in self.repo.rglob("*")
            if p.is_file()
        }

    def test_end_to_end_codex(self):
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertEqual(self.phases().count("build"), 1)
        tasks = read_tasks(
            self.repo / "specs" / self.slug / "TAREAS.md", self.repo, "GAR-123", {"R1"}
        )
        self.assertEqual(tasks["tasks"][0]["status"], "verified")
        self.assertEqual(tasks["tasks"][0]["evidence"][0]["returncode"], 0)
        self.assertNotIn("publish", self.phases())

    def test_end_to_end_claude(self):
        self.assertEqual(self.runner("claude").run()["status"], "completed")

    def test_publish_is_explicit(self):
        self.runner().run(publish=True)
        self.assertIn("publish", self.phases())
        self.assertIn("publish", self.state()["completed_phases"])

    def test_dry_run_has_no_writes_or_model_calls(self):
        before = self.snapshot()
        self.assertEqual(self.runner().run(dry_run=True)["status"], "dry-run")
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.events.exists())

    def test_dirty_foreign_file_blocks_before_model(self):
        (self.repo / "foreign.txt").write_text("preserve")
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual((self.repo / "foreign.txt").read_text(), "preserve")
        self.assertFalse(self.events.exists())

    def test_main_branch_rejected(self):
        git(self.repo, "checkout", "main")
        with self.assertRaises(Blocked):
            self.runner().run()

    def test_checkpoint_requires_explicit_ack(self):
        os.environ["GARA_FAKE_MODE"] = "checkpoint"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual(self.state()["checkpoint"], "T1")
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual(self.runner().run(acknowledge=True)["status"], "completed")
        self.assertEqual(self.phases().count("build"), 1)

    def test_tasks_contract_pauses_for_review_unless_acknowledged(self):
        runner = Runner(
            self.repo, self.slug, "codex", client=str(self.client), timeout=20
        )
        with self.assertRaises(Blocked) as raised:
            runner.run()
        self.assertIn("T1:", str(raised.exception))
        self.assertEqual(self.state()["checkpoint"], "tasks")
        self.assertEqual(self.phases(), ["plan", "tasks"])
        with self.assertRaises(Blocked):
            runner.run()
        self.assertEqual(runner.run(acknowledge=True)["status"], "completed")
        self.assertEqual(self.phases().count("tasks"), 1)

    def test_acknowledging_up_front_skips_the_contract_pause(self):
        runner = Runner(
            self.repo, self.slug, "codex", client=str(self.client), timeout=20
        )
        self.assertEqual(runner.run(acknowledge=True)["status"], "completed")

    def test_model_cannot_start_tasks_as_verified(self):
        os.environ["GARA_FAKE_MODE"] = "initial-verified"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertNotIn("build", self.phases())
        self.assertEqual(self.state()["status"], "blocked")

    def test_gate_does_not_inherit_secrets_from_the_environment(self):
        os.environ["GARA_FAKE_MODE"] = "env-probe"
        os.environ["GARA_SECRET_PROBE"] = "must-not-reach-the-gate"
        self.addCleanup(os.environ.pop, "GARA_SECRET_PROBE", None)
        self.assertEqual(self.runner().run()["status"], "completed")

    def test_unexpected_exception_is_recorded_as_failed(self):
        with patch.object(Runner, "build", side_effect=KeyError("reviews")):
            with self.assertRaises(KeyError):
                self.runner().run()
        self.assertEqual(self.state()["status"], "failed")

    def test_reset_requires_confirmation_and_keeps_artifacts(self):
        self.runner().run()
        arguments = ["reset", "--repo", str(self.repo), "--slug", self.slug]
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli_main(arguments), 2)
        self.assertTrue((runtime_dir(self.repo, self.slug) / "state.json").is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli_main([*arguments, "--yes"]), 0)
        self.assertFalse(runtime_dir(self.repo, self.slug).exists())
        self.assertTrue((self.repo / "specs" / self.slug / "TAREAS.md").is_file())

    def test_reset_waits_for_the_active_run(self):
        from gara_workflow.runner import checkout_lock_path

        arguments = ["reset", "--repo", str(self.repo), "--slug", self.slug, "--yes"]
        with flow_lock(checkout_lock_path(self.repo)):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli_main(arguments), 2)

    def test_termination_signals_become_an_interrupt_and_are_restored(self):
        before = signal.getsignal(signal.SIGTERM)
        with terminate_as_interrupt():
            with self.assertRaises(KeyboardInterrupt):
                signal.raise_signal(signal.SIGTERM)
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    def test_completed_resume_skips_model_phases(self):
        self.runner().run()
        before = self.phases()
        self.runner().run()
        self.assertEqual(self.phases(), before)

    def test_plan_edit_prevents_stale_resume(self):
        self.runner().run()
        (self.repo / "specs" / self.slug / "PLAN.md").write_text("Changed")
        with self.assertRaises(Blocked):
            self.runner().run()

    def test_changed_verified_file_is_reconciled(self):
        self.runner().run()
        (self.repo / "feature.txt").write_text("broken")
        self.runner().run()
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")
        self.assertEqual(self.phases().count("build"), 2)

    def test_crash_before_commit_recovers_without_rebuilding(self):
        os.environ["GARA_FAKE_MODE"] = "crash-before-commit"
        with self.assertRaises(WorkflowError):
            self.runner().run()
        os.environ["GARA_FAKE_MODE"] = "normal"
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(self.phases().count("build"), 1)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_unchanged_quota_retries_once(self):
        os.environ["GARA_FAKE_MODE"] = "quota-once"
        self.runner().run()
        self.assertEqual(self.phases().count("build"), 2)

    def test_quota_after_edits_reconciles_before_retry(self):
        os.environ["GARA_FAKE_MODE"] = "quota-after-write"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual(self.phases().count("build"), 1)
        os.environ["GARA_FAKE_MODE"] = "normal"
        self.runner().run()
        self.assertEqual(self.phases().count("build"), 1)

    def test_agent_success_does_not_hide_acceptance_failure(self):
        os.environ["GARA_FAKE_MODE"] = "gate-failure"
        with self.assertRaises(WorkflowError):
            self.runner().run()
        self.assertNotIn("commit", self.phases())
        self.assertEqual(self.state()["status"], "failed")

    def test_agent_cannot_edit_outside_scope(self):
        os.environ["GARA_FAKE_MODE"] = "build-escape"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertNotIn("commit", self.phases())

    def test_gate_cannot_escape_contract(self):
        os.environ["GARA_FAKE_MODE"] = "gate-escape"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertNotIn("commit", self.phases())

    def test_agent_cannot_change_acceptance_contract(self):
        os.environ["GARA_FAKE_MODE"] = "contract-change"
        with self.assertRaises(Blocked):
            self.runner().run()

    def test_success_message_cannot_replace_commit(self):
        os.environ["GARA_FAKE_MODE"] = "missing-commit"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertNotIn("verify", self.phases())

    def test_permission_block_retains_state(self):
        os.environ["GARA_FAKE_MODE"] = "permission"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual(self.state()["status"], "blocked")

    def test_dependencies_across_two_batches(self):
        os.environ["GARA_FAKE_MODE"] = "two-batches"
        self.runner().run()
        self.assertEqual(self.phases().count("build"), 2)
        self.assertEqual((self.repo / "second.txt").read_text(), "done")

    def test_review_regression_invalidates_previous_verification(self):
        os.environ["GARA_FAKE_MODE"] = "review-regression"
        with self.assertRaises(WorkflowError):
            self.runner().run()
        os.environ["GARA_FAKE_MODE"] = "normal"
        self.runner().run()
        self.assertEqual(self.phases().count("verify"), 2)
        self.assertEqual(self.phases().count("review"), 2)
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")

    def test_same_checkout_cannot_take_two_locks(self):
        lock = runtime_dir(self.repo, self.slug) / "test.lock"
        with flow_lock(lock):
            with self.assertRaises(Blocked), flow_lock(lock):
                pass
        with flow_lock(lock):
            pass


if __name__ == "__main__":
    unittest.main()
