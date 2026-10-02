# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`gara-skill` is a development bundle for the **Gara** product, installable into both Codex and Claude Code. It ships 29 skills, 10 agent roles, and a Python runner (`gara_workflow/`) that drives the spec → plan → tasks → build → verify → review flow with real acceptance commands, per-spec state, and resume. The repo's own prose, skill text, and commit messages are in Spanish; match that. `AGENTS.md` and `README.md` are authoritative for contributor rules; `AGENTS.md` is kept byte-for-byte unmodified (`-text -eol` in `.gitattributes`), so don't edit or reformat it.

## Commands

Run from the repo root. Python 3.11+; the runtime uses only the standard library. On Windows use `py`, on macOS/Linux `python3`.

```powershell
py -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,validation]"   # ruff + PyYAML

py -m unittest discover -s tests -v                          # full suite (~10 min; spawns real git repos)
py -m unittest tests.test_packaging -v                       # one module
py -m unittest tests.test_packaging.Packaging.test_catalog_covers_export -v   # one test
py skills/gara-commit/scripts/test_gara_commit.py -v         # commit helper tests (skill copy)
py plugins/gara-commit/skills/commit/scripts/test_gara_commit.py -v   # same tests (plugin copy)

py scripts/gara_workflow.py validate                         # catalog/skills/refs consistency
py scripts/gara_workflow.py package                          # generate .build/{codex,claude}
py scripts/gara_workflow.py install --engine both --dry-run  # preview install, writes nothing
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

CI (`.github/workflows/test.yml`) runs, in order: `py_compile` + `cmp` of the commit helper copies, both commit test suites, ruff check/format, `validate`, then the unittest suite. Keep all of these green.

Other subcommands of `scripts/gara_workflow.py`: `doctor`, `run`, `resume`, `status`, `metrics`, `fixes`, `sessions`, `watch`. `run` requires a target Gara checkout on a `GAR-N` branch with an approved SPEC; use `--dry-run` when testing. Exit codes: 0 success/dry-run, 2 blocked, 1 failure, 130 interrupted.

## Architecture

**Single source, generated distributions.** `catalog.json` is the inventory: every skill (`name`, `execution: direct|coordinated`, `agents`, `explicit_only`) and every role (`source`, `claude_tools`, `read_only`, …), plus a `mapping` to the 46 components of the original `export.zip`. `gara_workflow/packaging.py` validates the catalog against `skills/*/SKILL.md` and `roles/*.md` (names match `gara-…`, frontmatter present, relative Markdown links resolve, bundled `.py` compiles, direct skills list no agents and coordinated ones list at least one) and then generates engine-native output in `.build/` (never edit it; it is git-ignored):

- Codex: skills with `agents/openai.yaml`, agents as `.toml`.
- Claude: skills (`disable-model-invocation` added for `explicit_only`), agents as `.md` with `model: inherit`.

`install` copies only files it registered (hash manifest), refuses to overwrite locally edited files, removes obsolete ones only if unmodified, and shares collision checks with `--dry-run`. `--home` redirects the target for tests.

**Shared files are copied into every skill.** Skills must be self-contained once installed, so each `skills/<name>/references/` holds byte copies of `profiles/gara.md` (as `gara.md`) and, where the skill links them, `references/{artifacts,runtime,delegation}.md`. The build regenerates the installed copies from the sources, but the checked-in ones are what a checkout reads, so keep them in sync by hand (`for d in skills/*/; do [ -f $d/references/runtime.md ] && cp references/runtime.md $d/references/; done`); `tests.test_packaging` fails if one drifts. `runtime.md` links `artifacts.md`, so a skill that carries one must carry both. Skills `gara-workflow`, `gara-pdf`, and `gara-workflow-health` also get a bundled copy of `gara_workflow/*.py` under `scripts/gara_workflow/` at build time, which is why their helper scripts are thin shims that prefer the bundled package and fall back to the checkout root.

**Runner (`gara_workflow/`).** `cli.py` dispatches subcommands; `runner.py` (`Runner`) executes phases against a target checkout; `engines.py` launches the Codex/Claude CLI as a subprocess, streams its JSON events, and records observed agent delegations; `reviews.py` validates structured verify/review evidence bound to the implementation SHA; `common.py` holds git helpers, atomic writes, secret redaction, and the SPEC/TAREAS parsers; `pdf.py` renders PDFs via a local Chrome/Edge; `health.py`/`utilities.py` back `doctor`, `fixes`, `sessions`, `watch`. Key invariants (see `references/runtime.md` and `references/artifacts.md` for the full contract):

- The coordinator runs acceptance commands itself; a model's claim never marks a task verified. Those commands are written by the model but run outside the client sandbox, so they get a minimal environment (`GATE_ENVIRONMENT` in `common.py`), a 3600 s timeout cap, and a human pause after `tasks` (checkpoint `tasks`, skipped with `--ack-checkpoint`; tests pass `confirm_contract=False` to `Runner`). New contracts must start every task as `pending`.
- `inside()` only guards `.git` (with Windows aliases like `.git.`/`GIT~1`) because the installer also uses it for `~/.codex` and `~/.claude`. Task contracts additionally forbid `.claude/`, `.codex/`, `.husky/` and `.env*` through `protected_part()` in `validate_tasks`.
- `redact()`/`redacted_tail()` scrub before truncating; extend its patterns when you persist a new kind of provider output. SIGTERM/SIGHUP become `KeyboardInterrupt` (exit 130) via `terminate_as_interrupt`; `reset --slug S --yes` deletes only the private runtime state.
- Artifacts live in `specs/<slug>/` of the *target* repo (`SPEC.md` with `approved: true`, `PLAN.md`, `TAREAS.md` with a `<!-- gara-tasks:v1 -->` JSON block); state, locks and summaries live in the target's private Git dir. One lock covers the whole checkout regardless of slug.
- Delivery is frozen: after verify/review, any change to code or closed artifacts invalidates the closure.
- Agent identity in a report does not prove independent review (`independence: unverified` is deliberate).

**Commit helper is duplicated on purpose.** `skills/gara-commit/scripts/gara_commit.py` (+ its test) and `plugins/gara-commit/skills/commit/scripts/…` must stay byte-identical; CI uses `cmp`. Change one, copy to the other. The plugin is published via `.claude-plugin/marketplace.json` (marketplace `gara-tools`). Commits in this repo must go through the `gara-commit` format: short title plus `PORQUÉ`, `CÓMO`, `DOCUMENTACIÓN` sections.

## Conventions and gotchas

- Ruff (`pyproject.toml`) is the only formatter/linter: 4-space indent, line length 88, rules `E4,E7,E9,F`. It excludes `export`, `.build`, `.venv`, `skills/gara-commit`, `plugins/gara-commit`, and `skills/gara-ui-animation` (preserved third-party/original code), so don't reformat those.
- `export.zip`, `export/`, `logs/`, `output/` are local-only (git-ignored). `validate` and the tests work without `export/`; if present it must be covered by the catalog `mapping`.
- Adding or renaming a skill/role means updating `catalog.json`, the skill directory, and `docs/migration.md`/README counts (29 skills, 10 roles, 8 coordinated / 21 direct); `validate` fails if catalog and `skills/` folders disagree. `scripts/adapt_export.py` was a one-time conversion and refuses to regenerate existing skills; edit the canonical sources directly.
- Tests use fake model clients (`tests/fixtures/fake_client.py`) and temporary git repos; no network, Linear, or real HPC jobs. Do not add tests that need credentials.
- Gara's own stack (React/Vite/TS, FastAPI) appears only in the skill text and `profiles/gara.md` as guidance for the target checkout; there is no frontend/backend code here.
- Preserve licenses and `docs/provenance.md` when touching imported skills (`gara-frontend-design`, `gara-ui-animation`, `gara-pdf` fonts).
