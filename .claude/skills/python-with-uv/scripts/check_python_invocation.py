#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_LOCAL_COMMANDS = {
    "python",
    "python3",
    "pytest",
    "ruff",
    "mypy",
    "black",
    "isort",
    "alembic",
    "celery",
    "fastapi",
    "flask",
    "uvicorn",
    "gunicorn",
}

GLOBAL_INSTALL_PATTERNS = {
    ("pip", "install"),
    ("pip3", "install"),
    ("python", "-m", "pip"),
    ("python3", "-m", "pip"),
}

UV_PREFIXES = {
    ("uv", "run"),
    ("uv", "add"),
    ("uv", "remove"),
    ("uv", "sync"),
    ("uv", "python"),
    ("uv", "tool"),
    ("uvx",),
}


def normalize_command(argv: list[str]) -> list[str]:
    return [part.strip() for part in argv if part.strip()]


def detect_python_path_invocation(first: str) -> bool:
    if "/" not in first:
        return False

    lowered = first.lower()
    name = Path(first).name.lower()

    return "python" in lowered or name.startswith("python")


def starts_with(tokens: list[str], prefix: tuple[str, ...]) -> bool:
    if len(tokens) < len(prefix):
        return False
    return tuple(tokens[: len(prefix)]) == prefix


def classify_invocation(tokens: list[str]) -> dict[str, Any]:
    if not tokens:
        return {
            "classification": "empty_command",
            "is_safe": False,
            "should_rewrite": False,
            "reason": "no command was provided",
            "recommended_rewrite": None,
            "notes": [],
        }

    first = tokens[0]
    notes: list[str] = []

    for prefix in UV_PREFIXES:
        if starts_with(tokens, prefix):
            return {
                "classification": "uv_managed",
                "is_safe": True,
                "should_rewrite": False,
                "reason": "command already uses a uv-managed workflow",
                "recommended_rewrite": None,
                "notes": notes,
            }

    for pattern in GLOBAL_INSTALL_PATTERNS:
        if starts_with(tokens, pattern):
            if pattern in {("python", "-m", "pip"), ("python3", "-m", "pip")} and len(tokens) >= 4:
                pkg_part = " ".join(tokens[3:])
                rewrite = f"uv add {pkg_part}"
            elif len(tokens) >= 3:
                pkg_part = " ".join(tokens[2:])
                rewrite = f"uv add {pkg_part}"
            else:
                rewrite = "uv add <package>"

            return {
                "classification": "global_pip_install",
                "is_safe": False,
                "should_rewrite": True,
                "reason": "global or raw pip installation bypasses the uv project workflow",
                "recommended_rewrite": rewrite,
                "notes": notes,
            }

    if detect_python_path_invocation(first):
        rewritten = "uv run " + " ".join(tokens)
        return {
            "classification": "direct_python_path",
            "is_safe": False,
            "should_rewrite": True,
            "reason": "direct interpreter path bypasses uv-managed execution",
            "recommended_rewrite": rewritten,
            "notes": notes,
        }

    if first in {"python", "python3"}:
        rewritten = "uv run " + " ".join(tokens)
        return {
            "classification": "raw_python_execution",
            "is_safe": False,
            "should_rewrite": True,
            "reason": "raw python execution bypasses the uv project environment",
            "recommended_rewrite": rewritten,
            "notes": notes,
        }

    if first in PROJECT_LOCAL_COMMANDS:
        rewritten = "uv run " + " ".join(tokens)
        return {
            "classification": "raw_project_command",
            "is_safe": False,
            "should_rewrite": True,
            "reason": "project-local command should usually run inside the uv-managed environment",
            "recommended_rewrite": rewritten,
            "notes": notes,
        }

    if first in {"pip", "pip3"}:
        return {
            "classification": "raw_pip_command",
            "is_safe": False,
            "should_rewrite": True,
            "reason": "raw pip usage usually conflicts with uv-managed project workflows",
            "recommended_rewrite": "prefer uv add, uv remove, or uv sync depending on intent",
            "notes": notes,
        }

    if shutil.which(first) is None:
        notes.append("command executable was not found on PATH during validation")

    return {
        "classification": "unknown_command",
        "is_safe": True,
        "should_rewrite": False,
        "reason": "command does not match a known unsafe Python invocation pattern",
        "recommended_rewrite": None,
        "notes": notes,
    }


def main() -> int:
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        raw_command = sys.argv[idx + 1 :]
    else:
        raw_command = sys.argv[1:]

    tokens = normalize_command(raw_command)
    analysis = classify_invocation(tokens)

    result = {
        "schema_version": "1.0",
        "tool": "check_python_invocation",
        "input_command": raw_command,
        "normalized_command": tokens,
        **analysis,
        "summary": {
            "classification": analysis["classification"],
            "is_safe": analysis["is_safe"],
            "should_rewrite": analysis["should_rewrite"],
        },
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())