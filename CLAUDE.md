# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`gara-skill` is a bundle of **Claude Code skills and agents** for the **Gara** product: 27 skills (`skills/`) and 10 agents (`agents/`). There is no runner, installer or catalog; the user drives every phase by hand (`/gara-spec` → `plan` → `tasks` → `build` → `verify` → `review` → `deliver`). The repo's own prose, skill text and commit messages are in Spanish; match that. `AGENTS.md` and `README.md` are authoritative for contributor rules; `AGENTS.md` is kept byte-for-byte unmodified (`-text -eol` in `.gitattributes`) and predates the manual rewrite, so don't edit or reformat it and treat its runner-specific parts as historical.

## Commands

Run from the repo root (Git Bash on Windows). The only code here is the helper scripts inside some skills.

```bash
bash scripts/check.sh                                          # frontmatter, reference copies, links, commit-helper cmp
py skills/gara-commit/scripts/test_gara_commit.py -v           # commit helper tests (skill copy)
py plugins/gara-commit/skills/commit/scripts/test_gara_commit.py -v   # same tests (plugin copy)
.venv/Scripts/python -m ruff check . && .venv/Scripts/python -m ruff format --check .   # needs a venv with ruff
```

CI (`.github/workflows/test.yml`, Ubuntu and Windows, Python 3.12) runs `scripts/check.sh`, `compileall` and both commit test suites. Keep them green. On Windows use `py`, on macOS/Linux `python3`.

## Architecture

**Skills and agents are the source, in Claude Code's native format.** `skills/<name>/SKILL.md` has frontmatter `name` (must equal the folder, `gara-…`) and `description` (what it does and when to use it), plus `disable-model-invocation: true` for the explicit-only skills (the phase skills, `gara-commit`, `gara-find-skills`, research/design ones). `agents/<name>.md` has `name`, `description`, `model: inherit`, `tools` (omitted only for `gara-revisor-visual`, which inherits the browser MCP) and `disallowedTools: Agent`. `scripts/check.sh` enforces this.

**Shared files are copied into every skill.** Skills must be self-contained once copied to `~/.claude/skills`, so each `skills/<name>/references/` holds byte copies of `profiles/gara.md` (as `gara.md`) and, where the skill links them, `references/{flujo,artifacts,delegation,casos-de-uso}.md`. Edit the originals, then re-copy (loop in `README.md`); `scripts/check.sh` fails if a copy drifts. A skill that carries `flujo.md` must carry `artifacts.md` too, and one with `casos-de-uso.md` must carry `delegation.md`. `references/casos-de-uso.md` is the user-facing guide of which skills/agents to use per kind of work; update it when adding or removing a skill or agent.

**Manual-control contract** (`references/flujo.md`, `references/artifacts.md`): one phase per invocation and then stop with a summary; approval, commits (via `gara-commit`), push/PR and Linear changes only on explicit user order; no hidden state, everything lives in `specs/<slug>/` of the *target* Gara checkout (`SPEC.md` with `approved: true`, `PLAN.md`, `TAREAS.md`, `REVISION.md`, `ENTREGA.md`, all plain Markdown). `references/delegation.md` is the matrix of which skill may delegate to which agent; delegation is conditional and agents never launch other agents. Agent identity in a report does not prove independent review.

**Commit helper is duplicated on purpose.** `skills/gara-commit/scripts/gara_commit.py` (+ its test) and `plugins/gara-commit/skills/commit/scripts/…` must stay byte-identical; `check.sh` uses `cmp`. Change one, copy to the other. The plugin is published via `.claude-plugin/marketplace.json` (marketplace `gara-tools`). Commits in this repo must go through the `gara-commit` format: short title plus `PORQUÉ`, `CÓMO`, `DOCUMENTACIÓN` sections.

`gara-pdf` is self-contained: `scripts/build_pdf.py` imports `scripts/pdf.py` and needs a local Chrome/Chromium/Edge.

## Conventions and gotchas

- Ruff (`pyproject.toml`) is the only linter/formatter: line length 88, rules `E4,E7,E9,F`. It excludes `export`, `skills/gara-commit`, `plugins/gara-commit` and `skills/gara-ui-animation` (preserved third-party/original code), so don't reformat those. Preserve licenses and `docs/provenance.md` when touching imported skills (`gara-frontend-design`, `gara-ui-animation`, `gara-pdf` fonts).
- `export.zip`, `export/`, `logs/`, `output/` are local-only (git-ignored) leftovers of the original conversion.
- Gara's own stack (React/Vite/TS, Zustand, FastAPI) appears only in skill text and `profiles/gara.md` as guidance for the target checkout; there is no application code here. Don't freeze inventories, Linear states or commands in that text: the target checkout's own instructions prevail.
- Adding or removing a skill/agent means: the folder or file with correct frontmatter, a row in the `references/delegation.md` matrix, the counts in `README.md` (27 skills, 10 agents), and re-copying the references. `docs/audit/` and `docs/migration.md` describe the earlier runner-based version and are historical.
