---
name: python-with-uv
description: enforce safe local python project workflows with uv. use when creating a new python project, entering an existing local repository, adding dependencies, running scripts, tests, linters, formatters, or migrations, or choosing a python version. check for uv, pyproject.toml, uv.lock, .venv, and project state before making changes. prefer uv-managed python, uv add, uv sync, and uv run over global installs, system python, or raw pip. if uv or python is missing, guide the user through installation or migration before continuing.
---

# Manage local Python projects with uv

Use this skill to keep local Python project work reproducible, project-local, and uv-managed.

This skill exists to prevent common failures such as:
- installing dependencies globally
- using the system Python for routine project work
- using raw `pip install` in a project that should be managed through `uv`
- guessing project state without checking files first
- running project commands outside the uv-managed environment

## Core policy

For local Python projects, treat `uv` as the default tool for:
- project initialization
- Python version management
- dependency management
- virtual environment management
- running project commands

Default behavior:
- avoid global installs
- avoid system Python for normal project tasks
- avoid raw `pip install` unless the user explicitly wants a non-uv workflow
- prefer `uv run` for project commands
- prefer `uv add` for project dependencies
- prefer `uv sync` for environment repair and alignment
- prefer uv-managed Python versions over arbitrary system interpreters

Always follow the operating policy in `references/project-conventions.md`.

## Required workflow

Before the first project-changing action, inspect the current directory and determine the correct next step.

Run:
`python scripts/check_uv_project.py`

Then run:
`python scripts/suggest_uv_next_step.py`

Use these results together with:
- `references/preflight.md`
- `references/decision-tree.md`
- `references/project-conventions.md`

Do not create a project, install dependencies, run repair steps, or execute Python project commands until the project state is known.

## How to use the scripts

### `scripts/check_uv_project.py`

Use first.

This script inspects the current directory and returns structured JSON about:
- whether `uv` is installed
- whether `pyproject.toml` exists
- whether `uv.lock` exists
- whether `.venv` exists
- whether `.python-version` exists
- whether the directory looks like:
  - an empty directory
  - a non-project directory
  - a uv project
  - a Python project without uv
  - a legacy Python project
  - an ambiguous or partial setup

Use this script as the source of truth for initial project state detection.

### `scripts/suggest_uv_next_step.py`

Use immediately after project inspection.

This script reads the result of `check_uv_project.py` and returns the single best next step, for example:
- install uv
- ask for Python version strategy
- initialize project with uv
- sync environment
- continue with uv workflow
- offer migration to uv
- inspect legacy workflow
- stop and clarify project state

Use this script as the source of truth for routing the next action.

### `scripts/check_python_invocation.py`

Use before executing a Python-related command that may bypass uv.

Pass the planned command after `--`.

Example:
`python scripts/check_python_invocation.py -- python main.py`

Use this script when the agent is about to run:
- raw `python`
- raw `python3`
- `pip install`
- `python -m pip ...`
- `pytest`
- `ruff`
- `mypy`
- other project-local Python tooling outside `uv run`

If the script marks the command as unsafe:
- rewrite it into the uv-based form
- continue with the raw form only if the user explicitly requests that behavior

## Preflight routing

After inspection, classify the current directory and follow the corresponding path.

### New or empty directory

If the directory is empty and intended for a new local Python project:
1. verify that `uv` is installed
2. determine whether to use the default Python resolved by `uv` or a user-specified version
3. install or select Python if needed
4. initialize the project through `uv`
5. continue all project work through `uv`

Use:
- `references/preflight.md`
- `references/decision-tree.md`

### Non-project directory

If the directory is not empty but is not recognized as a Python project:
- do not initialize a new project blindly
- inspect the script output carefully
- if the directory looks like another structured workspace, treat that as a warning
- ask for confirmation before creating project files

### Existing uv project

If the project is already uv-managed:
- stay inside uv workflows
- use `uv sync` when the environment should match project state
- use `uv add` / `uv remove` for dependency changes
- use `uv run` for project commands

Do not replace the project workflow with raw `pip`, unmanaged `venv`, or system Python defaults.

### Existing Python project without uv

If the directory is a Python project but not clearly uv-managed:
- inspect the existing workflow
- explain that this skill prefers uv-managed local project workflows
- offer migration before major project changes
- do not silently assume the repository is already uv-managed

### Legacy Python project

If the project relies on `requirements.txt`, raw pip usage, Pipenv, Poetry, or manual virtual environments:
- treat it as a migration candidate
- explain the detected state briefly
- offer migration to uv
- do not pretend the project is already using uv

### Ambiguous or partial setup

If project signals are incomplete or conflicting:
- stop
- summarize the ambiguity briefly
- recommend the minimum safe next step
- do not install dependencies or run repair commands blindly

## Dependency and execution rules

When the user asks to install something, determine what kind of thing it is before acting:
- runtime dependency for the project
- development-only dependency
- one-off external tool
- legacy dependency request in a non-uv project

Use `references/decision-tree.md` to choose the correct path.

Default rules:
- runtime dependency -> add through `uv add`
- development-only dependency -> use the dev dependency path
- one-off external tool -> prefer a non-project tool path
- project command execution -> prefer `uv run`
- environment repair -> prefer `uv sync`
- legacy project -> offer migration before major changes

Do not treat every “install package” request as equivalent to `pip install`.

## Python version policy

Handle Python version choice explicitly near the beginning of a new project workflow or when repairing a broken local setup.

Default behavior:
- check whether the project already pins Python
- if not pinned, ask whether to use the default Python resolved by `uv` or a specific version
- if a specific version is requested, install or select it through `uv`
- pin the chosen version when appropriate

Do not silently bind the project to an arbitrary system Python if uv can manage the version.

See:
- `references/preflight.md`
- `references/project-conventions.md`

## Command rewriting policy

If a planned command uses raw Python or raw pip in a way that bypasses uv unnecessarily, prefer rewriting it.

Typical rewrites:
- `python main.py` -> `uv run python main.py`
- `pytest` -> `uv run pytest`
- `ruff check .` -> `uv run ruff check .`
- `pip install requests` -> `uv add requests`

Do not assume that every raw pip install should always become `uv add`.
If intent is ambiguous, use the project references and ask only when needed.

## Confirmation policy

Ask before continuing when the next step would:
- install `uv`
- install a Python version
- create a new project structure
- migrate an existing project to uv
- replace an existing dependency workflow
- make changes while the current project state is ambiguous

Usually no extra confirmation is needed for:
- syncing an existing uv project
- adding a dependency after the user asked for it and the project workflow is already established
- running tests or linters through `uv run`
- executing an already agreed project command through uv

## Anti-patterns

Avoid these unless the user explicitly requests them and understands the tradeoff:
- global `pip install` for project dependencies
- routine use of system Python for managed local projects
- mixing uv and unmanaged pip workflows without explanation
- asking the user to manually activate `.venv` for ordinary project tasks
- manually editing lock-related files
- installing unrelated one-off tools as runtime project dependencies
- continuing after ambiguous environment detection without resolving the ambiguity first

## Response style

When responding under this skill:
- be direct
- be operational
- prefer short explanations and concrete next actions
- use the minimum safe set of commands needed for the task
- clearly state missing prerequisites
- propose uv-based recovery paths when the project is misconfigured

## End goal

For any normal local Python project task, the safe default is:

1. detect state first
2. determine the correct next step
3. keep the work local to the project
4. use uv for setup
5. use uv for Python version management
6. use uv for dependencies
7. use uv for execution
8. avoid global installs and system Python defaults