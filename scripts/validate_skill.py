#!/usr/bin/env python3
"""Validate the Skill package before release or pull request."""
from __future__ import annotations

import argparse
import py_compile
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bpostgres(?:ql)?://[^/\s:@]+:[^@\s]+@", re.I),
]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".ps1", ".json", ".txt"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"\'')
    return result


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_file = root / "SKILL.md"
    if not skill_file.is_file():
        return [f"missing SKILL.md: {skill_file}"]

    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"SKILL.md is not UTF-8: {exc}"]

    frontmatter = parse_frontmatter(text)
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not NAME_RE.fullmatch(name):
        fail(errors, f"invalid skill name: {name!r}")
    if name != root.name:
        fail(errors, f"skill name must match folder name: {name!r} != {root.name!r}")
    if len(description) < 20:
        fail(errors, "frontmatter description is missing or too short")

    for required in ("README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md"):
        if not (root / required).is_file():
            fail(errors, f"missing release file: {required}")

    for markdown in root.rglob("*.md"):
        if any(part == ".git" for part in markdown.parts):
            continue
        try:
            body = markdown.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            fail(errors, f"non-UTF-8 markdown: {markdown.relative_to(root)}: {exc}")
            continue
        for raw_target in LINK_RE.findall(body):
            target = raw_target.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "codex://")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if re.match(r"^[A-Za-z]:[\\/]", target):
                continue
            candidate = (markdown.parent / target).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                fail(errors, f"link escapes repository: {markdown.relative_to(root)} -> {raw_target}")
                continue
            if not candidate.exists():
                fail(errors, f"broken link: {markdown.relative_to(root)} -> {raw_target}")

    for source in root.rglob("*.py"):
        if "__pycache__" in source.parts:
            continue
        try:
            py_compile.compile(str(source), doraise=True)
        except py_compile.PyCompileError as exc:
            fail(errors, f"python compile failed: {source.relative_to(root)}: {exc.msg}")

    for source in root.rglob("*"):
        if not source.is_file() or source.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", "__pycache__"} for part in source.parts):
            continue
        try:
            body = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(body):
                fail(errors, f"possible secret in {source.relative_to(root)}: {pattern.pattern}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    errors = validate(root)
    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Skill validation passed: {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
