---
name: managing-python-projects-with-uv
description: enforce safe local python project workflows with uv. use when creating a new python project, entering an existing local repository, adding dependencies, running scripts, tests, linters, migrations, or choosing a python version. check for uv, pyproject.toml, uv.lock, and .venv before making changes. prefer uv-managed python, uv add, uv sync, and uv run over global installs, system python, or raw pip. if uv or python is missing, guide the user through installation or migration before continuing.
---

# Manage local python projects with uv

Use this skill to manage local Python projects through `uv` instead of the system Python or global package installation.

Treat `uv` as the default tool for:
- project initialization
- Python version management
- dependency management
- virtual environment management
- running Python commands inside the project
- launching tests, linters, formatters, and migrations

## Core policy

Always prefer project-local workflows over global Python workflows.

For local Python projects:
- do not install dependencies globally
- do not use the system Python for project tasks unless the user explicitly requests it
- do not default to `pip install`
- do not ask the user to manually activate `.venv` unless activation is specifically needed for their workflow
- prefer `uv run ...` over raw `python ...`, `pytest ...`, `ruff ...`, and similar commands
- prefer `uv add` over `pip install`
- prefer `uv sync` to align the environment with the project state
- prefer `uv`-managed Python versions when choosing or installing Python for the project

Assume that the correct default for a local project is:
1. detect the project state
2. ensure `uv` is available
3. ensure an appropriate Python version is available
4. ensure the project is initialized or recognized correctly
5. perform all Python-related work through `uv`

## Required preflight before the first project-changing action

Before creating a project, installing dependencies, running project code, or modifying Python tooling, perform a preflight check.

Run the project check script first:

`python scripts/check_uv_project.py`

Use the result to classify the current directory into one of these states:
- empty directory or non-project directory
- uv project
- Python project without uv
- legacy project using requirements.txt or pip-style workflows
- project with ambiguous or partial configuration

If needed, run the next-step suggestion script:

`python scripts/suggest_uv_next_step.py`

Use these checks before taking action. Do not skip them unless the current conversation already established the exact project state.

## How to behave based on project state

### 1. Empty directory or new project

If the user is starting a new Python project:
- confirm that the project should be created with `uv`
- check whether `uv` is installed
- ask the user whether to use the default Python resolved by `uv` or whether they want a specific Python version
- if the user wants a specific version and it is not available, install it through `uv`
- initialize the project through `uv`
- ensure the project will be managed through `uv` going forward

Default flow:
1. verify `uv` exists
2. determine Python version strategy
3. install or pin Python if needed
4. initialize the project
5. use only `uv` commands for future work in this project

### 2. Existing uv project

If the current directory is already a uv project:
- do not switch to raw `pip`
- do not replace the workflow with manual venv management
- use the existing project metadata
- use `uv sync` when the environment should match the project state
- use `uv add` or `uv remove` for dependency changes
- use `uv run` for project commands

Treat `pyproject.toml` and `uv.lock` as the source of truth for the project state.

### 3. Existing Python project without uv

If this is a Python project but not clearly a uv project:
- inspect the existing files
- determine whether the user wants to migrate the project to `uv`
- do not force migration without telling the user
- explain the recommended migration path briefly
- after migration is accepted, use `uv` as the exclusive tool for Python-related project work

Common migration indicators:
- `requirements.txt`
- `setup.py`
- `Pipfile`
- Poetry files
- existing virtual environment folders without uv metadata

### 4. Legacy pip-style workflow

If the project appears to rely on global `pip`, manual `venv`, or requirements-based workflows:
- explain that the current skill prefers project-local `uv` workflows
- offer migration
- if the user declines migration, do not pretend the project is uv-managed
- if the user accepts migration, convert the workflow before continuing with project changes

## Python version policy

Python version choice must be handled explicitly near the beginning of a new project workflow.

When creating a new project or repairing a broken local setup:
- check whether a project Python version is already pinned
- if not pinned, ask whether the user wants the default Python from `uv` or a specific version
- if a specific version is requested, install or select it through `uv`
- pin the chosen version for project consistency when appropriate

Do not silently use an arbitrary system Python if `uv` can manage Python for this project.

## Dependency policy

When dependencies are needed:
- add project dependencies through `uv add`
- add development-only tools through the dev dependency flow
- do not install project dependencies globally
- do not use bare `pip install` inside a normal uv-managed project
- do not recommend mixing global package installation with project-local dependency management

When the user asks to install a package, interpret the request in context:
- if the package is needed by this project, add it to the project
- if the package is only needed for a one-off command, consider a non-project tool workflow
- if the package is a developer tool for this repository, place it in the development dependency flow

