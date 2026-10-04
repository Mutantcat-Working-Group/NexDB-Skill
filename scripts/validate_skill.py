#!/usr/bin/env python3
"""Validate the NexDB-Skill repository without third-party dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "SKILL.md",
    "README.md",
    "README.en.md",
    "LICENSE",
    "agents/openai.yaml",
    "assets/icon.png",
    "references/clients.md",
    "references/connection-modes.md",
    "references/tools.md",
    "references/troubleshooting.md",
)

REQUIRED_SKILL_TERMS = (
    "dbx-mcp",
    "@dbx-app/mcp-server",
    "npx",
    "Streamable HTTP",
    "DBX_WEB_URL",
    "Settings",
)


def validate_frontmatter(problems: list[str]) -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        problems.append("SKILL.md must start with YAML frontmatter")
        return text

    end = text.find("\n---\n", 4)
    if end < 0:
        problems.append("SKILL.md frontmatter is not closed")
        return text

    frontmatter = text[4:end]
    if len(frontmatter) > 1024:
        problems.append("SKILL.md frontmatter exceeds 1024 characters")

    name = re.search(r"^name:\s*([^\s]+)\s*$", frontmatter, re.MULTILINE)
    if not name:
        problems.append("SKILL.md frontmatter must define name")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name.group(1)):
        problems.append("SKILL.md name must use lowercase letters, numbers, and hyphens")

    description = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not description:
        problems.append("SKILL.md frontmatter must define description")
    elif not description.group(1).startswith("Use when "):
        problems.append("SKILL.md description must start with 'Use when '")

    return text


def validate_links(skill_text: str, problems: list[str]) -> None:
    for relative in re.findall(r"\]\((references/[^)]+)\)", skill_text):
        if not (ROOT / relative).is_file():
            problems.append(f"SKILL.md references a missing file: {relative}")


def validate_icon(problems: list[str]) -> None:
    icon = ROOT / "assets/icon.png"
    if not icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        problems.append("assets/icon.png is not a PNG file")


def validate_content(skill_text: str, problems: list[str]) -> None:
    for term in REQUIRED_SKILL_TERMS:
        if term not in skill_text:
            problems.append(f"SKILL.md is missing required compatibility term: {term}")


def main() -> int:
    problems: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            problems.append(f"missing required file: {relative}")

    if (ROOT / "SKILL.md").is_file():
        skill_text = validate_frontmatter(problems)
        validate_links(skill_text, problems)
        validate_content(skill_text, problems)
    if (ROOT / "assets/icon.png").is_file():
        validate_icon(problems)
    else:
        problems.append("missing required file: assets/icon.png")

    if problems:
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("NexDB-Skill validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
