"""A published source clone works without the historical archive."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gara_workflow.common import ROOT, WorkflowError
from gara_workflow.packaging import validate


class PublishedBundle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-published-bundle-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "clone"
        self.source.mkdir()
        for name in ("catalog.json", "AGENTS.md"):
            shutil.copy2(ROOT / name, self.source / name)
        for name in (
            "gara_workflow",
            "skills",
            "roles",
            "profiles",
            "references",
            "scripts",
        ):
            shutil.copytree(
                ROOT / name,
                self.source / name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        self.catalog = json.loads(
            (self.source / "catalog.json").read_text(encoding="utf-8")
        )
        self.expected = {
            "status": "valid",
            "skills": len(self.catalog["skills"]),
            "agents": len(self.catalog["agents"]),
            "original_components": len(
                {row["original"] for row in self.catalog["mapping"]}
            ),
        }
        self.environment = {
            key: value for key, value in os.environ.items() if key != "PYTHONPATH"
        }
        self.environment.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")

    def command(self, script, *arguments, cwd=None):
        result = subprocess.run(
            [sys.executable, str(script), *map(str, arguments)],
            cwd=cwd or self.source,
            env=self.environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_fresh_source_validates_packages_installs_and_runs_its_own_helpers(self):
        script = self.source / "scripts/gara_workflow.py"
        home, distribution = self.base / "home", self.base / "dist"
        self.assertFalse((self.source / "export").exists())
        self.assertFalse((self.source / "export.zip").exists())
        self.assertEqual(json.loads(self.command(script, "validate")), self.expected)

        preview = json.loads(
            self.command(
                script, "install", "--engine", "both", "--home", home, "--dry-run"
            )
        )
        self.assertFalse(home.exists())
        self.assertFalse((self.source / ".build").exists())
        packaged = json.loads(
            self.command(script, "package", "--destination", distribution)
        )
        self.assertEqual(packaged["files"], len(preview["files"]))
        self.assertEqual(packaged["skills_per_engine"], self.expected["skills"])
        installed = json.loads(
            self.command(script, "install", "--engine", "both", "--home", home)
        )
        self.assertEqual(installed["files_changed"], preview["files_changed"])
        self.assertEqual(installed["files_managed"], len(preview["files"]))
        modules = {
            path.name: path.read_bytes()
            for path in (self.source / "gara_workflow").glob("*.py")
        }

        # Move the source away and prevent accidental use of globally installed clients.
        self.source.rename(self.base / "source-unavailable")
        config = self.base / "unavailable-clients.toml"
        config.write_text(
            '[codex]\nclient = "gara-fixture-unavailable-codex"\n'
            '[claude]\nclient = "gara-fixture-unavailable-claude"\n',
            encoding="utf-8",
        )
        for prefix in (".agents/skills", ".claude/skills"):
            for name in ("gara-workflow", "gara-workflow-health", "gara-pdf"):
                folder = home / prefix / name / "scripts"
                for module, content in modules.items():
                    self.assertEqual(
                        (folder / "gara_workflow" / module).read_bytes(), content
                    )
            workflow = home / prefix / "gara-workflow/scripts/gara_workflow.py"
            report = json.loads(
                self.command(workflow, "doctor", "--config", config, cwd=home)
            )
            self.assertEqual(set(report["engines"]), {"codex", "claude"})
            self.assertTrue(
                all(not engine["available"] for engine in report["engines"].values())
            )
            for helper in (
                "gara-workflow-health/scripts/health.py",
                "gara-pdf/scripts/build_pdf.py",
            ):
                self.assertIn(
                    "usage:", self.command(home / prefix / helper, "--help", cwd=home)
                )

    def test_optional_archive_keeps_inventory_count_and_requires_mapping_coverage(self):
        self.assertEqual(validate(self.source), self.expected)
        original = next(
            row["original"]
            for row in self.catalog["mapping"]
            if row["original"].startswith("agents/")
        )
        archived = self.source / "export" / original
        archived.parent.mkdir(parents=True)
        archived.write_text("# Ficha histórica temporal\n", encoding="utf-8")
        self.assertEqual(validate(self.source), self.expected)
        (archived.parent / "unmapped-fixture.md").write_text(
            "# Sin mapping\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(WorkflowError, "no cubre"):
            validate(self.source)


if __name__ == "__main__":
    unittest.main()
