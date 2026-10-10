#!/usr/bin/env python3
"""Check local Markdown links, code fences, YAML syntax, and Python syntax."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    print("Missing dependency: install PyYAML before running this validator.", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*((?:\x60){3,}|~{3,})(.*)$")
errors: list[str] = []
markdown_count = 0
yaml_count = 0
python_count = 0


def parse_yaml(text: str, label: str) -> None:
    """Parse all YAML documents and report syntax errors with a useful label."""
    global yaml_count
    try:
        list(yaml.safe_load_all(text))
        yaml_count += 1
    except yaml.YAMLError as exc:
        errors.append(f"{label}: invalid YAML: {exc}")


def check_python(path: Path) -> None:
    """Parse a Python source file without executing it."""
    global python_count
    python_count += 1
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid Python syntax: {exc}")


def check_markdown(path: Path) -> None:
    global markdown_count
    markdown_count += 1
    lines = path.read_text(encoding="utf-8").splitlines()
    visible_lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    fence_language = ""
    fence_start_line = 0
    fence_content: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if fence_char is None:
            if match:
                marker, info = match.groups()
                fence_char = marker[0]
                fence_length = len(marker)
                fence_language = info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""
                fence_start_line = line_number
                fence_content = []
                visible_lines.append("")
            else:
                visible_lines.append(line)
            continue

        visible_lines.append("")
        if match:
            marker = match.group(1)
            if marker[0] == fence_char and len(marker) >= fence_length and not match.group(2).strip():
                if fence_language in {"yaml", "yml"}:
                    label = f"{path.relative_to(ROOT)}:{fence_start_line} (YAML code fence)"
                    parse_yaml("\n".join(fence_content), label)
                fence_char = None
                fence_length = 0
                fence_language = ""
                fence_content = []
            else:
                fence_content.append(line)
        else:
            fence_content.append(line)

    if fence_char is not None:
        errors.append(f"{path.relative_to(ROOT)}:{fence_start_line}: fenced code block is not closed")

    visible_text = "\n".join(visible_lines)
    for line_number, line in enumerate(visible_text.splitlines(), start=1):
        for match in MARKDOWN_LINK_RE.finditer(line):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and ">" in raw_target:
                raw_target = raw_target[1:raw_target.index(">")]
            else:
                raw_target = raw_target.split(maxsplit=1)[0] if raw_target else ""
            parsed = urlsplit(raw_target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue

            target_path = Path(unquote(parsed.path))
            if parsed.path.startswith("/"):
                candidate = ROOT / target_path.as_posix().lstrip("/")
            else:
                candidate = path.parent / target_path
            candidate = candidate.resolve()
            if not candidate.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: broken local link target {raw_target!r}"
                )


def main() -> int:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" not in path.parts:
            check_markdown(path)

    for path in sorted(ROOT.rglob("*.py")):
        if ".git" not in path.parts:
            check_python(path)

    for suffix in ("*.yaml", "*.yml"):
        for path in sorted(ROOT.rglob(suffix)):
            if ".git" not in path.parts:
                parse_yaml(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT)))

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"Documentation validation passed: {markdown_count} Markdown files checked; {yaml_count} YAML files/code fences parsed; {python_count} Python files syntax-checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
