# Repository Guidelines

## Project Structure & Module Organization

`gara-skill` currently has no source files, tests, assets, or package manifests. Keep `AGENTS.md` at the root. When adding implementation, group related code by responsibility; keep tests near their modules or in a clearly named `tests/` directory. Add a `README.md` describing new directories and setup requirements.

## Build, Test, and Development Commands

No build, test, lint, or local development commands are configured. When selecting a toolchain, add reproducible commands to its configuration and document exact invocations in `README.md`. Verify commands from the repository root before listing them as supported. Avoid dependencies that do not serve the implementation.

## Coding Style & Naming Conventions

For Markdown, use descriptive headings, short paragraphs, fenced code examples with language labels, and relative links. Keep filenames meaningful and consistent within each component. For new code, choose the language's standard formatter and linter, commit their configuration, and follow their indentation rules. Avoid introducing competing style conventions.

## Testing Guidelines

No testing framework or coverage threshold is defined. Introduce tests alongside behavior changes and document how to run them. Name tests after the behavior and expected result; include edge cases and regressions when applicable. For documentation changes, check paths, commands, and Markdown rendering.

## Commit & Pull Request Guidelines

There is no `.git` directory or commit history to establish existing conventions. If Git is initialized, use focused, imperative commits such as `docs: add contributor guide`. Keep each commit limited to one logical change.

Pull requests should explain the change, reference relevant issues, and list validation performed. Include screenshots for visible interface changes. If validation cannot run, state the reason.

## Security & Configuration

Never commit secrets or machine-specific credentials. When configuration is introduced, document required variables and provide example values without sensitive information.
