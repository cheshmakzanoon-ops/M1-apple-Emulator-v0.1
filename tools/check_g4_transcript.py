#!/usr/bin/env python3
"""Check P003 serial-probe evidence; this cannot authenticate or certify G4.

The host must record the chosen nonce/operands independently and transmit the
challenge only after READY. This offline checker cannot establish that ordering,
a fresh emulator process, truthful guest data, artifact provenance, or actual
Apple hardware behavior. Those remain separate witness/review obligations.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re

MAX_BYTES = 8 * 1024 * 1024
# Linux v6.12 kernel/irq/proc.c formats counts as %u and domain hwirq as
# unsigned long (%lu), respectively 32 and 64 bits on the selected ARM64 guest.
MAX_COUNTER = (1 << 32) - 1
MAX_HWIRQ = (1 << 64) - 1
COMPATIBLE = ("apple,j274", "apple,t8103", "apple,arm-platform")
IRQ_TARGETS = {"UART": ("AIC", "235200000.serial"), "timer": ("AIC-FIQ", "arch_timer")}
FATAL = re.compile(r"\b(?:Kernel panic|kernel BUG\b|Oops:|BUG:|Internal error:|Unable to handle kernel)"
                   r"|(?:^|\n)G4-ERROR(?:\s|$)", re.I)


class ProtocolError(ValueError):
    """A malformed or incomplete serial witness, reported without a traceback."""


class _Reader:
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.position = 0

    def expect(self, expected: str) -> None:
        if self.position >= len(self.lines) or self.lines[self.position] != expected:
            raise ProtocolError(f"expected {expected!r} at framed line {self.position + 1}")
        self.position += 1

    def block(self, label: str) -> list[str]:
        self.expect(f"G4-{label}-BEGIN")
        start = self.position
        while self.position < len(self.lines):
            line = self.lines[self.position]
            if line == f"G4-{label}-END":
                result = self.lines[start:self.position]
                self.position += 1
                if not result:
                    raise ProtocolError(f"{label}: empty evidence block")
                return result
            if line.startswith("G4-"):
                raise ProtocolError(f"{label}: unexpected protocol frame inside evidence block")
            self.position += 1
        raise ProtocolError(f"{label}: missing closing frame")

    def uptime(self, label: str) -> int:
        if self.position >= len(self.lines):
            raise ProtocolError(f"missing UPTIME-{label}")
        line = self.lines[self.position]
        match = re.fullmatch(rf"G4-UPTIME-{label} (0|[1-9][0-9]{{0,12}})\.([0-9]{{2}}) "
                             r"(?:0|[1-9][0-9]{0,12})\.[0-9]{2}", line)
        if match is None:
            raise ProtocolError(f"UPTIME-{label}: expected the two decimal fields from /proc/uptime")
        self.position += 1
        return int(match[1]) * 100 + int(match[2])


def _interrupts(lines: list[str], label: str) -> tuple[tuple[str, ...], dict]:
    """Read Linux counters without freezing its assigned virq or hwirq numbers."""
    cpus = tuple(lines[0].split())
    if cpus != ("CPU0",):
        raise ProtocolError(f"{label}: initial laboratory profile requires exactly one CPU0 column")
    targets: dict = {}
    for line in lines[1:]:
        match = re.fullmatch(r"\s*([0-9]+):\s+(.+?)\s*", line)
        if match is None:
            # Linux also emits IPI and Err summary rows; they are not the two
            # independently required external-IRQ and timer-FIQ observations.
            continue
        fields = match[2].split()
        count_fields, metadata = fields[:len(cpus)], tuple(fields[len(cpus):])
        if (len(count_fields) != len(cpus) or any(not re.fullmatch(r"[0-9]{1,10}", value)
                                                for value in count_fields)
                or len(metadata) < 3):
            raise ProtocolError(f"{label}: malformed numeric IRQ row")
        counts = tuple(int(value) for value in count_fields)
        if any(value > MAX_COUNTER for value in counts):
            raise ProtocolError(f"{label}: IRQ counter outside unsigned 32-bit range")
        for name, (chip, action) in IRQ_TARGETS.items():
            if metadata[0] == chip and metadata[-1] == action:
                if (re.fullmatch(r"(?:0|[1-9][0-9]{0,19})", metadata[1]) is None
                        or int(metadata[1]) > MAX_HWIRQ):
                    raise ProtocolError(f"{label}: {name} hwirq must be an unsigned decimal integer")
                qualifiers = list(metadata[2:-1])
                if qualifiers and qualifiers[0] in ("Level", "Edge"):
                    qualifiers.pop(0)
                if qualifiers and re.fullmatch(r"-[A-Za-z0-9_.+-]+", qualifiers[0]):
                    qualifiers.pop(0)
                if qualifiers:
                    raise ProtocolError(f"{label}: unexpected {name} IRQ metadata")
                if name in targets:
                    raise ProtocolError(f"{label}: duplicate {name} IRQ row")
                targets[name] = ((match[1], metadata), counts)
    for name in IRQ_TARGETS:
        if name not in targets:
            raise ProtocolError(f"{label}: missing source-profile {name} IRQ row")
    return cpus, targets


def _consoles(lines: list[str]) -> None:
    selected = []
    for line in lines:
        match = re.fullmatch(r"\s*(\S+)\s+([R-][W-][U-])\s+\(([^)]*)\)\s+[0-9]+:[0-9]+\s*", line)
        if match and match[1] == "ttySAC0":
            selected.append(match)
    if len(selected) != 1 or selected[0][2][1] != "W" or "E" not in selected[0][3]:
        raise ProtocolError("CONSOLES: expected one enabled writable ttySAC0 console")


def validate_transcript(text: str, nonce: str, left: int, right: int) -> list[str]:
    """Return diagnostics for an independently captured, single-trial transcript.

    An empty list means consistent protocol evidence, never an awarded runtime
    gate. In particular, arbitrary or replayed data can be made consistent; use
    a fresh random nonce plus independently reviewed capture/provenance records.
    """
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        return ["nonce: expected exactly 32 lowercase hexadecimal characters"]
    if any(type(value) is not int or not 1 <= value <= 999999 for value in (left, right)):
        return ["operands: expected integer values in 1..999999"]
    if not isinstance(text, str):
        return ["transcript: expected UTF-8 text"]
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError:
        return ["transcript: invalid Unicode text"]
    if size > MAX_BYTES:
        return ["transcript: exceeds 8 MiB limit"]
    text = text.replace("\r\n", "\n")
    if any(ord(char) < 32 and char not in "\n\t" or ord(char) == 127 for char in text):
        return ["transcript: unexpected control character or incomplete CRLF"]
    if FATAL.search(text):
        return ["transcript: guest failure or kernel panic/oops/BUG diagnostic"]
    # Serial framing is LF (or normalized CRLF), not Unicode's broader set of
    # line separators. A command echo cannot gain an anchor through U+2028.
    lines = text.split("\n")
    if lines[-1].startswith("G4-"):
        return ["transcript: truncated protocol line"]
    frames = [i for i, line in enumerate(lines) if line.startswith("G4-")]
    if not frames:
        return ["transcript: no anchored probe frames; a prompt or echoed command is insufficient"]
    reader = _Reader(lines[frames[0]:frames[-1] + 1])
    try:
        reader.expect(f"G4-BEGIN {nonce}")
        reader.expect("G4-ARCH aarch64")
        reader.expect("G4-TTY /dev/ttySAC0")
        reader.expect("G4-DRIVER samsung-uart")
        if reader.block("COMPAT") != list(COMPATIBLE):
            raise ProtocolError("COMPAT: expected the exact ordered J274/T8103 root compatible list")
        _consoles(reader.block("CONSOLES"))
        before_cpus, before = _interrupts(reader.block("IRQ-BEFORE"), "IRQ-BEFORE")
        before_time = reader.uptime("BEFORE")
        reader.expect(f"G4-READY {nonce}")
        after_cpus, after = _interrupts(reader.block("IRQ-AFTER"), "IRQ-AFTER")
        after_time = reader.uptime("AFTER")
        reader.expect(f"G4-RESULT {nonce} {left + right}")
        reader.expect(f"G4-END {nonce}")
        # After the probe exits, the host sends a separate printf/arithmetic
        # command to the interactive shell. Its prompt and echoed command may
        # appear here, but neither contains an anchored computed result frame.
        while reader.position < len(reader.lines) and not reader.lines[reader.position].startswith("G4-"):
            reader.position += 1
        reader.expect(f"G4-SHELL {nonce} {left * right}")
        if reader.position != len(reader.lines):
            raise ProtocolError("unexpected extra or duplicate probe frames")
        if before_cpus != after_cpus:
            raise ProtocolError("IRQ: CPU columns changed during the trial")
        for name in IRQ_TARGETS:
            before_identity, before_counts = before[name]
            after_identity, after_counts = after[name]
            if before_identity != after_identity:
                raise ProtocolError(f"IRQ: {name} identity changed during the trial")
            if any(new < old for old, new in zip(before_counts, after_counts)):
                raise ProtocolError(f"IRQ: {name} per-CPU counter regressed")
            if sum(after_counts) <= sum(before_counts):
                raise ProtocolError(f"IRQ: {name} counter did not increase")
        if after_time - before_time < 100:
            raise ProtocolError("UPTIME: scheduled sleep did not advance guest time by at least 1.00 seconds")
    except ProtocolError as exc:
        return [str(exc)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path, help="raw guest-to-host serial capture from one trial")
    parser.add_argument("--nonce", required=True, help="independently recorded fresh 32-digit lowercase hex nonce")
    parser.add_argument("--left", type=int, required=True, help="independently recorded first challenge operand")
    parser.add_argument("--right", type=int, required=True, help="independently recorded second challenge operand")
    args = parser.parse_args()
    try:
        with args.transcript.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            errors = ["transcript: exceeds 8 MiB limit"]
        else:
            errors = validate_transcript(data.decode("utf-8"), args.nonce, args.left, args.right)
    except (OSError, UnicodeError) as exc:
        errors = [f"{args.transcript}: cannot read UTF-8 transcript: {exc}"]
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid G4 probe protocol ONLY: challenge, shell return, Apple serial observations and timer progress agree")
        print("This does not authenticate evidence or certify G4; prerequisite, provenance and cold-boot review remain required")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
