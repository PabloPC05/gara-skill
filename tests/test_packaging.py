from __future__ import annotations

import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from gara_workflow.common import ROOT, WorkflowError, digest
from gara_workflow.packaging import build, frontmatter, install, validate
from gara_workflow.pdf import document


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-install-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        for name in ("catalog.json", "AGENTS.md"):
            shutil.copy2(ROOT / name, self.root / name)
        for name in (
            "skills",
            "roles",
            "profiles",
            "references",
            "gara_workflow",
        ):
            shutil.copytree(
                ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        if (ROOT / "export").is_dir():
            shutil.copytree(ROOT / "export", self.root / "export")

    def test_catalog_covers_export(self):
        self.assertEqual(
            validate(self.root),
            {"status": "valid", "skills": 29, "agents": 10, "original_components": 46},
        )

    def test_build_generates_native_metadata(self):
        target = self.home / "dist"
        build(self.root, target)
        role = tomllib.loads(
            (target / "codex/agents/gara-scout.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(role["name"], "gara-scout")
        self.assertEqual(role["sandbox_mode"], "read-only")
        self.assertNotIn("model", role)
        fields, _ = frontmatter(target / "claude/skills/gara-spec/SKILL.md")
        self.assertTrue(fields["disable-model-invocation"])
        fields, _ = frontmatter(target / "claude/agents/gara-implementer.md")
        self.assertEqual(fields["model"], "inherit")
        self.assertEqual(fields["disallowedTools"], "Agent")
        fields, _ = frontmatter(target / "claude/agents/gara-revisor-visual.md")
        self.assertNotIn("tools", fields)
        yaml = (target / "codex/skills/gara-spec/agents/openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("allow_implicit_invocation: false", yaml)
        self.assertIn("$gara-spec", yaml)
        self.assertEqual(
            (target / "codex/skills/gara-spec/references/gara.md").read_bytes(),
            (self.root / "profiles/gara.md").read_bytes(),
        )

    def test_both_installations_are_idempotent(self):
        first = install(self.root, self.home, "both")
        self.assertGreater(first["files_changed"], 0)
        second = install(self.root, self.home, "both")
        self.assertEqual(second["files_changed"], 0)
        self.assertTrue(
            (
                self.home
                / ".agents/skills/gara-workflow/scripts/gara_workflow/runner.py"
            ).is_file()
        )
        self.assertTrue(
            (self.home / ".claude/skills/gara-pdf/assets/fonts/OFL.txt").is_file()
        )

    def test_preserves_existing_codex_commit_skill(self):
        path = self.home / ".codex/skills/gara-commit/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Original del usuario.\n", encoding="utf-8")
        before = digest(path)
        result = install(self.root, self.home, "both")
        self.assertEqual(digest(path), before)
        self.assertIn(str(path), result["reused"])
        self.assertFalse((self.home / ".agents/skills/gara-commit").exists())
        self.assertTrue((self.home / ".claude/skills/gara-commit/SKILL.md").is_file())

    def test_collision_preflight_is_all_or_nothing(self):
        target = self.home / ".claude/agents/gara-scout.md"
        target.parent.mkdir(parents=True)
        target.write_text("Archivo ajeno.\n", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            install(self.root, self.home, "both")
        self.assertEqual(target.read_text(encoding="utf-8"), "Archivo ajeno.\n")
        self.assertFalse((self.home / ".agents").exists())

    def test_local_edits_are_not_overwritten(self):
        install(self.root, self.home, "codex")
        target = self.home / ".agents/skills/gara-spec/SKILL.md"
        target.write_text("Modificación local.\n", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            install(self.root, self.home, "codex")
        self.assertEqual(target.read_text(encoding="utf-8"), "Modificación local.\n")

    def test_dry_install_does_not_create_directories(self):
        target = self.home / "empty"
        result = install(self.root, target, "both", dry_run=True)
        self.assertEqual(result["status"], "dry-run")
        self.assertFalse(target.exists())
        self.assertFalse((self.root / ".build").exists())

    def test_bundled_helpers_do_not_require_source_checkout(self):
        import subprocess
        import sys

        install(self.root, self.home, "both")
        script = self.home / ".claude/skills/gara-workflow/scripts/gara_workflow.py"
        process = subprocess.run(
            [sys.executable, str(script), "doctor"],
            cwd=self.home,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(process.returncode, 0, process.stderr.decode(errors="replace"))
        self.assertIn("engines", json.loads(process.stdout))

    def test_build_protects_foreign_files(self):
        target = self.home / "dist/codex/agents/gara-scout.toml"
        target.parent.mkdir(parents=True)
        target.write_text("foreign", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            build(self.root, self.home / "dist")
        self.assertEqual(target.read_text(), "foreign")

    def test_existing_guidelines_are_preserved(self):
        before = digest(ROOT / "AGENTS.md")
        install(self.root, self.home, "both")
        self.assertEqual(digest(ROOT / "AGENTS.md"), before)


class Pdf(unittest.TestCase):
    def test_document_embeds_brand_fonts_and_escapes_metadata(self):
        body = document(
            "<h2>Análisis</h2>",
            {"title": '<script>alert("x")</script>'},
            ROOT / "skills/gara-pdf/assets",
        )
        self.assertIn("data:image/png;base64,", body)
        self.assertIn("data:font/ttf;base64,", body)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn("default-src 'none'", body)
        self.assertNotIn('<script>alert("x")</script>', body)

    def test_document_requires_real_title(self):
        with self.assertRaises(WorkflowError):
            document("<p>Contenido</p>", {}, ROOT / "skills/gara-pdf/assets")


if __name__ == "__main__":
    unittest.main()
