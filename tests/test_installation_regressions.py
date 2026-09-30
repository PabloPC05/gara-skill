from __future__ import annotations

import copy
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from gara_workflow.common import WorkflowError, digest
from gara_workflow.packaging import build, frontmatter, header, install, validate


def snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def save_catalog(root: Path, catalog: dict) -> None:
    (root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")


def package_source(root: Path) -> dict:
    catalog = {"version": "1.2.3", "skills": [], "agents": [], "mapping": []}
    for name in ("gara-probe", "gara-extra"):
        folder = root / "skills" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            header({"name": name, "description": "Fixture de instalación."})
            + "# Fixture\n\nTrabaja con los datos temporales.\n",
            encoding="utf-8",
        )
        catalog["skills"].append(
            {"name": name, "title": "Fixture", "short": "Fixture temporal"}
        )
    helper = root / "skills/gara-probe/scripts/helper.py"
    helper.parent.mkdir()
    helper.write_text('print("fixture")\n', encoding="utf-8")
    profile = root / "profiles/gara.md"
    profile.parent.mkdir()
    profile.write_text("# Perfil temporal\n", encoding="utf-8")
    role = root / "roles/gara-probe.md"
    role.parent.mkdir()
    role.write_text("# Rol temporal\n", encoding="utf-8")
    catalog["agents"].append(
        {
            "name": "gara-probe",
            "description": "Rol fixture",
            "read_only": True,
            "claude_tools": "Read",
            "source": "roles/gara-probe.md",
        }
    )
    save_catalog(root, catalog)
    return catalog


def retire_components(root: Path, catalog: dict) -> None:
    catalog["agents"] = []
    catalog["skills"] = [catalog["skills"][0]]
    (root / "skills/gara-extra/SKILL.md").unlink()
    (root / "skills/gara-extra").rmdir()
    (root / "skills/gara-probe/scripts/helper.py").unlink()
    skill = root / "skills/gara-probe/SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\nActualizada.\n", encoding="utf-8"
    )
    save_catalog(root, catalog)


class InstallationRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-install-regression-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.home = self.base / "home"
        self.catalog = package_source(self.source)

    def installation_manifest(self):
        return json.loads(
            (self.home / ".gara-workflow/installation.json").read_text(encoding="utf-8")
        )

    def test_retired_agents_skills_and_helpers_are_removed_by_hash(self):
        install(self.source, self.home, "both")
        foreign = self.home / ".claude/skills/gara-extra/notes.txt"
        foreign.write_text("Contenido ajeno.\n", encoding="utf-8")
        retire_components(self.source, self.catalog)

        result = install(self.source, self.home, "both")

        for prefix, extension in ((".codex", "toml"), (".claude", "md")):
            self.assertFalse(
                (self.home / f"{prefix}/agents/gara-probe.{extension}").exists()
            )
        for prefix in (".agents", ".claude"):
            self.assertFalse(
                (self.home / f"{prefix}/skills/gara-extra/SKILL.md").exists()
            )
            self.assertFalse(
                (self.home / f"{prefix}/skills/gara-probe/scripts/helper.py").exists()
            )
        self.assertFalse((self.home / ".agents/skills/gara-extra").exists())
        self.assertEqual(foreign.read_text(encoding="utf-8"), "Contenido ajeno.\n")
        self.assertGreater(result["files_removed"], 0)
        self.assertFalse(
            any("gara-extra/" in name for name in self.installation_manifest()["files"])
        )

    def test_renamed_agents_skills_and_helpers_replace_the_old_names(self):
        install(self.source, self.home, "both")
        folder = self.source / "skills/gara-probe"
        folder.rename(self.source / "skills/gara-renamed")
        folder = self.source / "skills/gara-renamed"
        fields, body = frontmatter(folder / "SKILL.md")
        fields["name"] = "gara-renamed"
        (folder / "SKILL.md").write_text(header(fields) + body, encoding="utf-8")
        (folder / "scripts/helper.py").rename(folder / "scripts/renamed.py")
        self.catalog["skills"][0]["name"] = "gara-renamed"
        self.catalog["agents"][0]["name"] = "gara-renamed"
        save_catalog(self.source, self.catalog)

        install(self.source, self.home, "both")

        for prefix, extension in ((".codex", "toml"), (".claude", "md")):
            self.assertFalse(
                (self.home / f"{prefix}/agents/gara-probe.{extension}").exists()
            )
            self.assertTrue(
                (self.home / f"{prefix}/agents/gara-renamed.{extension}").is_file()
            )
        for prefix in (".agents", ".claude"):
            self.assertFalse((self.home / f"{prefix}/skills/gara-probe").exists())
            self.assertTrue(
                (
                    self.home / f"{prefix}/skills/gara-renamed/scripts/renamed.py"
                ).is_file()
            )

    def test_case_only_helper_rename_preserves_the_new_payload_on_windows(self):
        install(self.source, self.home, "both")
        old = self.source / "skills/gara-probe/scripts/helper.py"
        renamed = old.with_name("Helper.py")
        old.rename(renamed)
        renamed.write_text('print("actualizada")\n', encoding="utf-8")
        before = snapshot(self.base)

        preview = install(self.source, self.home, "both", dry_run=True)

        self.assertEqual(snapshot(self.base), before)
        actual = install(self.source, self.home, "both")
        self.assertEqual(preview["files_changed"], actual["files_changed"])
        self.assertEqual(preview["files_removed"], actual["files_removed"])
        files = self.installation_manifest()["files"]
        for prefix in (".agents", ".claude"):
            name = f"{prefix}/skills/gara-probe/scripts/Helper.py"
            self.assertEqual((self.home / name).read_bytes(), renamed.read_bytes())
            self.assertIn(name, files)
            self.assertNotIn(f"{prefix}/skills/gara-probe/scripts/helper.py", files)

    def test_partial_update_preserves_other_engine_files_and_manifest_entries(self):
        install(self.source, self.home, "both")
        edited = self.home / ".claude/skills/gara-extra/SKILL.md"
        edited.write_text("Modificación local del otro motor.\n", encoding="utf-8")
        claude_before = snapshot(self.home / ".claude")
        old_files = self.installation_manifest()["files"]
        retire_components(self.source, self.catalog)

        install(self.source, self.home, "codex")

        self.assertEqual(snapshot(self.home / ".claude"), claude_before)
        files = self.installation_manifest()["files"]
        self.assertEqual(
            {
                name: value
                for name, value in files.items()
                if name.startswith(".claude/")
            },
            {
                name: value
                for name, value in old_files.items()
                if name.startswith(".claude/")
            },
        )
        self.assertFalse((self.home / ".codex/agents/gara-probe.toml").exists())
        with self.assertRaisesRegex(WorkflowError, "obsoletos editados"):
            install(self.source, self.home, "claude")

    def test_edits_to_each_retired_component_block_before_build_or_install_writes(self):
        for relative in (
            ".claude/agents/gara-probe.md",
            ".claude/skills/gara-extra/SKILL.md",
            ".claude/skills/gara-probe/scripts/helper.py",
        ):
            with self.subTest(relative=relative):
                case = self.base / str(len(relative))
                source, home = case / "source", case / "home"
                catalog = package_source(source)
                install(source, home, "both")
                (home / relative).write_text("Edición local.\n", encoding="utf-8")
                retire_components(source, catalog)
                before = snapshot(case)
                for dry_run in (True, False):
                    with self.assertRaisesRegex(WorkflowError, "obsoletos editados"):
                        install(source, home, "both", dry_run=dry_run)
                    self.assertEqual(snapshot(case), before)

    def test_dry_run_computes_exact_payload_without_creating_build_or_home(self):
        before = snapshot(self.source)

        preview = install(self.source, self.home, "both", dry_run=True)

        self.assertFalse(self.home.exists())
        self.assertFalse((self.source / ".build").exists())
        self.assertEqual(snapshot(self.source), before)
        actual = install(self.source, self.home, "both")
        files = self.installation_manifest()["files"]
        self.assertEqual(preview["files"], sorted(files))
        self.assertEqual(preview["files_to_write"], sorted(files))
        for name, expected in files.items():
            self.assertEqual(digest(self.home / name), expected)
        for name in ("files_changed", "files_removed", "files_managed"):
            self.assertEqual(preview[name], actual[name])
        self.assertEqual(self.installation_manifest()["version"], "1.2.3")

    def test_dry_run_and_real_install_report_the_same_collision_without_writes(self):
        target = self.home / ".claude/agents/gara-probe.md"
        target.parent.mkdir(parents=True)
        target.write_text("Archivo ajeno.\n", encoding="utf-8")
        before = snapshot(self.base)
        errors = []
        for dry_run in (True, False):
            with self.assertRaises(WorkflowError) as caught:
                install(self.source, self.home, "both", dry_run=dry_run)
            errors.append(str(caught.exception))
            self.assertEqual(snapshot(self.base), before)
        self.assertEqual(errors[0], errors[1])
        self.assertFalse((self.source / ".build").exists())

    def test_dry_run_distinguishes_obsolete_entries_from_existing_removals(self):
        install(self.source, self.home, "both")
        missing = ".claude/agents/gara-probe.md"
        (self.home / missing).unlink()
        retire_components(self.source, self.catalog)
        before = snapshot(self.base)

        preview = install(self.source, self.home, "claude", dry_run=True)

        self.assertIn(missing, preview["files_obsolete"])
        self.assertNotIn(missing, preview["files_to_remove"])
        self.assertEqual(snapshot(self.base), before)
        actual = install(self.source, self.home, "claude")
        self.assertEqual(preview["files_changed"], actual["files_changed"])
        self.assertEqual(preview["files_removed"], actual["files_removed"])
        self.assertFalse(
            set(preview["files_obsolete"])
            & self.installation_manifest()["files"].keys()
        )

    def test_non_directory_parent_is_detected_before_any_install_or_build_writes(self):
        target = self.home / ".claude/agents"
        target.parent.mkdir(parents=True)
        target.write_text("Archivo ajeno.\n", encoding="utf-8")
        before = snapshot(self.base)
        for dry_run in (True, False):
            with self.assertRaises(WorkflowError):
                install(self.source, self.home, "both", dry_run=dry_run)
            self.assertEqual(snapshot(self.base), before)

    def test_unknown_managed_entries_legacy_commit_and_global_configuration_are_preserved(
        self,
    ):
        install(self.source, self.home, "both")
        paths = (
            ".other/owned.txt",
            ".codex/skills/gara-commit/SKILL.md",
            ".codex/config.toml",
            ".claude/settings.json",
        )
        manifest = self.installation_manifest()
        for name in paths:
            path = self.home / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Configuración ajena.\n", encoding="utf-8")
        for name in paths[:2]:
            manifest["files"][name] = digest(self.home / name)
        (self.home / ".gara-workflow/installation.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        retire_components(self.source, self.catalog)

        install(self.source, self.home, "both")

        for name in paths:
            self.assertEqual(
                (self.home / name).read_text(encoding="utf-8"), "Configuración ajena.\n"
            )
        for name in paths[:2]:
            self.assertEqual(
                self.installation_manifest()["files"][name], manifest["files"][name]
            )

    def test_build_preflight_protects_modified_obsolete_files(self):
        destination = self.base / "dist"
        build(self.source, destination)
        (destination / "claude/agents/gara-probe.md").write_text(
            "Edición local.\n", encoding="utf-8"
        )
        retire_components(self.source, self.catalog)
        before = snapshot(self.base)

        with self.assertRaisesRegex(WorkflowError, "obsoletos editados"):
            build(self.source, destination)

        self.assertEqual(snapshot(self.base), before)

    def test_install_dry_run_preserves_build_edit_protection(self):
        build(self.source, self.source / ".build")
        (self.source / ".build/claude/agents/gara-probe.md").write_text(
            "Edición local.\n", encoding="utf-8"
        )
        before = snapshot(self.base)
        for dry_run in (True, False):
            with self.assertRaises(WorkflowError):
                install(self.source, self.home, "both", dry_run=dry_run)
            self.assertEqual(snapshot(self.base), before)
        self.assertFalse(self.home.exists())

    def test_extra_foreign_build_files_are_preserved_without_being_installed(self):
        build(self.source, self.source / ".build")
        foreign = self.source / ".build/claude/skills/gara-probe/foreign.txt"
        foreign.write_text("Archivo ajeno.\n", encoding="utf-8")

        install(self.source, self.home, "claude")

        self.assertEqual(foreign.read_text(encoding="utf-8"), "Archivo ajeno.\n")
        self.assertFalse((self.home / ".claude/skills/gara-probe/foreign.txt").exists())


class CatalogContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gara-catalog-regression-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.catalog = package_source(self.source)

    def test_minimal_legacy_catalog_still_validates(self):
        self.assertEqual(validate(self.source)["skills"], 2)

    def test_declared_execution_modes_and_agent_references_validate(self):
        self.catalog["skills"][0].update(execution="coordinated", agents=["gara-probe"])
        self.catalog["skills"][1].update(execution="direct", agents=[])
        save_catalog(self.source, self.catalog)
        self.assertEqual(validate(self.source)["agents"], 1)

    def test_invalid_or_contradictory_execution_contracts_are_rejected(self):
        for contract in (
            {"execution": "direct", "agents": ["gara-probe"]},
            {"execution": "coordinated", "agents": []},
            {"execution": "coordinated", "agents": ["gara-missing"]},
            {"execution": "coordinated", "agents": ["gara-probe", "gara-probe"]},
            {"execution": "coordinated", "agents": [1]},
            {"execution": ["direct"], "agents": []},
            {"execution": "direct"},
            {"agents": []},
        ):
            with self.subTest(contract=contract):
                catalog = copy.deepcopy(self.catalog)
                catalog["skills"][0].update(contract)
                save_catalog(self.source, catalog)
                with self.assertRaises(WorkflowError):
                    validate(self.source)

    def test_duplicate_or_invalid_agent_names_are_rejected(self):
        for name in ("gara-probe", "../foreign", "gara-Foreign", "gara-" + "a" * 65):
            with self.subTest(name=name):
                catalog = copy.deepcopy(self.catalog)
                role = copy.deepcopy(catalog["agents"][0])
                role["name"] = name
                catalog["agents"].append(role)
                save_catalog(self.source, catalog)
                with self.assertRaises(WorkflowError):
                    validate(self.source)

    def test_invalid_or_contradictory_claude_capabilities_are_rejected(self):
        for fields in (
            {"claude_tools": ["Read"]},
            {"claude_tools": ""},
            {"claude_disallowed_tools": None},
            {"claude_disallowed_tools": [1]},
            {"claude_disallowed_tools": {"Agent": True}},
            {"claude_disallowed_tools": "Read"},
        ):
            with self.subTest(fields=fields):
                catalog = copy.deepcopy(self.catalog)
                catalog["agents"][0].update(fields)
                save_catalog(self.source, catalog)
                with self.assertRaises(WorkflowError):
                    validate(self.source)

    def test_null_claude_tools_inherit_capabilities_and_denials_are_native(self):
        for denied in ("Agent", ["Agent", "Task"]):
            with self.subTest(denied=denied):
                self.catalog["agents"][0].update(
                    claude_tools=None, claude_disallowed_tools=denied
                )
                save_catalog(self.source, self.catalog)
                destination = self.base / (
                    "string" if isinstance(denied, str) else "list"
                )

                build(self.source, destination)

                fields, _ = frontmatter(destination / "claude/agents/gara-probe.md")
                self.assertNotIn("tools", fields)
                self.assertEqual(fields["model"], "inherit")
                self.assertEqual(fields["disallowedTools"], denied)
                self.assertNotIn("permissionMode", fields)
                codex = tomllib.loads(
                    (destination / "codex/agents/gara-probe.toml").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertNotIn("model", codex)
                self.assertEqual(codex["sandbox_mode"], "read-only")

    def test_shared_delegation_reference_is_refreshed_in_each_native_payload(self):
        references = self.source / "references"
        references.mkdir()
        copies = self.source / "skills/gara-probe/references"
        copies.mkdir()
        for name in ("artifacts.md", "runtime.md", "delegation.md"):
            (references / name).write_text(f"# Fuente {name}\n", encoding="utf-8")
            (copies / name).write_text("# Copia antigua\n", encoding="utf-8")
        destination = self.base / "dist"

        build(self.source, destination)

        for engine in ("codex", "claude"):
            for name in ("artifacts.md", "runtime.md", "delegation.md"):
                self.assertEqual(
                    (
                        destination / engine / "skills/gara-probe/references" / name
                    ).read_bytes(),
                    (references / name).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
