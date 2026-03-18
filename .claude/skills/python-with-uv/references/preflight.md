# Preflight for local Python projects managed with uv

Use this file before the first project-changing action.

Run preflight before:
- creating a new Python project
- adding or removing dependencies
- running tests, scripts, linters, formatters, or migrations
- repairing a broken local setup
- deciding whether to use project dependencies, dev dependencies, or a one-off tool workflow

## Goal

Determine the current project state before making changes.

The agent must avoid these mistakes:
- installing dependencies globally
- using system Python for routine project work
- using raw `pip install` in a project that should be managed by `uv`
- guessing the project state without checking files

## Step 1. Inspect the current directory

Run:

`python scripts/check_uv_project.py`

Use the result to determine:
- whether `uv` is installed
- whether `pyproject.toml` exists
- whether `uv.lock` exists
- whether `.venv` exists
- whether `.python-version` exists
- whether this directory looks like:
  - a new or empty directory
  - an existing uv project
  - a Python project without uv
  - a legacy pip-style project
  - an ambiguous or partial setup

Do not continue with dependency installation or project execution until this state is known.

## Step 2. If the next step is unclear, classify the task

Run:

`python scripts/suggest_uv_next_step.py`

Use it to decide whether the correct next action is:
- install uv
- initialize a new project
- install Python through uv
- pin a Python version
- sync the environment
- migrate from a legacy workflow
- continue normal uv project work

## Step 3. Handle missing uv

If `uv` is not installed:
- explain that this skill manages local Python projects through `uv`
- propose installing `uv`
- do not fall back to global `pip` workflows as the default replacement

Only continue with project-local Python operations after `uv` is available.

## Step 4. Handle Python version selection

If the project is new or the Python version is not pinned:
- ask whether to use the default Python resolved by `uv` or a specific version
- if the user requests a specific version, install it through `uv`
- pin the chosen version when appropriate

Do not silently use an arbitrary system Python if `uv` can manage Python for the project.

## Step 5. Handle project state

### New project or empty directory

If this is a new project:
1. verify that `uv` is available
2. decide the Python version strategy
3. install or select Python if needed
4. initialize the project with `uv`
5. continue all Python-related work through `uv`

### Existing uv project

If `pyproject.toml` and uv-managed project signals are present:
- treat the project as uv-managed
- use `uv sync` to align the environment
- use `uv add` / `uv remove` for dependencies
- use `uv run` for project commands

### Existing Python project without uv

If the directory looks like a Python project but not a uv project:
- inspect the existing dependency workflow
- explain that this skill prefers uv-managed local project workflows
- offer migration before continuing with major project changes

### Legacy pip-style project

If the project relies on:
- `requirements.txt`
- raw `pip install`
- manual virtual environment usage
- old tooling without uv metadata

then:
- explain the current state briefly
- offer migration to `uv`
- do not pretend the project is already uv-managed

### Ambiguous state

If the directory contains conflicting or incomplete signals:
- stop
- summarize the ambiguity
- recommend the minimum safe next step
- do not install dependencies or run repair commands blindly

## Step 6. Decide how to install or run something

Before acting on a user request, classify the request:

- project dependency -> add it to the project
- development-only dependency -> add it as a dev dependency
- one-off external tool -> prefer a tool-style or ephemeral workflow
- Python execution inside the project -> use `uv run`
- environment repair -> use `uv sync` or the uv project workflow
- migration -> convert the workflow before continuing

Do not treat all “install package” requests the same way.

## Step 7. Check command safety before execution

If the planned command uses raw `python`, `pip`, or another interpreter path, run:

`python scripts/check_python_invocation.py`

If the command bypasses `uv` unnecessarily:
- rewrite it into the uv-based form
- only continue with the raw form if the user explicitly wants that behavior

## Step 8. Safe defaults after preflight

Once preflight is complete, the default behavior is:

- use `uv` for project setup
- use `uv` for dependency management
- use `uv` for environment synchronization
- use `uv run` for project commands
- keep work project-local
- avoid global installs
- avoid relying on system Python

## Minimal preflight summary format

When reporting the result of preflight, prefer this structure:

- project state
- uv installed: yes/no
- python version pinned: yes/no
- environment present: yes/no
- recommended next action
- whether confirmation is required

Keep the summary short and operational.