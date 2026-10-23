#!/usr/bin/env python3
"""Check the P002 fidelity policy; this does not certify emulator behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/fidelity.json")
ARCHITECTURE = Path("docs/ARCHITECTURE.md")
ROADMAP = Path("ROADMAP_365_PHASES.md")
LEVELS = {
    "toolchain": "Toolchain validation",
    "isa": "ISA accuracy",
    "apple-cpu": "Apple CPU profile",
    "peripheral": "T8103 peripheral accuracy",
    "machine-linux": "Whole-machine Linux compatibility",
    "machine-macos": "Whole-machine macOS compatibility",
    "evidence-audit": "Evidence and release audit",
}
GATES = {
    "G0": ("toolchain",),
    "G1": ("isa", "apple-cpu"),
    "G2": ("peripheral",),
    "G3": ("isa", "apple-cpu", "peripheral"),
    "G4": ("machine-linux",),
    "G5": ("peripheral",),
    "G6": ("machine-linux", "peripheral"),
    "P361": ("isa", "apple-cpu", "peripheral"),
    "P362": ("isa", "apple-cpu", "peripheral"),
    "P363": ("machine-linux",),
    "P364": ("evidence-audit",),
    "P365": ("evidence-audit",),
}
LEVEL_FIELDS = {"id", "title", "definition", "evidence", "exclusions"}
GATE_FIELDS = {"id", "levels", "kind", "test", "scope"}


def _text(value: object) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and not any(char in value for char in "\r\n|"))


def validate(raw: object) -> list[str]:
    """Validate policy structure and fixed scope boundaries, not prose truth."""
    if not isinstance(raw, dict):
        return ["fidelity policy must be an object"]
    errors: list[str] = []
    if set(raw) != {"schema_version", "levels", "gates"}:
        errors.append("policy fields must be exactly schema_version, levels and gates")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        errors.append("schema_version: expected integer 1")
    for field, inventory, fields in (
        ("levels", LEVELS, LEVEL_FIELDS), ("gates", GATES, GATE_FIELDS),
    ):
        entries = raw.get(field)
        if not isinstance(entries, list):
            errors.append(f"{field}: expected an array")
            continue
        seen: list[str] = []
        for index, entry in enumerate(entries):
            location = f"{field}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{location}: expected an object")
                continue
            if set(entry) != fields:
                errors.append(f"{location}: expected exactly {', '.join(sorted(fields))}")
            identifier = entry.get("id")
            if not isinstance(identifier, str) or identifier not in inventory:
                errors.append(f"{location}.id: unknown identifier {identifier!r}")
            else:
                seen.append(identifier)
                location = identifier
            for name in sorted(fields - {"levels"}):
                if not _text(entry.get(name)):
                    errors.append(f"{location}.{name}: expected nonempty single-line text without pipes")
            if field == "levels":
                if isinstance(identifier, str) and identifier in LEVELS:
                    if entry.get("title") != LEVELS[identifier]:
                        errors.append(f"{location}.title: expected {LEVELS[identifier]!r}")
            else:
                if isinstance(identifier, str) and identifier in GATES:
                    if entry.get("levels") != list(GATES[identifier]):
                        errors.append(f"{location}.levels: expected exactly {list(GATES[identifier])!r}")
                    kind = "development" if identifier.startswith("G") else "release"
                    if entry.get("kind") != kind:
                        errors.append(f"{location}.kind: expected {kind!r}")
                elif not isinstance(entry.get("levels"), list):
                    errors.append(f"{location}.levels: expected an array")
        for identifier in inventory:
            if seen.count(identifier) != 1:
                errors.append(f"{field}: expected {identifier} exactly once, found {seen.count(identifier)}")
    return errors


def render_levels(raw: dict) -> str:
    """Render a validated manifest's independent definitions in declared order."""
    return "\n\n".join(
        f"### `{level['id']}` — {level['title']}\n\n"
        f"**Definition:** {level['definition']}\n\n"
        f"**Required evidence:** {level['evidence']}\n\n"
        f"**Does not establish:** {level['exclusions']}"
        for level in raw["levels"]
    )


