"""Regression gates for checkout exclusion, review evidence and closed delivery."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gara_workflow.common import (
    Blocked,
    ROOT,
    WorkflowError,
    git,
    read_tasks,
    runtime_dir,
)
from gara_workflow.engines import Result
from gara_workflow.reviews import (
    implementation_files,
    implementation_matches,
    read_review,
    validate_record,
)
from gara_workflow.runner import Runner, flow_lock


def record(sha, tasks, role="gara-verifier"):
    return {
        "implementation_sha": sha,
        "author": {"name": "Fixture", "role": role},
        "requirements": [
            {"id": "R1", "result": "passed", "evidence": "feature.txt y aceptación T1"}
        ],
        "checks": [
            {"task": task["id"], "gate": number, "returncode": 0, "summary": "done"}
            for task in tasks
            for number in range(1, len(task["acceptance"]) + 1)
        ],
        "findings": [],
        "limitations": ["Cliente simulado; revisión humana pendiente."],
    }


def write_review(path, data):
    path.write_text(
        "# Revisión\n\n<!-- gara-review:v1 -->\n```json\n"
        + json.dumps(data, ensure_ascii=False)
        + "\n```\n",
        encoding="utf-8",
    )


class RunnerRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-regressions-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "gara"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "README.md").write_text("Fixture.\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "test: initialize fixture")
        self.base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-b", "fixture/gar-123-example")
        self.slug = "gar-123-example"
        self.artifacts = self.repo / "specs" / self.slug
        self.artifacts.mkdir(parents=True)
        (self.artifacts / "SPEC.md").write_text(
            "---\nissue: GAR-123\napproved: true\n---\n# Spec\n"
            "### R1 — Archivo verificable\nCrea feature.txt con done.\n",
            encoding="utf-8",
        )
        self.calls = []
        self.mode = "normal"
        self.publish_effect = None
        self.provider_patch = patch("gara_workflow.runner.run_session", self.provider)
        self.provider_patch.start()
        self.addCleanup(self.provider_patch.stop)

    def runner(self, slug=None):
        return Runner(self.repo, slug or self.slug, "codex", timeout=20)

    def state(self):
        return json.loads(
            (runtime_dir(self.repo, self.slug) / "state.json").read_text(
                encoding="utf-8"
            )
        )

    def tasks(self):
        return read_tasks(self.artifacts / "TAREAS.md", self.repo, "GAR-123", {"R1"})[
            "tasks"
        ]

    def commit_paths(self, *names):
        git(self.repo, "add", "--", *names)
        pending = subprocess.run(
            ["git", "-C", str(self.repo), "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if pending.returncode:
            git(self.repo, "commit", "-m", "test: record isolated evidence")

    def provider(self, engine, prompt, cwd, log, **kwargs):
        phase = re.search(r"Fase: ([a-z]+);", prompt)[1]
        self.calls.append(phase)
        feature = self.repo / "feature.txt"
        revision = self.artifacts / "REVISION.md"
        if phase == "plan":
            (self.artifacts / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
        elif phase == "tasks":
            task = {
                "id": "T1",
                "requirements": ["R1"],
                "depends_on": [],
                "files": ["feature.txt"],
                "briefing": "Crea feature.txt con done.",
                "acceptance": [
                    {
                        "argv": [
                            sys.executable,
                            "-c",
                            "from pathlib import Path; assert Path('feature.txt').read_text().strip() == 'done'",
                        ],
                        "timeout": 10,
                    }
                ],
                "status": "pending",
                "weight": 1,
                "checkpoint": self.mode == "checkpoint",
            }
            data = {
                "version": 1,
                "issue": "GAR-123",
                "tasks": [task],
                "batches": [["T1"]],
            }
            (self.artifacts / "TAREAS.md").write_text(
                "# Tareas\n\n<!-- gara-tasks:v1 -->\n```json\n"
                + json.dumps(data)
                + "\n```\n",
                encoding="utf-8",
            )
        elif phase == "build":
            feature.write_text("done", encoding="utf-8")
        elif phase == "commit":
            if self.mode == "crash-before-commit":
                return Result("failed", "Interrupción simulada")
            self.commit_paths("specs", "feature.txt")
        elif phase in {"verify", "review"}:
            if self.mode == "empty-review":
                revision.write_text("", encoding="utf-8")
                return Result("completed", "Archivo vacío", "fixture-" + phase)
            try:
                data = read_review(revision, "GAR-123")
            except Blocked:
                data = {"version": 1, "issue": "GAR-123"}
            if phase == "review":
                if self.mode == "review-regression":
                    feature.write_text("broken", encoding="utf-8")
                elif (
                    self.mode == "review-correction" and self.calls.count("review") == 1
                ):
                    feature.write_text("done\n", encoding="utf-8")
                    self.commit_paths("feature.txt")
                elif self.mode == "repeated-review-correction":
                    feature.write_text(feature.read_text() + "\n", encoding="utf-8")
                    self.commit_paths("feature.txt")
                if self.mode == "overwrite-verification":
                    data["verification"]["limitations"] = ["Sobrescrita."]
            key = "verification" if phase == "verify" else "review"
            data[key] = record(git(self.repo, "rev-parse", "HEAD"), self.tasks())
            if phase == "review":
                data[key]["author"]["role"] = "gara-review"
            write_review(revision, data)
        elif phase == "publish":
            review = read_review(revision, "GAR-123")["review"]
            sha = review["implementation_sha"]
            if self.mode == "delivery-wrong-sha":
                sha = self.base
            (self.artifacts / "ENTREGA.md").write_text(
                "# Entrega simulada\nhttps://github.com/example/gara/pull/1\n"
                f"Implementation SHA: {sha}\nIn Review\n",
                encoding="utf-8",
            )
            if self.publish_effect:
                self.publish_effect()
        return Result("completed", "Evidencia simulada", "fixture-" + phase)

    def report(self):
        return read_review(self.artifacts / "REVISION.md", "GAR-123")

    def assert_unclosed_reviews(self):
        self.assertFalse(
            {"verify", "review", "publish"} & set(self.state()["completed_phases"])
        )

    def test_full_issue_token_rejects_numeric_prefix_before_any_model_call(self):
        spec = self.artifacts / "SPEC.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("GAR-123", "GAR-12"),
            encoding="utf-8",
        )
        with self.assertRaises(Blocked):
            self.runner().run(dry_run=True)
        self.assertEqual(self.calls, [])
        self.assertFalse(runtime_dir(self.repo, self.slug).exists())

    def test_issue_token_accepts_delimiters_and_rejects_embedded_tokens(self):
        for branch in (
            "gar-1234",
            "fixture/gar-123x",
            "fixture/xgar-123",
            "feature/without-issue",
        ):
            with self.subTest(branch=branch):
                git(self.repo, "branch", "-m", branch)
                with self.assertRaises(Blocked):
                    self.runner().run(dry_run=True)
        for branch in ("gar-123", "fixture/GAR-123-title", "fixture/gar-123_title"):
            with self.subTest(branch=branch):
                git(self.repo, "branch", "-m", branch)
                self.assertEqual(self.runner().run(dry_run=True)["status"], "dry-run")
        self.assertEqual(self.calls, [])

    def test_empty_revision_cannot_close_verification(self):
        self.mode = "empty-review"
        with self.assertRaisesRegex(Blocked, "gara-review:v1"):
            self.runner().run()
        self.assertNotIn("verify", self.state()["completed_phases"])
        self.assertNotIn("review", self.calls)

    def test_review_preserves_verification_and_later_document_commits_are_allowed(self):
        self.assertEqual(self.runner().run()["status"], "completed")
        report = self.report()
        self.assertNotEqual(
            report["verification"]["implementation_sha"],
            git(self.repo, "rev-parse", "HEAD"),
        )
        for phase in ("verify", "review"):
            key = "verification" if phase == "verify" else "review"
            self.assertEqual(self.state()["reviews"][phase]["record"], report[key])
            self.assertEqual(
                self.state()["reviews"][phase]["independence"], "unverified"
            )
            self.assertEqual(
                self.state()["reviews"][phase]["provider_session_id"],
                "fixture-" + phase,
            )
            self.assertEqual(self.state()["reviews"][phase]["delegations"], [])
            validate_record(report, phase, self.repo, {"R1"}, self.tasks())

    def test_review_cannot_overwrite_closed_verification(self):
        self.mode = "overwrite-verification"
        with self.assertRaisesRegex(Blocked, "sobrescribió"):
            self.runner().run()
        self.assert_unclosed_reviews()

    def test_report_requires_author_coverage_results_limitations_and_real_sha(self):
        self.runner().run()
        original = self.report()
        mutations = [
            lambda r: r.pop("author"),
            lambda r: r.update(author={"name": "Fixture"}),
            lambda r: r.update(requirements=[]),
            lambda r: r["requirements"][0].update(evidence=" "),
            lambda r: r.update(checks=[]),
            lambda r: r["checks"][0].update(returncode=1),
            lambda r: r["checks"][0].update(gate=True),
            lambda r: r.update(limitations=[]),
            lambda r: r.update(implementation_sha="f" * 40),
            lambda r: r.update(implementation_sha=self.base),
            lambda r: r.update(independent=True),
            lambda r: r.update(
                findings=[
                    {
                        "severity": {},
                        "status": "resolved",
                        "summary": "fallo",
                        "evidence": "reproducción",
                    }
                ]
            ),
            lambda r: r.update(
                findings=[
                    {
                        "severity": "low",
                        "status": [],
                        "summary": "fallo",
                        "evidence": "reproducción",
                    }
                ]
            ),
            lambda r: r.update(
                findings=[
                    {
                        "severity": "high",
                        "status": "open",
                        "summary": "fallo",
                        "evidence": "reproducción",
                    }
                ]
            ),
        ]
        for number, mutate in enumerate(mutations):
            with self.subTest(case=number):
                candidate = copy.deepcopy(original)
                mutate(candidate["review"])
                with self.assertRaises(Blocked):
                    validate_record(
                        candidate, "review", self.repo, {"R1"}, self.tasks()
                    )

    def test_report_requires_every_acceptance_once_without_duplicate_requirements(self):
        self.runner().run()
        report = self.report()
        tasks = self.tasks()
        tasks[0]["acceptance"].append(copy.deepcopy(tasks[0]["acceptance"][0]))
        tasks[0]["evidence"].append(copy.deepcopy(tasks[0]["evidence"][0]))
        with self.assertRaises(Blocked):
            validate_record(report, "review", self.repo, {"R1"}, tasks)
        report["review"]["checks"].append(copy.deepcopy(report["review"]["checks"][0]))
        with self.assertRaises(Blocked):
            validate_record(report, "review", self.repo, {"R1"}, self.tasks())
        report = self.report()
        report["review"]["requirements"].append(
            copy.deepcopy(report["review"]["requirements"][0])
        )
        with self.assertRaises(Blocked):
            validate_record(report, "review", self.repo, {"R1"}, self.tasks())

    def test_real_sha_from_unrelated_history_is_rejected_even_when_content_matches(
        self,
    ):
        self.runner().run()
        original = git(self.repo, "branch", "--show-current")
        git(self.repo, "checkout", "--orphan", "fixture/gar-123-unrelated")
        self.commit_paths("specs", "feature.txt", "README.md")
        unrelated = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", original)
        self.assertFalse(
            implementation_matches(
                self.repo, unrelated, implementation_files(self.tasks())
            )
        )

    def test_sha_checks_blob_content_even_with_index_trust_flags(self):
        feature = self.repo / "feature.txt"
        feature.write_text("done", encoding="utf-8")
        self.commit_paths("feature.txt")
        sha = git(self.repo, "rev-parse", "HEAD")
        for enable, disable in (
            ("--assume-unchanged", "--no-assume-unchanged"),
            ("--skip-worktree", "--no-skip-worktree"),
        ):
            with self.subTest(flag=enable):
                git(self.repo, "update-index", enable, "--", "feature.txt")
                feature.write_text("done\n", encoding="utf-8")
                self.assertEqual(git(self.repo, "diff", "--name-only", sha), "")
                self.assertFalse(
                    implementation_matches(self.repo, sha, ["feature.txt"])
                )
                feature.write_text("done", encoding="utf-8")
                git(self.repo, "update-index", disable, "--", "feature.txt")

    def test_sha_checks_preserve_git_line_ending_normalization(self):
        (self.repo / ".gitattributes").write_text(
            "feature.txt text eol=lf\n", encoding="utf-8"
        )
        feature = self.repo / "feature.txt"
        feature.write_bytes(b"done\n")
        self.commit_paths(".gitattributes", "feature.txt")
        sha = git(self.repo, "rev-parse", "HEAD")
        feature.write_bytes(b"done\r\n")
        self.assertTrue(implementation_matches(self.repo, sha, ["feature.txt"]))

    def test_report_edit_after_completion_cannot_reuse_saved_review(self):
        self.runner().run()
        before = list(self.calls)
        changed = self.report()
        changed["review"]["author"]["name"] = "Otro autor"
        write_review(self.artifacts / "REVISION.md", changed)
        with self.assertRaisesRegex(Blocked, "evidencia"):
            self.runner().run()
        self.assertEqual(self.calls, before)
        self.assert_unclosed_reviews()

    def test_correction_in_review_gets_one_fresh_verification_and_review(self):
        self.mode = "review-correction"
        result = self.runner().run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            set(result["completed"]), {"plan", "tasks", "build", "verify", "review"}
        )
        self.assertEqual(self.calls.count("build"), 1)
        self.assertEqual(self.calls.count("verify"), 2)
        self.assertEqual(self.calls.count("review"), 2)
        for phase in ("verify", "review"):
            validate_record(self.report(), phase, self.repo, {"R1"}, self.tasks())

    def test_repeated_correction_blocks_with_recoverable_review_phases(self):
        self.mode = "repeated-review-correction"
        with self.assertRaisesRegex(Blocked, "volvió a corregir"):
            self.runner().run()
        self.assert_unclosed_reviews()
        self.assertEqual(self.calls.count("verify"), 2)
        self.mode = "normal"
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(self.calls.count("build"), 1)
        self.assertEqual(self.calls.count("verify"), 3)

    def test_checkpoint_resume_does_not_repeat_verified_build(self):
        self.mode = "checkpoint"
        with self.assertRaises(Blocked):
            self.runner().run()
        self.assertEqual(self.state()["checkpoint"], "T1")
        self.mode = "normal"
        self.assertEqual(self.runner().run(acknowledge=True)["status"], "completed")
        self.assertEqual(self.calls.count("build"), 1)

    def test_interrupted_commit_recovers_without_reimplementing(self):
        self.mode = "crash-before-commit"
        with self.assertRaises(WorkflowError):
            self.runner().run()
        self.mode = "normal"
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(self.calls.count("build"), 1)

    def test_review_acceptance_failure_requires_new_verification_after_rebuild(self):
        self.mode = "review-regression"
        with self.assertRaises(WorkflowError):
            self.runner().run()
        self.mode = "normal"
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(self.calls.count("verify"), 2)
        self.assertEqual(self.calls.count("review"), 2)
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")

    def test_completed_resume_keeps_closed_evidence_and_makes_no_model_calls(self):
        self.runner().run()
        before = list(self.calls)
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertEqual(self.calls, before)

    def test_delivery_preserves_verified_code_and_records_implementation_sha(self):
        result = self.runner().run(publish=True)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["completed"], self.state()["completed_phases"])
        self.assertEqual(self.calls.count("publish"), 1)
        self.assertEqual(
            self.state()["publication_sha"],
            self.report()["review"]["implementation_sha"],
        )
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")

    def test_rebuild_clears_previous_publication_sha_when_delivery_is_invalidated(self):
        self.runner().run(publish=True)
        old_sha = self.state()["publication_sha"]
        (self.repo / "feature.txt").write_text("done\n", encoding="utf-8")
        self.assertEqual(self.runner().run()["status"], "completed")
        self.assertNotIn("publish", self.state()["completed_phases"])
        self.assertNotIn("publication_sha", self.state())
        self.assertFalse(implementation_matches(self.repo, old_sha, ["feature.txt"]))

    def test_delivery_must_include_the_reviewed_implementation_sha(self):
        self.mode = "delivery-wrong-sha"
        with self.assertRaisesRegex(Blocked, "SHA"):
            self.runner().run(publish=True)
        self.assertNotIn("publish", self.state()["completed_phases"])
        self.mode = "normal"
        self.assertEqual(self.runner().run(publish=True)["status"], "completed")
        self.assertEqual(self.calls.count("review"), 1)

    def test_closed_delivery_edit_invalidates_only_publish_and_can_resume(self):
        self.runner().run(publish=True)
        before = list(self.calls)
        delivery = self.artifacts / "ENTREGA.md"
        delivery.write_text(
            delivery.read_text(encoding="utf-8") + "Alterada.\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(Blocked, "entrega cerrada"):
            self.runner().run(publish=True)
        self.assertEqual(self.calls, before)
        self.assertNotIn("publish", self.state()["completed_phases"])
        self.assertNotIn("publication_sha", self.state())
        self.assertNotIn("delivery_hash", self.state())
        self.assertTrue({"verify", "review"} <= set(self.state()["completed_phases"]))
        self.assertEqual(self.runner().run(publish=True)["status"], "completed")
        self.assertEqual(self.calls.count("publish"), 2)
        self.assertEqual(self.calls.count("review"), 1)

    def test_uncommitted_code_mutation_during_delivery_invalidates_review(self):
        self.publish_effect = lambda: (self.repo / "feature.txt").write_text("broken")
        with self.assertRaisesRegex(Blocked, "solo puede escribir ENTREGA"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()
        self.assertEqual((self.repo / "feature.txt").read_text(), "broken")
        self.publish_effect = None
        self.assertEqual(self.runner().run(publish=True)["status"], "completed")
        self.assertEqual(self.calls.count("build"), 2)
        self.assertEqual(self.calls.count("verify"), 2)

    def test_committed_code_mutation_during_delivery_invalidates_review(self):
        def mutate():
            (self.repo / "feature.txt").write_text("broken")
            self.commit_paths("feature.txt")

        self.publish_effect = mutate
        with self.assertRaisesRegex(Blocked, "feature.txt"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()
        self.assertEqual(git(self.repo, "show", "HEAD:feature.txt"), "broken")

    def test_staged_code_mutation_and_worktree_restore_during_delivery_is_rejected(
        self,
    ):
        def mutate_stage_restore():
            feature = self.repo / "feature.txt"
            feature.write_text("broken", encoding="utf-8")
            git(self.repo, "add", "--", "feature.txt")
            feature.write_text("done", encoding="utf-8")

        self.publish_effect = mutate_stage_restore
        with self.assertRaisesRegex(Blocked, "feature.txt"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")
        self.assertEqual(git(self.repo, "show", ":feature.txt"), "broken")

    def test_committed_mutation_and_restore_during_delivery_is_still_rejected(self):
        def mutate_restore():
            (self.repo / "feature.txt").write_text("broken")
            self.commit_paths("feature.txt")
            (self.repo / "feature.txt").write_text("done")
            self.commit_paths("feature.txt")

        self.publish_effect = mutate_restore
        with self.assertRaisesRegex(Blocked, "feature.txt"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()
        self.assertEqual((self.repo / "feature.txt").read_text(), "done")
        self.publish_effect = None
        self.assertEqual(self.runner().run(publish=True)["status"], "completed")
        self.assertEqual(self.calls.count("build"), 1)
        self.assertEqual(self.calls.count("verify"), 2)

    def test_committed_closed_revision_mutation_during_delivery_is_rejected(self):
        def mutate():
            path = self.artifacts / "REVISION.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "Alterado.\n", encoding="utf-8"
            )
            self.commit_paths(path.relative_to(self.repo).as_posix())

        self.publish_effect = mutate
        with self.assertRaisesRegex(Blocked, "REVISION.md"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()

    def test_delivery_cannot_change_task_evidence_while_contract_stays_equal(self):
        def mutate():
            path = self.artifacts / "TAREAS.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    '"stdout": ""', '"stdout": "inventado"'
                ),
                encoding="utf-8",
            )

        self.publish_effect = mutate
        with self.assertRaisesRegex(Blocked, "TAREAS.md"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()

    def test_delivery_detects_writes_to_ignored_existing_files(self):
        (self.repo / ".gitignore").write_text("scratch.txt\n", encoding="utf-8")
        self.commit_paths(".gitignore")
        scratch = self.repo / "scratch.txt"
        scratch.write_text("conservado", encoding="utf-8")
        self.publish_effect = lambda: scratch.write_text("alterado", encoding="utf-8")
        with self.assertRaisesRegex(Blocked, "scratch.txt"):
            self.runner().run(publish=True)
        self.assert_unclosed_reviews()

    def lock_process(self, repo, slug):
        code = """import sys
