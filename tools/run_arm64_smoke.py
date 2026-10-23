#!/usr/bin/env python3
"""Run the explicitly NON-M1 ARM64 QEMU virt smoke test."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import shutil
import signal
import subprocess
import sys

EXPECTED = "ARM64 baseline OK"
MAX_TIMEOUT = 300.0


def command(qemu: str, elf: Path) -> list[str]:
    return [
        qemu, "-accel", "tcg", "-M", "virt", "-cpu", "cortex-a57",
        "-m", "128M", "-smp", "1",
        "-nographic", "-monitor", "none", "-serial", "stdio", "-no-reboot",
        "-kernel", str(elf),
    ]


def positive_timeout(text: str) -> float:
    """Reject values that cannot bound a smoke-test process."""
    message = f"timeout must be finite and greater than zero, at most {MAX_TIMEOUT:g} seconds"
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(message) from exc
    if not math.isfinite(value) or not 0 < value <= MAX_TIMEOUT:
        raise argparse.ArgumentTypeError(message)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    parser.add_argument(
        "--timeout", type=positive_timeout, default=8.0,
        help=f"finite seconds to wait, 0 < timeout <= {MAX_TIMEOUT:g} (default: %(default)s)",
    )
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if not qemu:
        print("Missing qemu-system-aarch64; install qemu-system-arm", file=sys.stderr)
        return 2
    if not args.elf.is_file():
        print(f"Missing guest ELF: {args.elf}", file=sys.stderr)
        return 2
    try:
        process = subprocess.Popen(
            command(qemu, args.elf.resolve()), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
    except OSError as exc:
        print(f"Cannot launch generic ARM64 QEMU TCG smoke test: {exc}", file=sys.stderr)
        return 2
    timed_out = False
    try:
        data, _ = process.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        data, _ = process.communicate()
    output = data.decode("utf-8", errors="replace")
    # The original guest intentionally waits forever after writing its marker.
    # Only the runner's timeout/SIGKILL path permits a nonzero QEMU exit status;
    # a later QEMU failure must not be hidden by an earlier successful write.
    expected_stop = timed_out and process.returncode == -signal.SIGKILL
    if process.returncode != 0 and not expected_stop:
        print(f"Generic ARM64 QEMU TCG exited with status {process.returncode}. Output:\n"
              + output, file=sys.stderr)
        return 1
    if EXPECTED not in output:
        print("Generic ARM64 smoke test failed. Output:\n" + output, file=sys.stderr)
        return 1
    print("PASS: generic ARM64 QEMU virt with TCG booted the guest and wrote:", EXPECTED)
    print("NOTE: this test does not implement or prove Apple M1 emulation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
