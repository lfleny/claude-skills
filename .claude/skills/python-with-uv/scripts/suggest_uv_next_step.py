#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_check_script() -> dict[str, Any]:
    script_path = Path(__file__).with_name("check_uv_project.py")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"check_uv_project.py failed with exit code {result.returncode}: "
            f"{(result.stderr or result.stdout).strip()}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"check_uv_project.py did not return valid JSON: {exc}"
        ) from exc


def choose_next_step(report: dict[str, Any]) -> tuple[str, str, bool, list[str], list[str]]:
    project_state = report.get("project_state")
    uv = report.get("uv", {})
    files = report.get("files", {})
    pyproject = report.get("pyproject", {})
    workspace_hints = report.get("workspace_hints", {})
    safe_to_init = report.get("is_safe_to_initialize_new_project_here", False)

    uv_installed = bool(uv.get("installed"))
    looks_like_claude_skill = bool(workspace_hints.get("looks_like_claude_skill"))
    python_version_pinned = bool(files.get("python_version_file")) or bool(pyproject.get("requires_python"))

    commands: list[str] = []
    notes: list[str] = []

    if not uv_installed:
        return (
            "install_uv",
            "uv is not installed, so uv-managed project workflows cannot continue yet",
            True,
            commands,
            notes,
        )

    if project_state == "empty_directory":
        if not python_version_pinned:
            return (
                "ask_python_version_strategy",
                "the directory is empty and ready for a new uv project, but the Python version strategy should be chosen first",
                True,
                commands,
                notes,
            )
        return (
            "initialize_project_with_uv",
            "the directory is empty and ready for a new uv project",
            True,
            ["uv init"],
            notes,
        )

    if project_state == "non_project_directory":
        if looks_like_claude_skill:
            notes.append("current directory looks like a Claude skill workspace, not a Python project")
        if not safe_to_init:
            return (
                "confirm_this_should_be_a_python_project",
                "the directory is not empty and does not look like a Python project, so initialization should be confirmed first",
                True,
                commands,
                notes,
            )
        return (
            "initialize_project_with_uv_if_confirmed",
            "the directory is not recognized as a Python project but appears safe for initialization if the user confirms",
            True,
            ["uv init"],
            notes,
        )

    if project_state == "uv_project":
        if not files.get("venv_dir"):
            return (
                "sync_environment",
                "the project looks uv-managed, but the local environment is missing or incomplete",
                False,
                ["uv sync"],
                notes,
            )
        if not python_version_pinned:
            notes.append("project is uv-managed but Python version is not explicitly pinned")
            return (
                "consider_pinning_python",
                "the uv project can continue normally, but pinning Python would improve reproducibility",
                True,
                commands,
                notes,
            )
        return (
            "continue_with_uv_workflow",
            "the project already looks uv-managed and is ready for normal uv-based work",
            False,
            commands,
            notes,
        )

    if project_state == "python_project_without_uv":
        if pyproject.get("looks_like_poetry"):
            notes.append("Poetry markers were detected")
        if pyproject.get("looks_like_setuptools"):
            notes.append("setuptools-style project markers were detected")
        return (
            "offer_migration_to_uv",
            "this looks like a Python project, but not a uv-managed one",
            True,
            commands,
            notes,
        )

    if project_state == "legacy_python_project":
        if files.get("requirements_txt"):
            notes.append("requirements.txt was detected")
        if files.get("pipfile") or files.get("pipfile_lock"):
            notes.append("Pipenv files were detected")
        if files.get("poetry_lock") or pyproject.get("looks_like_poetry"):
            notes.append("Poetry files were detected")
        return (
            "inspect_legacy_workflow",
            "legacy dependency or packaging files were detected, so migration should be discussed before changes",
            True,
            commands,
            notes,
        )

    if project_state == "ambiguous_partial_setup":
        return (
            "stop_and_clarify_project_state",
            "the repository has incomplete or conflicting signals, so the safe next step is clarification before changes",
            True,
            commands,
            notes,
        )

    return (
        "manual_review",
        "the next step could not be determined confidently",
        True,
        commands,
        notes,
    )


def build_result(report: dict[str, Any]) -> dict[str, Any]:
    next_step, reason, needs_confirmation, commands, notes = choose_next_step(report)

    return {
        "schema_version": "1.0",
        "tool": "suggest_uv_next_step",
        "cwd": report.get("cwd"),
        "project_state": report.get("project_state"),
        "next_step": next_step,
        "reason": reason,
        "needs_confirmation": needs_confirmation,
        "commands": commands,
        "notes": notes,
        "based_on": {
            "uv_installed": report.get("uv", {}).get("installed"),
            "python_version_pinned": (
                report.get("files", {}).get("python_version_file")
                or report.get("pyproject", {}).get("requires_python") is not None
            ),
            "environment_present": report.get("files", {}).get("venv_dir"),
            "looks_like_claude_skill": report.get("workspace_hints", {}).get("looks_like_claude_skill", False),
        },
        "summary": {
            "project_state": report.get("project_state"),
            "next_step": next_step,
            "needs_confirmation": needs_confirmation,
        },
    }


def main() -> int:
    report = run_check_script()
    result = build_result(report)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())