def _level_list(levels: list[str] | tuple[str, ...]) -> str:
    return ", ".join(f"`{level}`" for level in levels)


def render_gates(raw: dict, kind: str) -> str:
    """Render a validated manifest's development or formal release gate table."""
    lines = ["| Gate | Required observable test | Fidelity levels | Claim boundary |",
             "|---|---|---|---|"]
    lines.extend(
        f"| {gate['id']} | {gate['test']} | {_level_list(gate['levels'])} | {gate['scope']} |"
        for gate in raw["gates"] if gate["kind"] == kind
    )
    return "\n".join(lines)


def _visible_markdown(text: str) -> str:
    """Exclude HTML comments and fenced code from declarations we can count."""
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)
    visible: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not suffix.strip():
                fence = ""
            visible.append("")
        elif fence:
            visible.append("")
        else:
            visible.append(line)
    return "\n".join(visible)


def _read(root: Path, relative: Path, errors: list[str]) -> str | None:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: cannot read file: {exc}")
        return None


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def validate_repository(root: Path = ROOT) -> list[str]:
    """Require visible published definitions and all twelve gate classifications."""
    errors: list[str] = []
    content = _read(root, MANIFEST, errors)
    if content is None:
        return errors
    try:
        raw = json.loads(content, object_pairs_hook=_unique_object)
    except ValueError as exc:
        return [f"{MANIFEST}: invalid JSON: {exc}"]
    errors.extend(f"{MANIFEST}: {error}" for error in validate(raw))
    if errors:
        return errors
    architecture = _read(root, ARCHITECTURE, errors)
    if architecture is not None:
        visible = _visible_markdown(architecture)
        for name, expected in (
            ("level definitions", render_levels(raw)),
            ("development gate table", render_gates(raw, "development")),
            ("release gate table", render_gates(raw, "release")),
        ):
            if visible.count(expected) != 1:
                errors.append(f"{ARCHITECTURE}: expected one visible, manifest-matching {name}")
        definitions = re.findall(r"^### `([^`]+)` — ", visible, re.MULTILINE)
        for identifier in LEVELS:
            if definitions.count(identifier) != 1:
                errors.append(f"{ARCHITECTURE}: definition {identifier} must appear exactly once")
        for identifier in set(definitions) - set(LEVELS):
            errors.append(f"{ARCHITECTURE}: unknown fidelity definition {identifier}")
        gates = re.findall(r"^\| ((?:G\d+|P\d{3})) \|", visible, re.MULTILINE)
        for identifier in GATES:
            if gates.count(identifier) != 1:
                errors.append(f"{ARCHITECTURE}: gate {identifier} must appear exactly once")
        for identifier in set(gates) - set(GATES):
            errors.append(f"{ARCHITECTURE}: unknown fidelity gate {identifier}")
    roadmap = _read(root, ROADMAP, errors)
    if roadmap is not None:
        visible = _visible_markdown(roadmap)
        for identifier, levels in GATES.items():
            if not identifier.startswith("P"):
                continue
            lines = re.findall(rf"^- \[[ x]\] \*\*{identifier} — [^*]+\*\* — .+$",
                               visible, re.MULTILINE)
            annotation = f"**Fidelity:** {_level_list(levels)}."
            if len(lines) != 1 or lines[0].count("**Fidelity:**") != 1 or not lines[0].endswith(annotation):
                errors.append(f"{ROADMAP}: {identifier} needs exactly one visible phase and {annotation}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository snapshot to validate")
    args = parser.parse_args()
    errors = validate_repository(args.root)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P002 fidelity policy: 7 independent classifications and 12 scoped gates")
        print("Published definitions and G0-G6 / P361-P365 agree with the policy")
        print("This check does not establish passed runtime gates or hardware compatibility")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
