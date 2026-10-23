#!/usr/bin/env python3
"""Check P004 exploratory exclusions and bounded claims, never runtime success."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

if __package__:
    from . import validate_boot_milestone as boot
    from . import validate_fidelity as fidelity
else:
    import validate_boot_milestone as boot
    import validate_fidelity as fidelity

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/scope.json")
SPECIFICATION = Path("docs/EXPLORATORY_SCOPE.md")
REFERENCES = Path("docs/REFERENCES.md")
PUBLICATIONS = (
    "README.md", "ROADMAP_365_PHASES.md", "docs/ARCHITECTURE.md",
    "docs/LINUX_BOOT_MILESTONE.md", str(SPECIFICATION),
)
DECLARATION = (
    "> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are "
    "exploratory, unimplemented and not required."
)
OPTIONAL = "**Scope:** exploratory; not required for v0.1."
CAPABILITIES = {
    "cycle-accuracy": "Cycle accuracy",
    "gpu-graphics": "GPU graphics",
    "unmodified-macos": "Unmodified macOS",
}
RELATED_PHASES = {
    "cycle-accuracy": ["P102", "P344"],
    "gpu-graphics": [f"P{number}" for number in range(286, 301)],
    "unmodified-macos": [f"P{number}" for number in range(301, 316)],
}
QEMU_REVISION = "4fc49f46dc95d4a27de2509e7fceb2931e91faeb"
ASAHI_REVISION = "0d1f8917fa88745d62a4c05d802c4a7298c8616b"
SOURCES = {
    "qemu-icount": f"https://github.com/qemu/qemu/blob/{QEMU_REVISION}/docs/devel/tcg-icount.rst",
    "asahi-agx": f"https://github.com/AsahiLinux/docs/blob/{ASAHI_REVISION}/docs/hw/soc/agx.md",
    "apple-boot": "https://support.apple.com/en-ca/guide/security/secac71d5623/web",
    "qemu-vmapple": f"https://github.com/qemu/qemu/blob/{QEMU_REVISION}/docs/system/arm/vmapple.rst",
}
CAPABILITY_SOURCES = {
    "cycle-accuracy": ["qemu-icount"],
    "gpu-graphics": ["asahi-agx"],
    "unmodified-macos": ["apple-boot", "qemu-vmapple"],
}
FIELDS = {
    "id", "title", "required_for_v0_1", "implemented", "boundary",
    "allowed_research", "promotion_evidence", "related_phases", "sources",
}


def _members(value: object, expected: object) -> bool:
    return (isinstance(value, list)
            and all(isinstance(item, str) for item in value)
            and len(value) == len(expected) and set(value) == set(expected))


def _text(value: object) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and not any(unicodedata.category(char).startswith("C") or char in "|\u2028\u2029"
                        for char in value))


def validate(raw: object) -> list[str]:
    """Validate the closed P004 policy; false is a boolean, not zero or a string."""
    if not isinstance(raw, dict):
        return ["scope policy must be an object"]
    errors: list[str] = []
    if set(raw) != {"schema_version", "release", "success_gate", "capabilities", "gate_exclusions", "sources"}:
        errors.append("policy must contain exactly schema_version, release, success_gate, capabilities, gate_exclusions and sources")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        errors.append("schema_version: expected integer 1")
    for key, expected in (("release", "v0.1"), ("success_gate", "G4")):
        if raw.get(key) != expected:
            errors.append(f"{key}: expected {expected!r}")
    if raw.get("sources") != SOURCES:
        errors.append("sources: expected the four reviewed primary-source URLs and immutable evidence revisions")
    entries = raw.get("capabilities")
    if not isinstance(entries, list):
        errors.append("capabilities: expected an array")
    else:
        seen = []
        for index, entry in enumerate(entries):
            location = f"capabilities[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{location}: expected an object")
                continue
            if set(entry) != FIELDS:
                errors.append(f"{location}: expected exactly {', '.join(sorted(FIELDS))}")
            identifier = entry.get("id")
            known = isinstance(identifier, str) and identifier in CAPABILITIES
            if not known:
                errors.append(f"{location}.id: unknown capability {identifier!r}")
            else:
                seen.append(identifier)
                location = identifier
                if entry.get("title") != CAPABILITIES[identifier]:
                    errors.append(f"{location}.title: expected {CAPABILITIES[identifier]!r}")
                if not _members(entry.get("related_phases"), RELATED_PHASES[identifier]):
                    errors.append(f"{location}.related_phases: expected exactly the reviewed related phases")
                if not _members(entry.get("sources"), CAPABILITY_SOURCES[identifier]):
                    errors.append(f"{location}.sources: expected exactly the relevant primary-source IDs")
            for flag in ("required_for_v0_1", "implemented"):
                if entry.get(flag) is not False:
                    errors.append(f"{location}.{flag}: must be boolean false; P004 grants no implementation or release requirement")
            for field in ("title", "boundary", "allowed_research", "promotion_evidence"):
                value = entry.get(field)
                if not _text(value):
                    errors.append(f"{location}.{field}: expected visible nonempty single-line text without pipes")
                else:
                    errors.extend(audit_claims(value, f"{location}.{field}"))
        for identifier in CAPABILITIES:
            if seen.count(identifier) != 1:
                errors.append(f"capabilities: expected {identifier} exactly once, found {seen.count(identifier)}")
    gates = raw.get("gate_exclusions")
    if not isinstance(gates, dict) or set(gates) != set(fidelity.GATES):
        errors.append("gate_exclusions: expected all and only G0-G6 and P361-P365")
    if isinstance(gates, dict):
        for identifier in fidelity.GATES:
            if not _members(gates.get(identifier), CAPABILITIES):
                errors.append(f"gate_exclusions.{identifier}: must exclude all three exploratory capabilities exactly once")
    return errors


def render_contract(raw: dict) -> str:
    """Render a validated policy for a reviewable, drift-checked specification."""
    blocks = []
    for entry in raw["capabilities"]:
        phases = ", ".join(f"`{phase}`" for phase in entry["related_phases"])
        sources = ", ".join(f"[{key}]({raw['sources'][key]})" for key in entry["sources"])
        blocks.append(
            f"### {entry['id']} — {entry['title']}\n\n"
            "**Required for v0.1:** no. **Implemented:** no.\n\n"
            f"**Boundary:** {entry['boundary']}\n\n"
            f"**Allowed research:** {entry['allowed_research']}\n\n"
            f"**Evidence before changing this policy:** {entry['promotion_evidence']}\n\n"
            f"**Related roadmap phases:** {phases}.\n\n**Sources:** {sources}."
        )
    lines = ["### Gate exclusion inventory", "",
             "| Gate | Excluded capabilities; no implementation credit |", "|---|---|"]
    for identifier, excluded in raw["gate_exclusions"].items():
        lines.append(f"| {identifier} | {', '.join(f'`{item}`' for item in excluded)} |")
    return "\n\n".join(blocks) + "\n\n" + "\n".join(lines)


# This is a bounded contradiction lint, not an English-language theorem prover.
# Structured exclusions, publication matching and human milestone review remain
# necessary; P014 owns the broader release compatibility-language audit.
FEATURES = re.compile(
    r"\b(?:cycle[ -]accur(?:acy|ate)|(?:firestorm|icestorm) (?:pipeline |cycle )?timing|"
    r"native m1 (?:throughput|performance)|gpu (?:graphics|rendering|emulation|support)|"
    r"agx|macos|machine-macos)\b"
)
CLAIM = re.compile(
    r"\b(?:ships?|shipped|shipping|implements|implemented|supports|supported|"
    r"certif(?:y|ies|ied)|provides?|provided|requires|required|mandatory|"
    r"delivers?|delivered|guarantees?|guaranteed|boots|booted|runs|running|"
    r"works|working|available|enabled|passes|passed|ready)\b|"
    r"\b(?:is|are|now|status:)\s+(?:fully )?complete\b|"
    r"\b(?:will|must|shall|can|we)\s+(?:require|implement|support|boot|run)\b"
)
NEGATIVE = re.compile(
    r"\b(?:no(?!-op\b)|not|neither|nor|never|without|cannot|can't|doesn't|isn't|aren't|won't|don't|"
    r"unimplemented|unsupported|unproven|excluded|excludes?|exclusions?|"
    r"exploratory|research-only|rejects?|rejecting|forbids?|avoid|"
    r"outside (?:required |the )?v0\.1|from required v0\.1|independent of)\b"
)
FUTURE = re.compile(r"\b(?:future|eventual|prospective|proposed|hypothetical|could|would|may|might)\b")
PROJECT = re.compile(r"\b(?:v0\.1|g[0-6]|p\d{3}|this (?:repository|emulator|project)|our|we)\b")
DOUBLE_NEGATIVE = re.compile(r"\b(?:not (?:optional|excluded|exploratory|unimplemented)|no longer (?:excluded|unimplemented|optional))\b")
BOUNDED_RESEARCH = re.compile(
    r"\b(?:skeletal|discovery registers?|no-op (?:queue|job|submission)|"
    r"shader decod(?:er|ing)|arithmetic (?:shader )?kernel|independent framebuffer|fence tests?)\b"
)
BROAD_CAPABILITY = re.compile(r"\b(?:full|fully|general|graphics|rendering|renders|macos|cycle[ -]accur(?:acy|ate))\b")
GATE_REFERENCE = r"\b(?:v0\.1|g[0-6]|p36[1-5])\b"
RESEARCH_REFERENCE = r"\b(?:ws2[01]|p(?:28[6-9]|29\d|30\d|31[0-5]))\b"
DEPENDENCY = re.compile(
    GATE_REFERENCE + r".{0,70}\b(?:requires?|needs?|depends? on|blocked by|must await|waits? for)\b.{0,50}" + RESEARCH_REFERENCE
    + "|" + RESEARCH_REFERENCE + r".{0,50}\b(?:required|mandatory|prerequisite|blocker)\b.{0,50}" + GATE_REFERENCE
)


def _prose_units(text: str) -> list[tuple[int, str]]:
    """Join wrapped prose while keeping paragraphs, list items and rows apart."""
    units = []
    words = []
    first = 1
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        boundary = re.match(r"^(?:#{1,6}\s|[-+]\s|\d+\.\s|[>|])", line)
        if not line or boundary:
            if words:
                units.append((first, " ".join(words)))
                words = []
        if line:
            if not words:
                first = number
            words.append(line)
    if words:
        units.append((first, " ".join(words)))
    return units


def audit_claims(text: str, location: str) -> list[str]:
    """Catch explicit positive shipping/requirement claims, with local negation.

    Ignore code examples, comments and link destinations. A negative clause does
    not excuse a positive clause after a semicolon, conjunction or sentence.
    Source discussion and conditional future research are not current results.
    """
    errors = []
    visible = fidelity._visible_markdown(text)
    visible = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", visible)
    visible = unicodedata.normalize("NFKC", visible).casefold()
    visible = visible.translate(str.maketrans({char: "-" for char in "‐‑‒–—−"}))
    visible = re.sub(r"(?m)^( {0,3})\*\s", r"\1- ", visible)
    visible = visible.replace("’", "'").replace("`", "").replace("*", "").replace("_", "")
    for number, line in _prose_units(visible):
        for sentence in re.split(r"[;!?]|(?<!\d)\.|\.(?!\d)", line):
            context = ""
            for clause in re.split(r"\b(?:but|however|whereas|and|yet)\b|,\s*(?=not\b)|(?=\bwithout\b)", sentence):
                if DEPENDENCY.search(clause) and not NEGATIVE.search(clause):
                    errors.append(f"{location}:{number}: optional research cannot become a v0.1 prerequisite: {clause.strip()}")
                feature = FEATURES.search(clause)
                if feature:
                    context = feature.group()
                elif not context:
                    continue
                if DOUBLE_NEGATIVE.search(clause):
                    errors.append(f"{location}:{number}: exploratory capability promoted by double negation: {clause.strip()}")
                    continue
                negation_text = re.sub(r"\bnot only\b", "", clause)
                if not CLAIM.search(clause) or NEGATIVE.search(negation_text):
                    continue
                if BOUNDED_RESEARCH.search(clause) and not BROAD_CAPABILITY.search(clause):
                    continue
                if FUTURE.search(clause) and not PROJECT.search(clause):
                    continue
                # Upstream descriptions concern a different model and cannot
                # exempt an explicit claim about this project or its release.
                if re.search(r"\b(?:qemu|asahi|apple describes|apple's documentation)\b", sentence) and not PROJECT.search(sentence):
                    continue
                errors.append(f"{location}:{number}: unsupported shipped/required claim about {context}: {clause.strip()}")
    return errors


def _read(root: Path, path: Path, errors: list[str]) -> str | None:
    try:
        return (root / path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read file: {exc}")
        return None


def _json(root: Path, path: Path, errors: list[str]) -> object:
    text = _read(root, path, errors)
    if text is None:
        return None
    try:
        return json.loads(text, object_pairs_hook=fidelity._unique_object)
    except ValueError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return None


def validate_repository(root: Path = ROOT) -> list[str]:
    """Check policy, published scope, all milestones and optional research paths."""
    errors: list[str] = []
    raw = _json(root, MANIFEST, errors)
    if errors:
        return errors
    errors.extend(f"{MANIFEST}: {error}" for error in validate(raw))
    if errors:
        return errors
    documents: dict[str, str] = {}
    # Discover new root/docs Markdown too: a new release note cannot silently
    # bypass the claim lint. Vendor sources and test fixtures are not publications.
    paths = set(PUBLICATIONS) | {str(REFERENCES)}
    paths.update(str(path.relative_to(root)) for path in root.glob("*.md"))
    paths.update(str(path.relative_to(root)) for path in (root / "docs").rglob("*.md"))
    for name in sorted(paths):
        content = _read(root, Path(name), errors)
        if content is not None:
            documents[name] = fidelity._visible_markdown(content)
            errors.extend(audit_claims(content, name))
    for name in PUBLICATIONS:
        visible = documents.get(name, "")
        declarations = re.findall(r"^\s*> v0\.1 scope:.*$", visible, re.MULTILINE)
        if [line.strip() for line in declarations] != [DECLARATION]:
            errors.append(f"{name}: expected exactly one visible P004 scope declaration")
    specification = documents.get(str(SPECIFICATION), "")
    if specification.count(render_contract(raw)) != 1:
        errors.append(f"{SPECIFICATION}: expected one visible manifest-matching scope contract")
    references = documents.get(str(REFERENCES), "")
    for key, url in SOURCES.items():
        if f"]({url})" not in references:
            errors.append(f"{REFERENCES}: missing visible primary source {key}")
    roadmap = documents.get("ROADMAP_365_PHASES.md", "")
    for identifier in RELATED_PHASES["gpu-graphics"] + RELATED_PHASES["unmodified-macos"]:
        rows = re.findall(rf"^- \[[ x]\] \*\*{identifier} — [^*]+\*\* — .+$", roadmap, re.MULTILINE)
        if len(rows) != 1 or rows[0].count("**Scope:**") != 1 or not rows[0].endswith(OPTIONAL):
            errors.append(f"ROADMAP_365_PHASES.md: {identifier} must remain explicitly optional research")
    # Reuse earlier contracts so coordinated JSON/prose edits cannot weaken the
    # G4 witness or award machine-macos to a v0.1 gate.
    errors.extend(fidelity.validate_repository(root))
    errors.extend(boot.validate_repository(root))
    gates = _json(root, fidelity.MANIFEST, errors)
    if isinstance(gates, dict) and not fidelity.validate(gates):
        for gate in gates["gates"]:
            for field in ("test", "scope"):
                errors.extend(audit_claims(gate[field], f"{fidelity.MANIFEST}:{gate['id']}.{field}"))
            test = gate["test"].casefold()
            if FEATURES.search(test) and not NEGATIVE.search(test):
                errors.append(f"{fidelity.MANIFEST}:{gate['id']}.test: exploratory capability cannot become a required observable")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository snapshot to validate")
    args = parser.parse_args()
    errors = validate_repository(args.root)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P004 scope: 3 exploratory exclusions, 12 bounded gates and 30 optional research phases")
        print("No runtime gate, GPU graphics, macOS compatibility or cycle accuracy is certified by this check")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
