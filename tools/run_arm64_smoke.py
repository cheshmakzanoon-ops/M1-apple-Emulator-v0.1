#!/usr/bin/env python3
"""Run the explicitly NON-M1 ARM64 QEMU virt smoke test."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED = "ARM64 baseline OK"


def command(qemu: str, elf: Path) -> list[str]:
    return [
        qemu, "-M", "virt", "-cpu", "cortex-a57", "-m", "128M", "-smp", "1",
        "-nographic", "-monitor", "none", "-serial", "stdio", "-no-reboot",
        "-kernel", str(elf),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if not qemu:
        print("Missing qemu-system-aarch64; install qemu-system-arm", file=sys.stderr)
        return 2
    if not args.elf.is_file():
        print(f"Missing guest ELF: {args.elf}", file=sys.stderr)
        return 2
    process = subprocess.Popen(
        command(qemu, args.elf.resolve()), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        data, _ = process.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        data, _ = process.communicate()
    output = data.decode("utf-8", errors="replace")
    if EXPECTED not in output:
        print("Generic ARM64 smoke test failed. Output:\n" + output, file=sys.stderr)
        return 1
    print("PASS: generic ARM64 QEMU virt booted the guest and wrote:", EXPECTED)
    print("NOTE: this test does not implement or prove Apple M1 emulation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
