from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("gara_commit.py")


class GaraCommitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "gara"
        self.root.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("config", "user.name", "Gara Test")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def stage(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.run_git("add", relative)

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(self.root),
                "--title",
                "Actualiza comportamiento",
                "--why",
                "El cambio resuelve una limitacion funcional comprobada.",
                "--how",
                "Modifica el elemento necesario para cubrir el caso.",
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_infers_docs_type_and_builds_narrative(self) -> None:
        self.stage("README.md", "# Gara\nDetalle nuevo\n")
        process = self.invoke("--dry-run")
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn("docs: Actualiza comportamiento", process.stdout)
        self.assertIn("- README.md", process.stdout)

    def test_requires_semantic_type_for_source_code(self) -> None:
        self.stage("backend/src/utils/state.js", "export const state = 'READY';\n")
        process = self.invoke("--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("indique --type", process.stderr)

    def test_blocks_source_mixed_with_styles(self) -> None:
        self.stage("frontend/src/App.tsx", "export const App = () => null;\n")
        self.stage("frontend/src/index.css", "body { color: red; }\n")
        process = self.invoke("--type", "feat", "--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("mezcla logica funcional con estilos", process.stderr)

    def test_requires_docs_for_api_change(self) -> None:
        self.stage("backend/src/routes/jobs.js", "router.post('/jobs', handler);\n")
        process = self.invoke("--type", "feat", "--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("API publica", process.stderr)

    def test_requires_docs_for_environment_variable_change(self) -> None:
        self.stage("backend/src/config.js", "export const port = process.env.PORT;\n")
        process = self.invoke("--type", "feat", "--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("variables de entorno", process.stderr)

    def test_new_test_does_not_make_component_edit_architectural(self) -> None:
        self.stage("frontend/src/components/Viewer.tsx", "export function Viewer() { return null; }\n")
        self.run_git("commit", "-q", "-m", "baseline")
        self.stage("frontend/src/components/Viewer.tsx", "export function Viewer() { return <main />; }\n")
        self.stage("frontend/src/test/Viewer.test.tsx", "test('renders', () => true);\n")
        process = self.invoke("--type", "fix", "--dry-run")
        self.assertEqual(0, process.returncode, process.stderr)

    def test_requires_docs_for_new_architecture_module(self) -> None:
        self.stage("frontend/src/components/NewPanel.tsx", "export function NewPanel() { return null; }\n")
        process = self.invoke("--type", "feat", "--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("arquitectura", process.stderr)

    def test_commits_api_change_with_staged_documentation(self) -> None:
        self.stage("backend/src/routes/jobs.js", "router.post('/jobs', handler);\n")
        self.stage("README.md", "# Gara\nPOST /jobs\n")
        process = self.invoke("--type", "feat")
        self.assertEqual(0, process.returncode, process.stderr)
        message = self.run_git("log", "-1", "--pretty=%B").stdout
        self.assertIn("feat: Actualiza comportamiento", message)
        self.assertIn("PORQUÉ:", message)
        self.assertIn("CÓMO:", message)
        self.assertIn("DOCUMENTACIÓN:\n- README.md", message)

    def test_rejects_repository_not_named_gara(self) -> None:
        other = Path(self.temporary.name) / "otro-proyecto"
        self.root.rename(other)
        self.root = other
        self.stage("README.md", "# Fuera\n")
        process = self.invoke("--dry-run")
        self.assertEqual(2, process.returncode)
        self.assertIn("repositorio 'gara'", process.stderr)


if __name__ == "__main__":
    unittest.main()
