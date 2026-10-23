# Engineering instructions

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Scope and branch policy

- Work on `main` only, unless the repository owner explicitly requests a separate branch.
- Preserve existing work. Commit cohesive, tested progress; never use LOC count as a proxy for fidelity.
- `ROADMAP_365_PHASES.md` is the canonical plan. Do not mark a phase complete without proof matching its acceptance condition.
- Update `docs/ARCHITECTURE.md` and `hardware/t8103.json` alongside hardware-model changes.
- Preserve the P001 target charter and its declared identity in all six documented project entrypoints; run `python3 tools/validate_target.py` when changing target metadata or entrypoint documentation. Add any new project overview/setup entrypoint to the validator's inventory.
- Preserve the P002 fidelity definitions and all G0–G6/P361–P365 classifications in `docs/fidelity.json`, the architecture and the roadmap. Run `python3 tools/validate_fidelity.py` after scope or gate changes; labels alone never establish a passed runtime gate.

## Non-negotiable correctness rules

1. Distinguish **generic ARM64**, **Apple-specific CPU**, **T8103 SoC**, **Linux compatibility** and **macOS compatibility**. Their tests must not be conflated.
2. Every implemented MMIO register needs read/write/reset semantics and at least one test. Explicitly document unknown bits and fault behavior.
3. Use cited primary sources (Arm, Apple, Asahi, QEMU, Linux source); never invent memory addresses, register values, device IDs, timings, or ISA support.
4. Prioritize externally observable correctness; microarchitecture timing is a separate research track.
5. Prefer a QEMU board/CPU extension to rewriting standard AArch64 execution. Keep lab-only boot shortcuts separate from strict fidelity mode.
6. Never ship Apple proprietary firmware or images. Sanitize all captured traces and Apple Device Tree dumps before committing.
7. Avoid potentially harmful modification of reference machines; follow Asahi's non-destructive research guidance and explicitly review boot policy changes.

## Definition of done

- Build succeeds on supported Linux host or the known unavailable dependency is documented.
- Focused tests cover both expected and edge-case behavior.
- All checks pass: `python3 -m unittest discover -s tests -v`, `python3 tools/validate_target.py`, `python3 tools/validate_fidelity.py`, `python3 tools/validate_roadmap.py`, and `python3 tools/validate_hardware.py`.
- A short completion note records evidence, deviations, known limitations, and the relevant phase identifier.
- Status is honest: a failing or untested component is never described as implemented.
