#!/usr/bin/env python3
"""Verify P001 target declarations, not free prose or hardware compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAP_RELATIVE = Path("hardware/t8103.json")
ENTRYPOINTS = (
    "README.md", "ROADMAP_365_PHASES.md", "AGENTS.md",
    "docs/ARCHITECTURE.md", "docs/DEVELOPMENT.md", "docs/REFERENCES.md",
)
DECLARATION = "> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274."
IDENTITY = {
    "chip": "Apple M1", "soc": "T8103",
    "reference_board": "J274 (2020 M1 Mac mini)",
}
TARGET_IDENTITY = {
    "internal_name": "H13G", "board_id": "J274",
    "board_name": "Mac mini (M1, 2020)", "model_identifier": "Macmini9,1",
    "product_identifier": "J274AP",
    "linux_compatible": ["apple,j274", "apple,t8103", "apple,arm-platform"],
    "other_boards": "excluded",
}
IDENTITY_SOURCES = (
    "linux_apple_binding", "linux_j274", "asahi_devices",
    "asahi_soc_codenames", "apple_mac_mini_2020",
)
EXCLUDED_SOCS = {
    "T6000": "Apple M1 Pro", "T6001": "Apple M1 Max", "T6002": "Apple M1 Ultra",
}
EXCLUDED_BOARDS = ("J293", "J313", "J456", "J457")
EXCLUDED_FAMILIES = ("M2 and later M-series", "A-series")


def _same_members(value: object, expected: tuple[str, ...]) -> bool:
    return (isinstance(value, list)
            and all(isinstance(item, str) for item in value)
            and len(value) == len(expected) and set(value) == set(expected))


def _https_url(value: object) -> bool:
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and (parsed.port is None or 1 <= parsed.port <= 65535))
    except ValueError:
        return False


def validate(raw: object) -> list[str]:
    """Check the fixed original-M1/J274 identity and its sourced exclusions."""
    if not isinstance(raw, dict):
        return ["hardware metadata must be an object"]
    errors: list[str] = []
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        errors.append("schema_version: expected integer 1")
    for field, expected in IDENTITY.items():
        if raw.get(field) != expected:
            errors.append(f"{field}: expected {expected!r}, got {raw.get(field)!r}")
    target = raw.get("target")
    if not isinstance(target, dict):
        return errors + ["target must be an object"]
    for field, expected in TARGET_IDENTITY.items():
        if target.get(field) != expected:
            errors.append(f"target.{field}: expected {expected!r}, got {target.get(field)!r}")
    for field, expected in (
        ("identity_sources", IDENTITY_SOURCES),
        ("excluded_t8103_boards", EXCLUDED_BOARDS),
        ("excluded_families", EXCLUDED_FAMILIES),
    ):
        if not _same_members(target.get(field), expected):
            errors.append(f"target.{field}: expected exactly {list(expected)!r}, without duplicates")
    if target.get("excluded_soc_variants") != EXCLUDED_SOCS:
        errors.append(f"target.excluded_soc_variants: expected {EXCLUDED_SOCS!r}; T8103 is not excluded")
    boards = target.get("excluded_t8103_boards")
    if isinstance(boards, list) and "J274" in boards:
        errors.append("target.excluded_t8103_boards: selected board J274 must not be excluded")
    sources = raw.get("sources")
    if not isinstance(sources, dict):
        return errors + ["sources must be an object containing identity source URLs"]
    for key in IDENTITY_SOURCES:
        if not _https_url(sources.get(key)):
            errors.append(f"sources.{key}: expected a valid HTTPS URL")
    return errors


def _declarations(text: str) -> list[str]:
    """Find declarations outside Markdown fenced code and HTML comments."""
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)
    declarations: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not suffix.strip():
                fence = ""
            continue
        if not fence and line.lstrip().startswith("> Research target:"):
            declarations.append(line)
    return declarations


def validate_repository(root: Path = ROOT) -> list[str]:
    """Check metadata and the explicit six-entrypoint declaration inventory."""
    errors: list[str] = []
    path = root / MAP_RELATIVE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{MAP_RELATIVE}: cannot read metadata: {exc}")
    else:
        errors.extend(f"{MAP_RELATIVE}: {error}" for error in validate(raw))
    for entrypoint in ENTRYPOINTS:
        try:
            text = (root / entrypoint).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{entrypoint}: cannot read entrypoint: {exc}")
            continue
        declarations = _declarations(text)
        if declarations != [DECLARATION]:
            errors.append(f"{entrypoint}: expected exactly one visible declaration: {DECLARATION}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (defaults to this checkout)")
    args = parser.parse_args()
    errors = validate_repository(args.root)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P001 target: Apple M1 (T8103/H13G), Mac mini (M1, 2020), J274")
        print(f"Identity metadata and {len(ENTRYPOINTS)} entrypoint declarations agree; exclusions verified")
        print("This check does not prove hardware implementation or emulation compatibility")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
