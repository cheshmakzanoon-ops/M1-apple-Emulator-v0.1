#!/usr/bin/env python3
"""Validate the P003 G4 acceptance contract, never a runtime gate result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

if __package__:
    from .validate_fidelity import _unique_object, _visible_markdown
else:
    from validate_fidelity import _unique_object, _visible_markdown

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/boot-milestone.json")
SPECIFICATION = Path("docs/LINUX_BOOT_MILESTONE.md")
REFERENCES = Path("docs/REFERENCES.md")
LINUX_REVISION = "adc218676eef25575469234709c2d87185ca223a"
ASAHI_REVISION = "0d1f8917fa88745d62a4c05d802c4a7298c8616b"
SUCCESS = "T8103-targeted Linux reaches BusyBox shell via Apple UART/AIC"
TARGET = {
    "soc": "T8103", "board": "J274", "machine": "apple-m1-lab",
    "accelerator": "tcg", "boot_mode": "laboratory-direct", "architecture": "aarch64",
    "linux_compatible": ["apple,j274", "apple,t8103", "apple,arm-platform"],
    "console": "ttySAC0", "serial_driver": "samsung-uart", "root_filesystem": "BusyBox initramfs",
}
PREREQUISITES = {
    "G0": ["P016-P045"], "G1": ["P046-P120"], "G2": ["P121-P135"],
    "G3": ["P136-P180"], "boot-handoff": ["P181-P195"], "linux-integration": ["P196-P209"],
}
WITNESS = {
    "profile": "linux-v6.12-observables-v1",
    "guest_script": "experiments/linux-boot-witness/probe.sh",
    "checker": "tools/check_g4_transcript.py", "guest_script_path": "/g4-probe.sh",
    "binding_helper": "experiments/linux-boot-witness/serial-binding.sh",
    "binding_helper_path": "/g4-serial-binding.sh",
    "cold_boots": 3, "online_cpus": 1, "boot_timeout_seconds": 300,
    "interaction_timeout_seconds": 30, "guest_sleep_seconds": 1,
    "nonce_hex_characters": 32, "operand_min": 1, "operand_max": 999999,
    "shell_followup": "product-after-probe",
    "uart_irq_chip": "AIC", "uart_irq_action": "235200000.serial",
    "timer_irq_chip": "AIC-FIQ", "timer_irq_action": "arch_timer",
}
OBSERVATIONS = (
    "fresh-process", "interactive-shell", "active-drivers", "uart-irq",
    "timer-fiq", "bounded-run", "reviewed-evidence",
)
EVIDENCE_FIELDS = {
    "source": ["repository_url", "commit", "patch_series_sha256", "configuration_sha256"],
    "artifact": ["relative_path", "size_bytes", "sha256"],
    "host": ["os", "architecture", "compiler_versions", "build_commands", "environment"],
    "invocation": ["argv", "cwd", "machine", "cpu_profile", "memory_layout", "boot_mode",
                   "kernel_cmdline", "entry_state", "device_inventory", "shortcuts"],
    "prerequisite": ["id", "revision", "command", "result", "evidence_sha256", "limitations"],
    "run": ["id", "fresh_process", "nonce", "left", "right", "serial_sha256",
            "host_events_sha256", "stderr_sha256", "elapsed_seconds", "termination_reason", "checker_result"],
    "review": ["reviewer", "date", "prerequisite_review", "device_route_review", "limitations", "verdict"],
}
ARTIFACTS = (
    "qemu-binary", "linux-image", "linux-config", "linux-patch-series", "dtb", "dt-sources",
    "dt-patch-series", "busybox-binary", "busybox-config", "initramfs", "init-script",
    "probe-script", "serial-binding-script", "build-manifest",
)
EXCLUSIONS = (
    "virt", "vmapple", "PL011", "GIC", "virtio-console", "semihosting-console",
    "snapshot-resume", "host-root-filesystem",
)
LINUX_SOURCES = {
    "linux_boot": "Documentation/arch/arm64/booting.rst",
    "linux_j274": "arch/arm64/boot/dts/apple/t8103-j274.dts",
    "linux_t8103": "arch/arm64/boot/dts/apple/t8103.dtsi",
    "linux_uart": "drivers/tty/serial/samsung_tty.c",
    "linux_serial_core": "drivers/tty/serial/serial_core.c",
    "linux_serial_bus": "drivers/tty/serial/serial_base_bus.c",
    "linux_irq_proc": "kernel/irq/proc.c",
    "linux_aic": "drivers/irqchip/irq-apple-aic.c",
    "linux_timer": "drivers/clocksource/arm_arch_timer.c",
    "linux_initramfs": "Documentation/filesystems/ramfs-rootfs-initramfs.rst",
}
SOURCES = {
    key: f"https://github.com/torvalds/linux/blob/{LINUX_REVISION}/{path}"
    for key, path in LINUX_SOURCES.items()
} | {
    "asahi_aic": f"https://github.com/AsahiLinux/docs/blob/{ASAHI_REVISION}/docs/hw/soc/aic.md",
    "busybox": "https://busybox.net/downloads/BusyBox.html",
}


def _exact(actual: object, expected: object, location: str) -> list[str]:
    """Compare JSON policy values without equating true, 1 and 1.0."""
    if type(actual) is not type(expected):
        return [f"{location}: expected {expected!r}"]
    if isinstance(expected, dict):
        errors = [] if set(actual) == set(expected) else [f"{location}: missing or unknown fields"]
        for key, value in expected.items():
            errors.extend(_exact(actual.get(key), value, f"{location}.{key}"))
        return errors
    if isinstance(expected, list):
        if len(actual) != len(expected):
            return [f"{location}: expected {expected!r}"]
        return [error for index, (left, right) in enumerate(zip(actual, expected))
                for error in _exact(left, right, f"{location}[{index}]")]
    return [] if actual == expected else [f"{location}: expected {expected!r}"]


def _prose(value: object) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and not any(ord(char) < 32 or char in "|<>" for char in value))


def validate(raw: object) -> list[str]:
    """Check frozen identity, dependencies, observations and evidence requirements."""
    if not isinstance(raw, dict):
        return ["boot milestone must be an object"]
    fixed = {
        "schema_version": 1, "phase": "P003", "gate": "G4", "fidelity": ["machine-linux"],
        "success_criterion": SUCCESS, "target": TARGET, "witness": WITNESS,
        "evidence_fields": EVIDENCE_FIELDS, "required_artifacts": list(ARTIFACTS),
        "excluded_substitutes": list(EXCLUSIONS), "sources": SOURCES,
    }
    errors = []
    if set(raw) != set(fixed) | {"prerequisites", "observations"}:
        errors.append("contract: missing or unknown fields; runtime success/status does not belong here")
    for name, expected in fixed.items():
        errors.extend(_exact(raw.get(name), expected, name))
    for field, identifiers, text_field in (
        ("prerequisites", tuple(PREREQUISITES), "evidence"),
        ("observations", OBSERVATIONS, "requirement"),
    ):
        entries = raw.get(field)
        if not isinstance(entries, list):
            errors.append(f"{field}: expected an array")
            continue
        seen = []
        required = {"id", text_field} | ({"phases"} if field == "prerequisites" else set())
        for index, entry in enumerate(entries):
            location = f"{field}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{location}: expected an object")
                continue
            if set(entry) != required:
                errors.append(f"{location}: missing or unknown fields")
            identifier = entry.get("id")
            if not isinstance(identifier, str) or identifier not in identifiers:
                errors.append(f"{location}.id: unknown identifier")
            else:
                seen.append(identifier)
                if field == "prerequisites":
                    errors.extend(_exact(entry.get("phases"), PREREQUISITES[identifier], f"{location}.phases"))
            if not _prose(entry.get(text_field)):
                errors.append(f"{location}.{text_field}: expected visible single-line prose")
        if seen != list(identifiers):
            errors.append(f"{field}: expected each of {', '.join(identifiers)} once in order")
    return errors


def render_contract(raw: dict) -> str:
    """Render the complete visible policy block from an already validated manifest."""
    rows = ["### Frozen profile", "", "| Field | Requirement |", "|---|---|"]
    for key in ("phase", "gate", "fidelity", "success_criterion"):
        value = raw[key]
        rows.append(f"| {key} | {', '.join(value) if isinstance(value, list) else value} |")
    for section in ("target", "witness"):
        for key, value in raw[section].items():
            rows.append(f"| {section}.{key} | {', '.join(value) if isinstance(value, list) else value} |")
    rows.extend(["", "### Prerequisite evidence", "", "| ID | Roadmap owners | Required evidence |", "|---|---|---|"])
    rows.extend(f"| {entry['id']} | {', '.join(entry['phases'])} | {entry['evidence']} |"
                for entry in raw["prerequisites"])
    rows.extend(["", "### Required observations", "", "| ID | Requirement |", "|---|---|"])
    rows.extend(f"| {entry['id']} | {entry['requirement']} |" for entry in raw["observations"])
    rows.extend(["", "### Evidence record fields", "", "| Record | Required fields |", "|---|---|"])
    rows.extend(f"| {key} | {', '.join(value)} |" for key, value in raw["evidence_fields"].items())
    rows.extend(["", "Required hashed artifacts: " + ", ".join(raw["required_artifacts"]) + ".",
                 "", "Excluded substitutes: " + ", ".join(raw["excluded_substitutes"]) + "."])
    return "\n".join(rows)


def _read(root: Path, relative: Path, errors: list[str]) -> str | None:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative}: cannot read file: {exc}")
        return None


def validate_repository(root: Path = ROOT) -> list[str]:
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
    specification = _read(root, SPECIFICATION, errors)
    if specification is not None:
        visible = _visible_markdown(specification)
        if visible.count(render_contract(raw)) != 1:
            errors.append(f"{SPECIFICATION}: expected exactly one visible manifest-matching contract")
        for heading in ("Frozen profile", "Prerequisite evidence", "Required observations", "Evidence record fields"):
            if len(re.findall(rf"^### {heading}$", visible, re.MULTILINE)) != 1:
                errors.append(f"{SPECIFICATION}: expected one {heading} section")
    references = _read(root, REFERENCES, errors)
    if references is not None:
        visible = _visible_markdown(references)
        for identifier, url in raw["sources"].items():
            if f"]({url})" not in visible:
                errors.append(f"{REFERENCES}: missing visible primary source {identifier}")
    for key in ("guest_script", "binding_helper", "checker"):
        content = _read(root, Path(raw["witness"][key]), errors)
        if content is not None and not content.strip():
            errors.append(f"{raw['witness'][key]}: empty witness implementation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository snapshot to validate")
    args = parser.parse_args()
    errors = validate_repository(args.root)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P003 contract: G4 prerequisites, bounded witness and evidence requirements agree")
        print("This is a specification check; it does not establish a passed G4 or an M1 Linux boot")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
