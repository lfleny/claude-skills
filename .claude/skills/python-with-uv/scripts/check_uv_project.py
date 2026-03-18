#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None


def run_command(cmd: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or result.stderr).strip()
        return result.returncode == 0, output
    except Exception as exc:
        return False, str(exc)


def path_exists(path: Path) -> bool:
    return path.exists()


def is_non_empty_directory(path: Path) -> bool:
    try:
        return any(path.iterdir())
    except Exception:
        return False


def detect_python_files(root: Path) -> dict[str, bool]:
    markers = {
        "pyproject_toml": (root / "pyproject.toml").exists(),
        "uv_lock": (root / "uv.lock").exists(),
        "python_version_file": (root / ".python-version").exists(),
        "venv_dir": (root / ".venv").exists(),
        "requirements_txt": (root / "requirements.txt").exists(),
        "requirements_dev_txt": (root / "requirements-dev.txt").exists(),
        "setup_py": (root / "setup.py").exists(),
        "setup_cfg": (root / "setup.cfg").exists(),
        "pipfile": (root / "Pipfile").exists(),
        "pipfile_lock": (root / "Pipfile.lock").exists(),
        "poetry_lock": (root / "poetry.lock").exists(),
        "tox_ini": (root / "tox.ini").exists(),
        "pytest_ini": (root / "pytest.ini").exists(),
        "ruff_toml": (root / "ruff.toml").exists(),
        "src_dir": (root / "src").is_dir(),
        "tests_dir": (root / "tests").is_dir(),
    }
    return markers


def parse_pyproject(root: Path) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    result: dict[str, Any] = {
        "exists": pyproject.exists(),
        "parse_ok": False,
        "project_name": None,
        "requires_python": None,
        "dependencies_declared": False,
        "optional_dependencies_declared": False,
        "dependency_groups_declared": False,
        "build_system_declared": False,
        "tool_sections": [],
        "looks_like_poetry": False,
        "looks_like_setuptools": False,
        "looks_like_hatch": False,
        "looks_like_rye": False,
        "looks_like_uv_project": False,
        "parse_error": None,
    }

    if not pyproject.exists():
        return result

    if tomllib is None:
        result["parse_error"] = "tomllib is not available in this Python version"
        return result

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        result["parse_ok"] = True

        project = data.get("project", {})
        tool = data.get("tool", {})
        build_system = data.get("build-system", {})

        result["project_name"] = project.get("name")
        result["requires_python"] = project.get("requires-python")
        result["dependencies_declared"] = bool(project.get("dependencies"))
        result["optional_dependencies_declared"] = bool(project.get("optional-dependencies"))
        result["dependency_groups_declared"] = "dependency-groups" in data
        result["build_system_declared"] = bool(build_system)
        result["tool_sections"] = sorted(tool.keys()) if isinstance(tool, dict) else []

        result["looks_like_poetry"] = isinstance(tool, dict) and "poetry" in tool
        result["looks_like_setuptools"] = (
            isinstance(tool, dict) and "setuptools" in tool
        ) or (
            isinstance(build_system, dict)
            and any("setuptools" in req for req in build_system.get("requires", []))
        )
        result["looks_like_hatch"] = isinstance(tool, dict) and "hatch" in tool
        result["looks_like_rye"] = isinstance(tool, dict) and "rye" in tool

        # Heuristic only:
        # uv project usually has pyproject.toml and often uv.lock.
        # We intentionally avoid assuming [tool.uv] must exist.
        result["looks_like_uv_project"] = (root / "uv.lock").exists()

    except Exception as exc:
        result["parse_error"] = str(exc)

    return result


def detect_gitignore_venv(root: Path) -> dict[str, Any]:
    gitignore = root / ".gitignore"
    result = {
        "gitignore_exists": gitignore.exists(),
        "venv_ignored": False,
    }
    if not gitignore.exists():
        return result

    try:
        lines = [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()]
        result["venv_ignored"] = any(line in {".venv", "/.venv", ".venv/"} for line in lines)
    except Exception:
        pass
    return result