## Command execution policy

For commands that belong to the project environment, use `uv run`.

This includes:
- running Python scripts
- running tests
- running linters
- running formatters
- running migrations
- launching project CLIs
- running module entry points

Before using a raw Python or pip command, check whether that invocation violates project policy.

Run the invocation guard script when needed:

`python scripts/check_python_invocation.py`

If the planned command would bypass `uv` unnecessarily, revise the command before execution.

## Tool and one-off command policy

Not every Python-related task should become a project dependency.

When the user needs a Python-based CLI only for a one-off or isolated action:
- prefer a tool-style or ephemeral workflow instead of adding it to project dependencies
- do not pollute the project dependency graph with unrelated command-line tools unless the tool is part of the repository workflow

Only add a tool to project dependencies if it is actually part of the project itself.

## Lockfile and environment policy

In uv-managed projects:
- treat the lockfile as part of the project state
- prefer environment synchronization over ad hoc repair commands
- avoid manual edits to lock-related files
- do not tell the user to recreate the environment with unrelated tools when `uv` can repair or sync it properly

If the environment is missing or stale:
- sync it through `uv`
- then continue all project execution through `uv run`

## Virtual environment policy

Assume `.venv` is project-local state.

For normal agent workflows:
- do not require manual activation of `.venv`
- do not tell the user to leave the project-local workflow and install things into the global interpreter
- do not create separate unmanaged environments if the project should be managed by `uv`

If `.venv` is absent in a uv project, repair the project through the uv workflow rather than switching tools.

## Communication policy

When the project is not ready for the requested task:
- explain the missing prerequisite briefly
- propose the uv-based fix
- ask for confirmation only when the next step changes project structure, installs Python, or performs migration

Examples of cases that should usually be confirmed:
- installing `uv`
- installing a new Python version
- initializing a new project
- migrating an existing project to uv
- replacing an existing dependency management workflow

Examples of cases that usually do not need extra confirmation once the workflow is established:
- syncing the environment
- adding a dependency after the user asked for it
- running tests
- running linters or formatters through `uv run`
- executing an already agreed project command

## Default decision rules

Use these defaults unless the user explicitly says otherwise:

- New local Python project -> initialize and manage it with `uv`
- Existing uv project -> stay fully inside uv workflows
- Need package for the project -> add it through uv project dependency management
- Need package only for development in this repo -> use the development dependency path
- Need package only for a one-off command -> use a non-project tool path
- Need to run Python code in the project -> use `uv run`
- Need to choose Python version -> prefer uv-managed Python, not the system interpreter
- Detect raw pip or global installation plans -> stop and replace them with uv-based project actions when appropriate

## Anti-patterns to avoid

Do not do the following unless the user explicitly asks for it and understands the tradeoff:
- `pip install` into the global environment for a project dependency
- use system `python` for routine project execution
- ask the user to activate `.venv` for ordinary agent-driven project commands
- mix unmanaged `venv` flows with uv-managed project flows without explanation
- manually edit lockfiles
- install unrelated command-line tools as runtime dependencies of the project
- continue with ambiguous environment state without first checking the project

## Available scripts

Use these bundled scripts as decision support:

### `scripts/check_uv_project.py`
Use this to inspect the current directory and detect:
- whether `uv` is installed
- whether `pyproject.toml` exists
- whether `uv.lock` exists
- whether `.venv` exists
- whether Python project files indicate uv, legacy, or ambiguous state

### `scripts/suggest_uv_next_step.py`
Use this after project inspection when the next action is unclear.
This script should recommend the most appropriate next step, such as:
- install uv
- initialize project
- install or pin Python
- sync environment
- migrate project
- continue normal uv workflow

### `scripts/check_python_invocation.py`
Use this before executing a planned Python-related command when there is any risk of bypassing the uv workflow.
If the command uses raw `python`, `pip`, or another interpreter path in a way that conflicts with project policy, revise the command.

## Output style for this skill

When responding under this skill:
- be direct and operational
- prefer concrete next actions
- explain why uv is being used only when it helps the user
- keep setup explanations short
- when proposing commands, prefer the minimum safe set of commands needed for the task
- if a project is misconfigured, state the problem clearly and propose the uv-based recovery path

## End goal

The end goal of this skill is to keep local Python project work reproducible, project-local, and uv-managed.

For any normal local Python project task, the safe default is:
- avoid global installs
- avoid system Python
- detect state first
- use uv for setup
- use uv for dependencies
- use uv for execution