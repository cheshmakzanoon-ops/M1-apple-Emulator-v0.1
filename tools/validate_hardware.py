#!/usr/bin/env python3
"""Validate cited T8103 region metadata; does not claim device implementation."""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "hardware" / "t8103.json"
HEX = re.compile(r"^0x[0-9a-fA-F]+$")


def validate(raw: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["hardware metadata must be an object"]
    if raw.get("schema_version") != 1 or raw.get("soc") != "T8103":
        errors.append("expected schema_version=1 and soc=T8103")

    sources = raw.get("sources", {})
    if not isinstance(sources, dict) or not sources:
        return errors + ["sources must be a non-empty object"]
    for key, url in sources.items():
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append(f"invalid source URL for {key}")

    names: set[str] = set()
    mmio: list[tuple[int, int, str]] = []
    regions = raw.get("regions", [])
    if not isinstance(regions, list) or not regions:
        return errors + ["regions must be a non-empty array"]

    for index, region in enumerate(regions):
        if not isinstance(region, dict):
            errors.append(f"region {index} is not an object")
            continue
        name = region.get("name", "")
        if not isinstance(name, str) or not name or name in names:
            errors.append(f"invalid or duplicate region name at index {index}")
            name = f"region[{index}]"
        else:
            names.add(name)
        source = region.get("source")
        if not isinstance(source, str) or source not in sources:
            errors.append(f"{name}: unknown source")
        if region.get("confidence") not in ("documented", "inferred", "unverified"):
            errors.append(f"{name}: invalid confidence")
        if region.get("status") not in ("reference-only", "stubbed", "tested"):
            errors.append(f"{name}: invalid status")
        if not isinstance(region.get("notes"), str) or not region["notes"].strip():
            errors.append(f"{name}: missing notes")
        base_str, size_str = region.get("base"), region.get("size")
        if not isinstance(base_str, str) or not HEX.fullmatch(base_str):
            errors.append(f"{name}: invalid base")
            continue
        base = int(base_str, 16)
        if base < 0 or base >= (1 << 64):
            errors.append(f"{name}: out-of-range base")
        if region.get("kind") == "mmio":
            if not isinstance(size_str, str) or not HEX.fullmatch(size_str):
                errors.append(f"{name}: MMIO must have a hexadecimal size")
                continue
            size = int(size_str, 16)
            if not size or base + size > (1 << 64) or base % 0x1000:
                errors.append(f"{name}: invalid size, overflow or alignment")
            mmio.append((base, base + size, name))
        elif region.get("kind") != "ram":
            errors.append(f"{name}: invalid kind")
        elif size_str is not None and (not isinstance(size_str, str) or not HEX.fullmatch(size_str)):
            errors.append(f"{name}: RAM size must be null or hex")
        elif size_str is not None:
            size = int(size_str, 16)
            if not size or base + size > (1 << 64):
                errors.append(f"{name}: invalid RAM size or address overflow")

    mmio.sort()
    for prev, current in zip(mmio, mmio[1:]):
        if prev[1] > current[0]:
            errors.append(f"MMIO overlap: {prev[2]} and {current[2]}")
    return errors


def main() -> int:
    raw = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    errors = validate(raw)
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print(f"Valid T8103 reference map: {len(raw['regions'])} entries; MMIO ranges do not overlap")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