def classify_project_state(
    root: Path,
    uv_installed: bool,
    markers: dict[str, bool],
    pyproject: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    has_pyproject = markers["pyproject_toml"]
    has_uv_lock = markers["uv_lock"]
    has_python_files = any(
        [
            markers["requirements_txt"],
            markers["requirements_dev_txt"],
            markers["setup_py"],
            markers["setup_cfg"],
            markers["pipfile"],
            markers["pipfile_lock"],
            markers["poetry_lock"],
            markers["src_dir"],
            markers["tests_dir"],
            has_pyproject,
        ]
    )

    if not is_non_empty_directory(root):
        reasons.append("directory is empty")
        return "empty_directory", reasons, warnings

    if not has_python_files and not markers["venv_dir"]:
        reasons.append("directory is not empty but no clear Python project markers were found")
        return "non_project_directory", reasons, warnings

    if has_uv_lock and has_pyproject:
        reasons.append("pyproject.toml and uv.lock are present")
        if not uv_installed:
            warnings.append("project looks uv-managed but uv is not installed")
        return "uv_project", reasons, warnings

    if has_pyproject and pyproject.get("looks_like_poetry"):
        reasons.append("pyproject.toml is present and Poetry markers were detected")
        return "python_project_without_uv", reasons, warnings

    if has_pyproject and not has_uv_lock:
        reasons.append("pyproject.toml is present but uv.lock is missing")
        warnings.append("project may be Python-based but not yet uv-managed or not yet locked")
        return "python_project_without_uv", reasons, warnings

    if any(
        [
            markers["requirements_txt"],
            markers["requirements_dev_txt"],
            markers["pipfile"],
            markers["pipfile_lock"],
            markers["setup_py"],
            markers["setup_cfg"],
            markers["poetry_lock"],
        ]
    ):
        reasons.append("legacy dependency or packaging files were detected")
        return "legacy_python_project", reasons, warnings

    if markers["venv_dir"] and not has_pyproject and not has_uv_lock:
        reasons.append(".venv exists but project metadata is missing")
        warnings.append("virtual environment exists without clear project metadata")
        return "ambiguous_partial_setup", reasons, warnings

    if markers["src_dir"] or markers["tests_dir"]:
        reasons.append("Python project directories exist but project metadata is incomplete")
        warnings.append("repository may need initialization or migration")
        return "ambiguous_partial_setup", reasons, warnings

    reasons.append("project state could not be classified confidently")
    warnings.append("manual inspection is recommended before modifying dependencies")
    return "ambiguous_partial_setup", reasons, warnings


def recommend_next_actions(
    state: str,
    uv_installed: bool,
    markers: dict[str, bool],
    pyproject: dict[str, Any],
) -> list[str]:
    actions: list[str] = []

    if not uv_installed:
        actions.append("install_uv")

    if state == "empty_directory":
        if not uv_installed:
            actions.append("stop_until_uv_installed")
        else:
            if not markers["python_version_file"]:
                actions.append("ask_python_version_strategy")
            actions.append("initialize_project_with_uv")
        return actions

    if state == "non_project_directory":
        actions.append("confirm_this_should_be_a_python_project")
        if uv_installed:
            actions.append("initialize_project_with_uv_if_confirmed")
        return actions

    if state == "uv_project":
        if not markers["venv_dir"]:
            actions.append("sync_environment")
        if not markers["python_version_file"] and not pyproject.get("requires_python"):
            actions.append("consider_pinning_python")
        actions.append("continue_with_uv_workflow")
        return actions

    if state == "python_project_without_uv":
        actions.append("offer_migration_to_uv")
        if not pyproject.get("requires_python"):
            actions.append("consider_setting_requires_python")
        return actions

    if state == "legacy_python_project":
        actions.append("offer_migration_to_uv")
        if markers["requirements_txt"]:
            actions.append("inspect_requirements_workflow")
        if markers["poetry_lock"] or pyproject.get("looks_like_poetry"):
            actions.append("inspect_poetry_workflow")
        return actions

    if state == "ambiguous_partial_setup":
        actions.append("stop_and_clarify_project_state")
        actions.append("inspect_repository_before_changes")
        return actions

    return ["manual_review"]


def detect_workspace_hints(root: Path) -> dict[str, bool]:
    return {
        "looks_like_claude_skill": (
            (root / "SKILL.md").exists()
            and (root / "scripts").is_dir()
            and (root / "references").is_dir()
        )
    }


def is_safe_to_initialize_new_project_here(root: Path, markers: dict[str, bool]) -> bool:
    if not is_non_empty_directory(root):
        return True

    if any(
        [
            markers["pyproject_toml"],
            markers["uv_lock"],
            markers["requirements_txt"],
            markers["requirements_dev_txt"],
            markers["setup_py"],
            markers["setup_cfg"],
            markers["pipfile"],
            markers["pipfile_lock"],
            markers["poetry_lock"],
            markers["src_dir"],
            markers["tests_dir"],
        ]
    ):
        return False

    return False


def main() -> int:
    root = Path.cwd()

    uv_path = shutil.which("uv")
    uv_installed = uv_path is not None

    uv_version_ok = False
    uv_version_output = None
    if uv_installed:
        uv_version_ok, uv_version_output = run_command(["uv", "--version"])

    python_executable = sys.executable
    python_version = ".".join(map(str, sys.version_info[:3]))

    markers = detect_python_files(root)
    pyproject = parse_pyproject(root)
    gitignore = detect_gitignore_venv(root)
    workspace_hints = detect_workspace_hints(root)
    safe_to_initialize = is_safe_to_initialize_new_project_here(root, markers)

    state, reasons, warnings = classify_project_state(
        root=root,
        uv_installed=uv_installed,
        markers=markers,
        pyproject=pyproject,
    )

    result = {
        "schema_version": "1.0",
        "tool": "check_uv_project",
        "cwd": str(root),
        "project_state": state,
        "workspace_hints": workspace_hints,
        "is_safe_to_initialize_new_project_here": safe_to_initialize,
        "uv": {
            "installed": uv_installed,
            "path": uv_path,
            "version_ok": uv_version_ok,
            "version_output": uv_version_output,
        },
        "python_runtime": {
            "executable": python_executable,
            "version": python_version,
        },
        "files": markers,
        "pyproject": pyproject,
        "gitignore": gitignore,
        "reasons": reasons,
        "warnings": warnings,
        "recommended_next_actions": recommend_next_actions(
            state=state,
            uv_installed=uv_installed,
            markers=markers,
            pyproject=pyproject,
        ),
        "confirmation_required": state in {
            "empty_directory",
            "non_project_directory",
            "python_project_without_uv",
            "legacy_python_project",
            "ambiguous_partial_setup",
        } or not uv_installed,
        "summary": {
            "project_state": state,
            "uv_installed": uv_installed,
            "python_version_pinned": markers["python_version_file"],
            "environment_present": markers["venv_dir"],
            "recommended_next_action": (
                recommend_next_actions(
                    state=state,
                    uv_installed=uv_installed,
                    markers=markers,
                    pyproject=pyproject,
                )[0]
                if recommend_next_actions(
                    state=state,
                    uv_installed=uv_installed,
                    markers=markers,
                    pyproject=pyproject,
                )
                else None
            ),
        },
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())