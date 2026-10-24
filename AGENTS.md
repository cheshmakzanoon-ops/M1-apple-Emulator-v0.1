# Engineering instructions

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Scope and branch policy

- Work on `main` only, unless the repository owner explicitly requests a separate branch.
- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for review, exact staged-tree tests and publication to `main`; auxiliary branches and pull requests are not prerequisites.
- Preserve existing work. Commit cohesive, tested progress; never use LOC count as a proxy for fidelity.
- `ROADMAP_365_PHASES.md` is the canonical plan. Do not mark a phase complete without proof matching its acceptance condition.
- Update `docs/ARCHITECTURE.md` and `hardware/t8103.json` alongside hardware-model changes.
- Preserve the P001 target charter and its declared identity in all documented project entrypoints; run `python3 tools/validate_target.py` when changing target metadata or entrypoint documentation. Add any new project overview/setup entrypoint to the validator's inventory.
- Preserve the P002 fidelity definitions and all G0–G6/P361–P365 classifications in `docs/fidelity.json`, the architecture and the roadmap. Run `python3 tools/validate_fidelity.py` after scope or gate changes; labels alone never establish a passed runtime gate.
- Preserve the P003 G4 boot contract in `docs/boot-milestone.json` and `docs/LINUX_BOOT_MILESTONE.md`; run `python3 tools/validate_boot_milestone.py`. A contract check or synthetic transcript cannot certify a cold Linux boot. Changes to the source-observable profile require source review and matching probe/checker regressions.
- Preserve the P004 exploratory exclusions in `docs/scope.json` and `docs/EXPLORATORY_SCOPE.md`; run `python3 tools/validate_scope.py`. Cycle accuracy, GPU graphics and unmodified macOS remain outside required v0.1 scope and unimplemented. Narrow research completion must not promote them to shipped capabilities.
- Preserve the P005 executor decision in `docs/decisions/0001-qemu-tcg.md`: full-system AArch64 TCG, with explicit `-accel tcg` and no implicit hypervisor fallback in the generic smoke runner. Changes to the foundation need a linked decision and corresponding execution evidence; QEMU source citations do not complete P017's build pin.
- Preserve P006's licensing boundaries in `docs/LICENSING.md` and exact source inventory in `docs/licensing.json`. Review provenance before adding a file or updating dependency-input hashes; never automatically bless all discovered paths. Run `python3 tools/validate_licensing.py`; use `--root PATH --archive` for a clean source export. Future third-party imports and binary distribution need their own reviewed inventory and notices, not an MIT list entry.
- Preserve P007's contribution contract and run `python3 tools/validate_branch_policy.py`. Use `--checkout` for local precommit review on attached `main`; detached CI/source exports use the offline default. Never force-push or rewrite published history. Bind publication to the tested tree and immutable commit SHA, and verify both hosted jobs for that SHA before reporting it verified.

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
- All checks pass: `python3 -m unittest discover -s tests -v`, `python3 tools/validate_target.py`, `python3 tools/validate_fidelity.py`, `python3 tools/validate_boot_milestone.py`, `python3 tools/validate_scope.py`, `python3 tools/validate_licensing.py`, `python3 tools/validate_branch_policy.py`, `python3 tools/validate_roadmap.py`, and `python3 tools/validate_hardware.py`.
- A short completion note records evidence, deviations, known limitations, and the relevant phase identifier.
- Status is honest: a failing or untested component is never described as implemented.
