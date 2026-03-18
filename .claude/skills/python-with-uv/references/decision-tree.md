# Decision tree for managing local Python projects with uv

Use this file to choose the correct next action after preflight.

## 1. Is this a local Python project task?

If no:
- do not force uv into unrelated tasks

If yes:
- continue through this decision tree

## 2. Is `uv` installed?

If no:
- recommend installing `uv`
- stop before doing Python project work through other tools unless the user explicitly declines uv

If yes:
- continue

## 3. Is this a new project or an existing directory?

### New project or empty directory

Use the new-project path.

Questions:
- should this project be initialized with uv?
- should the default Python resolved by uv be used?
- does the user want a specific Python version?

Recommended path:
1. install or select Python if needed
2. pin Python if appropriate
3. initialize the project with uv
4. continue through uv only

Typical actions:
- `uv python install <version>` if needed
- `uv python pin <version>` if needed
- `uv init`

### Existing directory

Inspect the project state first.
Then choose one of the branches below.

## 4. Does the directory look like a uv project?

Signals:
- `pyproject.toml`
- `uv.lock`
- `.venv`
- uv-managed workflow already in use

If yes:
- treat it as a uv project
- do not switch to raw pip workflows

Typical actions:
- `uv sync`
- `uv add <package>`
- `uv add --dev <package>`
- `uv remove <package>`
- `uv run <command>`

## 5. Does the directory look like a Python project without uv?

Signals:
- `pyproject.toml` without uv usage
- `requirements.txt`
- `setup.py`
- `Pipfile`
- Poetry files
- unmanaged venv folders

If yes:
- classify it as a migration candidate
- do not force migration silently
- explain the situation briefly
- ask whether to migrate before major changes

If the user accepts migration:
- migrate to uv
- then continue with uv-only project workflows

If the user declines migration:
- do not pretend the project is uv-managed
- do not apply uv-specific assumptions to the project state

## 6. What kind of package or tool does the user need?

### A runtime dependency for this project

Use:
- `uv add <package>`

Examples:
- web framework
- database client
- HTTP library
- runtime SDK

### A development-only dependency for this repository

Use:
- `uv add --dev <package>`

Examples:
- pytest
- ruff
- mypy
- black
- tooling used only in development

### A one-off CLI or external tool not belonging to project dependencies

Prefer:
- an ephemeral or tool-style workflow

Do not add such tools as runtime dependencies unless they are truly part of the project.

### A package for a legacy non-uv workflow

If the repository is not yet migrated:
- offer migration first
- only use legacy-compatible flows if migration is not being performed

## 7. Does the user want to run something?

### Run code, tests, linters, formatters, migrations, or scripts inside the project

Use:
- `uv run <command>`

Preferred examples:
- `uv run python main.py`
- `uv run pytest`
- `uv run ruff check .`

Do not default to:
- `python main.py`
- `pytest`
- `ruff check .`

unless the user explicitly requests a non-uv flow

## 8. Is the environment missing, stale, or inconsistent?

If yes:
- prefer synchronization and repair through uv
- do not jump to unrelated tools

Typical action:
- `uv sync`

If the lockfile is missing or needs refresh:
- use the uv project workflow
- do not edit lock-related files manually

## 8A. Is manual virtual environment activation needed?

Default answer:
- no

If the user wants to run normal project commands:
- do not suggest manual activation
- use `uv run <command>`

Only allow manual activation if:
- the user explicitly asks for it
- the user explicitly wants an interactive shell session
- a non-uv external tool explicitly requires an activated environment

## 9. Is Python version handling needed?

If the version is not pinned or the requested version is unavailable:
- ask whether to use the uv default or a specific version
- install Python through uv if needed
- pin when appropriate

Typical actions:
- `uv python install <version>`
- `uv python pin <version>`

Do not silently bind the project to an arbitrary system interpreter if uv can manage the version.

## 10. Is the agent about to use raw `python` or `pip`?

If yes:
- treat that as a warning signal
- check whether the command should be rewritten through uv
- only keep the raw command if the user explicitly wants that behavior

Preferred replacements:
- `python ...` -> `uv run python ...`
- `pytest` -> `uv run pytest`
- `pip install <package>` -> `uv add <package>` or another uv-appropriate path

## 11. Default routing summary

Use these defaults:

- new project -> `uv init`
- choose Python version -> `uv python install` / `uv python pin`
- add project dependency -> `uv add`
- add dev dependency -> `uv add --dev`
- run project command -> `uv run`
- repair environment -> `uv sync`
- one-off tool -> ephemeral/tool-style workflow
- legacy project -> offer migration first

## 12. Escalation cases

Stop and ask before continuing if:
- uv is missing
- Python must be installed
- project initialization is about to create new files
- migration will change project structure or dependency workflow
- the current repository has ambiguous signals