# Project conventions for local Python projects managed with uv

Use these conventions as the default operating policy.

These rules are opinionated on purpose.
They exist to keep local Python project work reproducible, project-local, and consistent.

## Core conventions

### 1. Use uv as the default project tool

For local Python projects, use `uv` as the default tool for:
- project initialization
- Python version selection
- dependency management
- virtual environment management
- project command execution

Do not default to:
- global package installation
- raw `pip install`
- routine use of system Python for project tasks

## 2. Keep project work local

Treat the local project directory as the scope of Python work.

Use project-local state such as:
- `pyproject.toml`
- `uv.lock`
- `.venv`
- `.python-version` when present

Do not move routine project work into the global interpreter.

## 3. Initialize projects with uv

For new projects, prefer:
- `uv init`

This creates a project structure centered on `pyproject.toml`, which becomes the main source of project metadata.

## 4. Commit the lockfile

Treat `uv.lock` as part of the repository state.

Default rule:
- commit `uv.lock` to version control

Reason:
- it improves reproducibility across machines and across time

Do not treat the lockfile as disposable local noise in a normal project workflow.

## 5. Keep `.venv` out of version control

Treat `.venv` as local machine state.

Default rule:
- add `.venv` to `.gitignore`

The environment should be reproducible from project metadata and lock state, not committed directly.

## 6. Separate runtime and development dependencies

When a dependency is required by the application itself:
- add it as a normal project dependency

When a dependency is only needed for development:
- add it as a dev dependency

Examples of dev-only tools:
- pytest
- ruff
- mypy
- black

Do not mix runtime dependencies and developer tooling casually.

## 7. Prefer uv-managed Python versions

When choosing a Python version for a project:
- prefer uv-managed Python
- pin the version when appropriate

Typical actions:
- install Python through uv if needed
- pin the chosen version for project consistency

Do not silently rely on whatever system Python happens to be available.

## 8. Prefer uv run for project execution

For project-local execution, prefer:
- `uv run ...`

Use it for:
- scripts
- tests
- linters
- formatters
- migrations
- project CLI commands

Do not default to raw:
- `python`
- `pytest`
- `ruff`
- `mypy`

if those commands belong to the project environment.

## 9. Use dependency commands that reflect project intent

Use the project workflow for project dependencies.

Typical examples:
- add dependency -> `uv add`
- add dev dependency -> `uv add --dev`
- remove dependency -> `uv remove`
- sync environment -> `uv sync`

Do not use `pip install` as the normal path inside a uv-managed project.

## 10. Avoid manual lockfile editing

Lock-related files are part of dependency state.
Do not edit them manually.

If dependency state changes:
- update the project through uv workflows
- sync the environment through uv workflows

## 11. Do not require manual venv activation for normal agent work

For ordinary agent-driven tasks:
- do not require the user to activate `.venv`
- do not treat activation as a prerequisite for normal project commands

Prefer commands that work directly through uv.

Manual activation is acceptable only if the user explicitly wants an interactive shell workflow.

## 12. Distinguish project dependencies from one-off tools

Not every Python-based command belongs in project dependencies.

If a tool is only needed for a one-time or isolated action:
- prefer a non-project tool path

If the tool is part of the repository’s normal development workflow:
- keep it in dev dependencies

If the tool is part of runtime behavior:
- keep it in project dependencies

## 13. Migration should be explicit

When a repository currently uses:
- `requirements.txt`
- raw pip workflows
- unmanaged virtual environments
- older dependency managers

do not silently rewrite the workflow.

Instead:
- explain the detected state briefly
- propose migration to uv
- continue with uv-only conventions after migration is accepted

## 14. Safe default behavior

If the user does not specify otherwise, assume:

- this project should use uv
- project dependencies should remain project-local
- the environment should be reproducible
- system Python should not be the default execution path
- global installs should be avoided
- project commands should run through uv

## 15. Anti-patterns

Avoid these unless the user explicitly asks for them:

- global `pip install` for project packages
- routine use of system Python inside a managed local project
- mixing uv and unmanaged pip workflows without explanation
- treating `.venv` as a committed artifact
- skipping lockfile handling in a reproducible project setup
- adding unrelated one-off tools as runtime dependencies