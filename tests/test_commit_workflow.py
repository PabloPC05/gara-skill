from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/gara-commit"
PLUGIN = ROOT / "plugins/gara-commit/skills/commit"
HELPERS = (SKILL / "scripts/gara_commit.py", PLUGIN / "scripts/gara_commit.py")


class CommitWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.sequence = 0

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(
        self, repo: Path, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )

    def repository(self, name: str, origin: str = "") -> Path:
        self.sequence += 1
        repo = self.base / str(self.sequence) / name
        repo.mkdir(parents=True)
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "Gara Test")
        self.git(repo, "config", "user.email", "test@example.com")
        self.git(repo, "config", "commit.gpgSign", "false")
        hooks = repo / ".git" / "fixture-hooks"
        hooks.mkdir()
        self.git(repo, "config", "core.hooksPath", str(hooks))
        if origin:
            self.git(repo, "remote", "add", "origin", origin)
        return repo

    def stage(self, repo: Path, relative: str, content: str) -> None:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.git(repo, "add", "--", relative)

    def invoke(
        self, helper: Path, repo: Path, *args: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                str(helper),
                "--repo",
                str(repo),
                "--title",
                "Registra cambio validado",
                "--why",
                "El cambio resuelve una limitación comprobada del proyecto.",
                "--how",
                "Modifica únicamente el comportamiento de la tarea y lo verifica.",
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def assert_no_commit(self, repo: Path) -> None:
        self.assertNotEqual(
            0, self.git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode
        )

    def test_named_repositories_validate_and_create_narrative_commits(self) -> None:
        for helper in HELPERS:
            for name in ("gara", "gara-skill"):
                with self.subTest(helper=helper, name=name):
                    repo = self.repository(name)
                    self.stage(repo, "README.md", "# Proyecto\nDetalle actualizado.\n")
                    preview = self.invoke(helper, repo, "--dry-run")
                    self.assertEqual(0, preview.returncode, preview.stderr)
                    self.assert_no_commit(repo)
                    committed = self.invoke(helper, repo)
                    self.assertEqual(0, committed.returncode, committed.stderr)
                    message = self.git(repo, "log", "-1", "--pretty=%B").stdout
                    self.assertIn("docs: Registra cambio validado", message)
                    self.assertIn("PORQUÉ:", message)
                    self.assertIn("CÓMO:", message)
                    self.assertIn("DOCUMENTACIÓN:\n- README.md", message)
                    self.assertEqual("", self.git(repo, "diff", "--cached").stdout)

    def test_renamed_checkouts_accept_exact_gara_or_gara_skill_origin(self) -> None:
        origins = (
            "https://github.com/PabloPC05/gara.git",
            "git@github.com:PabloPC05/gara-skill.git",
            "https://github.com/PabloPC05/gara-skill/",
        )
        for helper in HELPERS:
            for origin in origins:
                with self.subTest(helper=helper, origin=origin):
                    repo = self.repository("checkout-local", origin)
                    self.stage(repo, "README.md", "# Proyecto\n")
                    nested = repo / "subdirectorio"
                    nested.mkdir()
                    preview = self.invoke(helper, nested, "--dry-run")
                    self.assertEqual(0, preview.returncode, preview.stderr)
                    self.assert_no_commit(repo)

    def test_other_repository_names_and_origin_suffixes_are_rejected(self) -> None:
        cases = (
            ("otro-proyecto", ""),
            ("gara-skill-extra", ""),
            ("checkout-local", "https://github.com/PabloPC05/gara-skill-extra.git"),
            ("checkout-local", "https://github.com/PabloPC05/otra-gara.git"),
        )
        for helper in HELPERS:
            for name, origin in cases:
                with self.subTest(helper=helper, name=name, origin=origin):
                    repo = self.repository(name, origin)
                    self.stage(repo, "README.md", "# Fuera del alcance\n")
                    rejected = self.invoke(helper, repo)
                    self.assertEqual(2, rejected.returncode, rejected.stderr)
                    self.assertIn("repositorio 'gara-skill'", rejected.stderr)
                    self.assert_no_commit(repo)

    def test_secondary_remote_does_not_authorize_another_repository(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper):
                repo = self.repository("otro-proyecto", "https://example.com/other.git")
                self.git(
                    repo,
                    "remote",
                    "add",
                    "upstream",
                    "https://github.com/PabloPC05/gara-skill.git",
                )
                self.stage(repo, "README.md", "# Fuera del alcance\n")
                rejected = self.invoke(helper, repo, "--dry-run")
                self.assertEqual(2, rejected.returncode, rejected.stderr)
                self.assert_no_commit(repo)

    def test_feature_requires_documentation_in_the_index(self) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper):
                repo = self.repository("gara-skill")
                self.stage(repo, "gara_workflow/domain.py", "VALUE = 1\n")
                documentation = repo / "notes" / "behavior.md"
                documentation.parent.mkdir()
                documentation.write_text("# Nueva funcionalidad\n", encoding="utf-8")
                rejected = self.invoke(helper, repo, "--type", "feat")
                self.assertEqual(2, rejected.returncode, rejected.stderr)
                self.assertIn("documentación", rejected.stderr)
                self.assert_no_commit(repo)
                self.git(repo, "add", "--", "notes/behavior.md")
                committed = self.invoke(helper, repo, "--type", "feat")
                self.assertEqual(0, committed.returncode, committed.stderr)
                message = self.git(repo, "log", "-1", "--pretty=%B").stdout
                self.assertIn("feat: Registra cambio validado", message)
                self.assertIn("DOCUMENTACIÓN:\n- notes/behavior.md", message)

    def test_rejected_mixed_staging_preserves_the_index_and_creates_no_commit(
        self,
    ) -> None:
        for helper in HELPERS:
            with self.subTest(helper=helper):
                repo = self.repository("gara-skill")
                self.stage(repo, "gara_workflow/domain.py", "VALUE = 1\n")
                self.stage(repo, "assets/theme.css", "body { color: red; }\n")
                self.stage(repo, "README.md", "# Cambio\n")
                before = self.git(repo, "diff", "--cached", "--binary").stdout
                rejected = self.invoke(helper, repo, "--type", "feat")
                self.assertEqual(2, rejected.returncode, rejected.stderr)
                self.assertIn("mezcla logica funcional con estilos", rejected.stderr)
                self.assertEqual(
                    before, self.git(repo, "diff", "--cached", "--binary").stdout
                )
                self.assert_no_commit(repo)

    def test_python_test_paths_infer_test_type_without_feature_documentation(
        self,
    ) -> None:
        paths = (
            "tests/test_state.py",
            "helpers/test_state.py",
            "src/test/State.test.ts",
        )
        for helper in HELPERS:
            for relative in paths:
                with self.subTest(helper=helper, path=relative):
                    repo = self.repository("gara-skill")
                    self.stage(repo, relative, "assert 1 == 1\n")
                    preview = self.invoke(helper, repo, "--dry-run")
                    self.assertEqual(0, preview.returncode, preview.stderr)
                    self.assertIn("test: Registra cambio validado", preview.stdout)
                    self.assert_no_commit(repo)

    def test_source_requires_semantic_intent_and_a_valid_title(self) -> None:
        cases = (
            (),
            ("--type", "chore"),
            ("--type", "fix", "--title", "titulo sin mayúscula"),
        )
        for helper in HELPERS:
            repo = self.repository("gara-skill")
            self.stage(repo, "gara_workflow/domain.py", "VALUE = 1\n")
            for args in cases:
                with self.subTest(helper=helper, args=args):
                    rejected = self.invoke(helper, repo, *args, "--dry-run")
                    self.assertEqual(2, rejected.returncode, rejected.stderr)
                    self.assert_no_commit(repo)
            preview = self.invoke(helper, repo, "--type", "fix", "--dry-run")
            self.assertEqual(0, preview.returncode, preview.stderr)

    def test_named_folder_without_git_is_rejected(self) -> None:
        repo = self.base / "gara-skill"
        repo.mkdir()
        for helper in HELPERS:
            with self.subTest(helper=helper):
                rejected = self.invoke(helper, repo, "--dry-run")
                self.assertEqual(2, rejected.returncode, rejected.stderr)
                self.assertIn("repositorio Git", rejected.stderr)
                self.assertFalse((repo / ".git").exists())

    def test_skill_and_self_contained_plugin_keep_one_commit_policy(self) -> None:
        for relative in (
            "scripts/gara_commit.py",
            "scripts/test_gara_commit.py",
            "references/policy.md",
        ):
            with self.subTest(path=relative):
                self.assertEqual(
                    (SKILL / relative).read_bytes(), (PLUGIN / relative).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
