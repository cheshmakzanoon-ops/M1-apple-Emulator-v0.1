#!/usr/bin/env python3
"""Enforce the numbering, specificity, and exactly-365 phase contract."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "ROADMAP_365_PHASES.md"
PHASE = re.compile(r"^- \[([ x])\] \*\*P(\d{3}) — ([^*]+)\*\* — (.+)$", re.MULTILINE)
STREAM = re.compile(r"^## WS(\d{2}) — (.+)$", re.MULTILINE)


def validate(text: str) -> list[str]:
    errors: list[str] = []
    matches = list(PHASE.finditer(text))
    numbers = [int(m.group(2)) for m in matches]
    if numbers != list(range(1, 366)):
        errors.append("phase IDs must appear in order P001..P365 exactly once")
    titles = [m.group(3).strip().lower() for m in matches]
    if len(titles) != len(set(titles)):
        errors.append("phase titles must be unique")
    for m in matches:
        if len(m.group(3).strip()) < 12 or len(m.group(4).strip()) < 22:
            errors.append(f"P{m.group(2)}: title or verification description is too short")
        if "**Check:**" not in m.group(4):
            errors.append(f"P{m.group(2)}: missing a testable completion criterion")
    streams = [int(m.group(1)) for m in STREAM.finditer(text)]
    if streams != list(range(1, 25)):
        errors.append("expected exactly WS01..WS24 workstreams in order")
    if len(matches) != 365:
        errors.append(f"expected 365 phases, found {len(matches)}")
    return errors


def main() -> int:
    if not ROADMAP.is_file():
        print("ERROR: roadmap is missing")
        return 1
    errors = validate(ROADMAP.read_text(encoding="utf-8"))
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid roadmap: 24 workstreams and 365 unique, verifiable phases")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
