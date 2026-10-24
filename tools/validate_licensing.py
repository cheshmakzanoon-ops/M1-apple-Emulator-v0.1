#!/usr/bin/env python3
"""Check the reviewed P006 source inventory, not authorship or legal compliance."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/licensing.json")
MIT_SHA256 = "13ef9712858d6db6ea516ac6e4ff2d1d542d10106af462c1a9772cfcf6aae6e9"
BOUNDARIES = {
    "qemu_derived": "separate-gpl-review-required",
    "apple_proprietary": "do-not-redistribute",
    "third_party_material": "review-before-import",
    "reference_documents": "links-and-original-summaries-only",
}
# This is a deliberately bounded source-only gate. Third-party source imports
# and binary packages need a new reviewed inventory, not an MIT list entry.
REQUIRED_DEPENDENCIES = {
    "qemu": "external-tool",
    "qemu-firmware": "external-runtime-data",
    "python": "external-tool",
    "gnu-toolchain": "external-tool",
    "qemu-build-dependencies": "external-tool",
    "host-environment": "external-tool",
    "github-actions": "external-tool",
    "linux": "research-reference",
    "busybox": "future-guest",
    "asahi-docs": "research-reference",
    "m1n1": "research-reference",
    "vendor-documents": "research-reference",
}
REVIEWED_INPUTS = {
    ".github/workflows/verify.yml",
    "CONTRIBUTING.md",
    "docs/DEVELOPMENT.md",
    "tools/setup_qemu.sh",
    "tools/run_arm64_smoke.py",
    "tools/validate_branch_policy.py",
    "experiments/arm64-virt-smoke/Makefile",
    "experiments/linux-boot-witness/probe.sh",
    "experiments/linux-boot-witness/serial-binding.sh",
}
CORE_SOURCES = {
    "qemu": "https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/LICENSE",
    "linux": "https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/COPYING",
    "asahi-docs": "https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/LICENSE",
    "m1n1": "https://github.com/AsahiLinux/m1n1/blob/7cde7d1a784d851ebfee5579fa363c38b14150c0/README.md",
    "busybox": "https://busybox.net/license.html",
}
CORE_LICENSES = {
    "qemu": "GPL-2.0 as a whole; file-specific compatible licenses; bundled firmware separate",
    "linux": "GPL-2.0-only kernel with Linux-syscall-note; file-specific and dual licenses apply",
    "asahi-docs": "CC-BY-3.0",
    "m1n1": "Version-dependent: MIT through 1.9.9; GPL-2.0-or-later from 2.0.0; embedded component terms apply",
    "busybox": "GPL-2.0-only distribution; exact selected files and future build require review",
}
RESERVED_DIRS = {
    ".git", "vendor", "third_party", "third-party", "firmware", "roms",
}
ARTIFACT_SUFFIXES = {
    ".ipsw", ".im4p", ".im4m", ".img4", ".dmg", ".kc", ".rom", ".fd",
    ".qcow2", ".img", ".bin", ".elf", ".o", ".a", ".so", ".dylib",
    ".dll", ".exe", ".zip", ".tar", ".gz", ".xz", ".bz2", ".7z",
    ".cpio", ".dtb", ".dtbo", ".pem", ".key", ".pyc", ".pyo",
}
MAX_TEXT_BYTES = 2 * 1024 * 1024


def _text(value: object) -> bool:
    return (isinstance(value, str) and bool(value.strip())
            and all(ord(char) >= 32 and ord(char) != 127
                    and not 0xD800 <= ord(char) <= 0xDFFF for char in value))


def _path(value: object) -> bool:
    return (_text(value) and "\\" not in value and ":" not in value
            and all(part not in ("", ".", "..") for part in value.split("/"))
            and not any(part.casefold() == ".git" for part in value.split("/")))


def _hex(value: object, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None


def _url(value: object) -> bool:
    if not _text(value) or any(char.isspace() for char in value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and bool(url.hostname) and url.username is None
                and url.password is None and (url.port is None or 1 <= url.port <= 65535))
    except ValueError:
        return False


def _list(value: object, check, location: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{location}: expected a nonempty array")
        return []
    result = []
    for item in value:
        if not check(item):
            errors.append(f"{location}: invalid entry {item!r}")
        elif item in result:
            errors.append(f"{location}: duplicate entry {item!r}")
        else:
            result.append(item)
    return result


def _fields(value: object, fields: set[str], location: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{location}: expected an object")
        return False
    if set(value) != fields:
        errors.append(f"{location}: expected exactly {', '.join(sorted(fields))}")
    return True


def _forbidden(path: str) -> bool:
    return (any(part.casefold() in RESERVED_DIRS for part in path.split("/"))
            or Path(path).suffix.casefold() in ARTIFACT_SUFFIXES)


def validate(raw: object) -> list[str]:
    """Validate a closed schema and the current source-only licensing boundary."""
    errors: list[str] = []
    if not _fields(raw, {
        "schema_version", "phase", "reviewed_on", "baseline_commit",
        "project_license", "project_files", "boundaries", "dependencies", "review_inputs",
    }, "licensing inventory", errors):
        return errors
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        errors.append("schema_version: expected integer 1")
    if raw.get("phase") != "P006":
        errors.append("phase: expected P006")
    reviewed = raw.get("reviewed_on")
    try:
        if not isinstance(reviewed, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reviewed):
            raise ValueError
        date.fromisoformat(reviewed)
    except ValueError:
        errors.append("reviewed_on: expected a valid YYYY-MM-DD date")
    if not _hex(raw.get("baseline_commit"), 40):
        errors.append("baseline_commit: expected a full reviewed Git commit SHA")
    if raw.get("project_license") != {"spdx": "MIT", "notice": "LICENSE", "sha256": MIT_SHA256}:
        errors.append("project_license: preserve the reviewed MIT LICENSE and its SHA-256")
    if raw.get("boundaries") != BOUNDARIES:
        errors.append("boundaries: QEMU, proprietary assets, imports and reference rules must be preserved")
    files = _list(raw.get("project_files"), _path, "project_files", errors)
    if files != sorted(files):
        errors.append("project_files: use sorted exact paths, without wildcard grants")
    for path in files:
        if _forbidden(path) or any(char in path for char in "*?[]"):
            errors.append(f"project_files: {path}: third-party/artifact or wildcard path needs separate review")
    for required in ("LICENSE", str(MANIFEST), "docs/LICENSING.md", "tools/validate_licensing.py"):
        if required not in files:
            errors.append(f"project_files: missing required path {required}")

    dependencies = raw.get("dependencies")
    if not isinstance(dependencies, list):
        errors.append("dependencies: expected an array")
        dependencies = []
    identifiers: list[str] = []
    for index, entry in enumerate(dependencies):
        location = f"dependencies[{index}]"
        if not _fields(entry, {"id", "kind", "license", "shipped", "sources", "use_sites"}, location, errors):
            continue
        identifier = entry.get("id")
        valid_id = isinstance(identifier, str) and re.fullmatch(r"[a-z][a-z0-9-]*", identifier)
        if not valid_id:
            errors.append(f"{location}.id: expected a stable lowercase identifier")
        elif identifier in identifiers:
            errors.append(f"{location}.id: duplicate {identifier}")
        else:
            identifiers.append(identifier)
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind not in set(REQUIRED_DEPENDENCIES.values()):
            errors.append(f"{location}.kind: unknown dependency role")
        elif valid_id and identifier in REQUIRED_DEPENDENCIES and kind != REQUIRED_DEPENDENCIES[identifier]:
            errors.append(f"{location}.kind: changed role for {identifier}")
        if not _text(entry.get("license")):
            errors.append(f"{location}.license: expected a reviewed license summary")
        elif valid_id and identifier in CORE_LICENSES and entry["license"] != CORE_LICENSES[identifier]:
            errors.append(f"{location}.license: preserve the reviewed {identifier} licensing distinction")
        if entry.get("shipped") is not False:
            errors.append(f"{location}.shipped: must be boolean false in this source-only inventory")
        sources = _list(entry.get("sources"), _url, f"{location}.sources", errors)
        if valid_id and identifier in CORE_SOURCES and CORE_SOURCES[identifier] not in sources:
            errors.append(f"{location}.sources: missing reviewed {identifier} license evidence")
        for path in _list(entry.get("use_sites"), _path, f"{location}.use_sites", errors):
            if path not in files:
                errors.append(f"{location}.use_sites: unclassified path {path}")
    for identifier in REQUIRED_DEPENDENCIES:
        if identifier not in identifiers:
            errors.append(f"dependencies: missing reviewed component group {identifier}")

    inputs = raw.get("review_inputs")
    if not isinstance(inputs, list):
        errors.append("review_inputs: expected an array")
        inputs = []
    input_paths: list[str] = []
    for index, entry in enumerate(inputs):
        location = f"review_inputs[{index}]"
        if not _fields(entry, {"path", "sha256", "dependencies"}, location, errors):
            continue
        path = entry.get("path")
        if not _path(path):
            errors.append(f"{location}.path: invalid repository-relative path")
        elif path in input_paths:
            errors.append(f"{location}.path: duplicate {path}")
        else:
            input_paths.append(path)
            if path not in files:
                errors.append(f"{location}.path: unclassified {path}")
        if not _hex(entry.get("sha256"), 64):
            errors.append(f"{location}.sha256: expected SHA-256 of the reviewed input")
        for identifier in _list(entry.get("dependencies"), _text, f"{location}.dependencies", errors):
            if identifier not in identifiers:
                errors.append(f"{location}.dependencies: unknown dependency {identifier}")
    if set(input_paths) != REVIEWED_INPUTS:
        errors.append(f"review_inputs: all {len(REVIEWED_INPUTS)} reviewed declaration/build/runner inputs are required")
    return errors


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _regular_file(root: Path, name: str) -> Path:
    """Check every component with lstat before opening; never follow links."""
    if not _path(name):
        raise ValueError(f"unsafe repository path {name!r}")
    current = root
    parts = name.split("/")
    for index, part in enumerate(parts):
        current = current / part
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"{name}: symbolic link is not reviewed source")
        if index < len(parts) - 1 and not stat.S_ISDIR(mode):
            raise ValueError(f"{name}: parent component is not a directory")
        if index == len(parts) - 1 and not stat.S_ISREG(mode):
            raise ValueError(f"{name}: not a regular source file")
    return current


def _read(root: Path, name: str) -> bytes:
    path = _regular_file(root, name)
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ValueError(f"{name}: exceeds the 2 MiB reviewed text limit")
    return path.read_bytes()


def _git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=15, check=False,
    )
    if result.returncode:
        # Git's diagnostic can contain untrusted config paths; a bounded message
        # suffices. Never run shell commands or repository-provided hooks here.
        raise ValueError(f"Git inventory command failed ({result.returncode}): {' '.join(arguments)}")
    return result.stdout


def _inventory(root: Path, archive: bool, errors: list[str]) -> set[str]:
    paths: set[str] = set()
    if archive:
        def walk_error(exc):
            errors.append(f"archive inventory: {exc}")
        for parent, directories, filenames in os.walk(root, followlinks=False, onerror=walk_error):
            for name in list(directories):
                path = Path(parent) / name
                relative = path.relative_to(root).as_posix()
                if name.casefold() == ".git" or path.is_symlink():
                    errors.append(f"{relative}: Git metadata or symbolic-link directory is forbidden in an archive")
                    directories.remove(name)
            for name in filenames:
                paths.add((Path(parent) / name).relative_to(root).as_posix())
        return paths
    # An ancestor's Git worktree is never the requested snapshot. Archive
    # scanning is explicit and stricter, never a fallback after a Git failure.
    marker = root / ".git"
    if marker.is_symlink() or not (marker.is_dir() or marker.is_file()):
        errors.append("Git inventory requires .git at --root; use --archive for an exported source tree")
        return paths
    try:
        top = Path(os.fsdecode(_git(root, "rev-parse", "--show-toplevel")).strip())
        if top.resolve() != root.resolve():
            raise ValueError("Git root differs from the requested inventory root")
        for record in _git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if not record:
                continue
            metadata, path_bytes = record.split(b"\t", 1)
            mode, _object_id, stage = metadata.split()
            name = os.fsdecode(path_bytes)
            paths.add(name)
            if mode not in (b"100644", b"100755") or stage != b"0":
                errors.append(f"{name}: unsupported Git mode/stage; symlinks, submodules and conflicts require review")
        paths.update(os.fsdecode(path) for path in _git(
            root, "ls-files", "--others", "--exclude-standard", "-z",
        ).split(b"\0") if path)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        errors.append(f"cannot inventory Git source tree: {exc}")
    return paths


def validate_repository(root: Path = ROOT, *, archive: bool = False) -> list[str]:
    """Audit working files, or every file of an explicit clean source archive."""
    errors: list[str] = []
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        return ["inventory root must be an existing directory, not a symbolic link"]
    try:
        raw = json.loads(_read(root, str(MANIFEST)).decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        return [f"{MANIFEST}: cannot read licensing inventory: {exc}"]
    errors.extend(validate(raw))
    if errors:
        return errors
    expected = set(raw["project_files"])
    actual = _inventory(root, archive, errors)
    for name in sorted(actual - expected):
        errors.append(f"{name}: unclassified file; review provenance before adding it to the inventory")
    for name in sorted(expected - actual):
        errors.append(f"{name}: inventoried source is missing from the selected tree")
    contents: dict[str, bytes] = {}
    for name in sorted(actual | expected):
        if not _path(name) or _forbidden(name):
            errors.append(f"{name!r}: prohibited artifact/third-party path in the source-only inventory")
            continue
        try:
            data = _read(root, name)
            text = data.decode("utf-8")
            if any(ord(char) < 32 and char not in "\t\r\n" or ord(char) == 127 for char in text):
                raise ValueError("binary/control bytes in a reviewed text file")
            # Detect explicit license-header conflicts, not arbitrary license
            # names in prose or synthetic strings in the regression tests.
            for line in text.splitlines():
                header = re.match(r"^\s*(?:#|//|/\*|\*|<!--)\s*SPDX-License-Identifier:\s*(.*?)\s*(?:\*/|-->)?$", line)
                if header and header.group(1) != "MIT":
                    raise ValueError("non-MIT SPDX header conflicts with project-authored classification")
            contents[name] = data
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append(f"{name}: cannot accept source content: {exc}")
    notice = contents.get("LICENSE")
    if notice is not None and hashlib.sha256(notice).hexdigest() != MIT_SHA256:
        errors.append("LICENSE: MIT notice differs from the reviewed permission grant")
    for entry in raw["review_inputs"]:
        data = contents.get(entry["path"])
        if data is not None and hashlib.sha256(data).hexdigest() != entry["sha256"]:
            errors.append(f"{entry['path']}: dependency review digest changed; inspect declarations and update the review")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root or exported source directory")
    parser.add_argument("--archive", action="store_true", help="scan every file of a clean export, without ignore rules")
    args = parser.parse_args()
    errors = validate_repository(args.root, archive=args.archive)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P006 source inventory: exact project paths, license boundaries and dependency review digests")
        print("This is an engineering check, not proof of authorship or approval of future binary redistribution")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
