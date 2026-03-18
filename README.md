# python-with-uv

A Claude Code skill for safe local Python project workflows with `uv`.

| Section | Description |
|---|---|
| Purpose | Prevent agents from using global installs, system Python, raw `pip`, and manual `.venv` activation as the default workflow. |
| Default workflow | Inspect project state → choose the safest next step → use `uv` for setup, dependencies, and execution. |
| Main commands encouraged | `uv init`, `uv add`, `uv sync`, `uv run ...` |
| Project scope | Local Python projects and repositories |
| Not optimized for | CI, Docker, deployment automation |
| Key references | `references/preflight.md`, `references/decision-tree.md`, `references/project-conventions.md` |
| Key scripts | `scripts/check_uv_project.py`, `scripts/suggest_uv_next_step.py`, `scripts/check_python_invocation.py` |

## What it enforces

| Rule | Preferred behavior |
|---|---|
| Project setup | Use `uv` instead of ad hoc Python setup |
| Dependency management | Use `uv add` instead of `pip install` |
| Command execution | Use `uv run ...` for project commands |
| Python selection | Prefer uv-managed Python versions |
| Virtual environment workflow | Do not suggest manual `.venv` activation unless explicitly needed |

## Typical use cases

- Create a new Python project
- Enter an existing local repository
- Add dependencies
- Run scripts, tests, linters, or formatters
- Decide whether a project should be migrated to `uv`