from pathlib import Path
from gara_workflow.common import Blocked
from gara_workflow.runner import Runner, flow_lock
try:
    with flow_lock(Runner(Path(sys.argv[1]), sys.argv[2], 'codex').lock_path):
        print('acquired')
except Blocked:
    print('blocked')
    raise SystemExit(2)
"""
        return subprocess.run(
            [sys.executable, "-c", code, str(repo), slug],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def test_different_slugs_in_one_checkout_conflict_between_processes(self):
        first, second = self.runner(), self.runner("gar-123-second")
        self.assertNotEqual(first.runtime, second.runtime)
        self.assertEqual(first.lock_path, second.lock_path)
        with flow_lock(first.lock_path):
            child = self.lock_process(self.repo, "gar-123-second")
            self.assertEqual(child.returncode, 2, child.stderr)
            self.assertEqual(child.stdout.strip(), "blocked")
        released = self.lock_process(self.repo, "gar-123-second")
        self.assertEqual(released.returncode, 0, released.stderr)
        self.assertEqual(released.stdout.strip(), "acquired")

    def test_distinct_git_worktrees_can_lock_in_different_processes(self):
        linked = self.root / "other" / "gara"
        git(
            self.repo, "worktree", "add", "-b", "fixture/gar-123-secondary", str(linked)
        )
        first = self.runner()
        second = Runner(linked, self.slug, "codex")
        self.assertNotEqual(first.lock_path, second.lock_path)
        self.assertNotEqual(first.runtime, second.runtime)
        with flow_lock(first.lock_path):
            child = self.lock_process(linked, self.slug)
            self.assertEqual(child.returncode, 0, child.stderr)
            self.assertEqual(child.stdout.strip(), "acquired")


if __name__ == "__main__":
    unittest.main()
