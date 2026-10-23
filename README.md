# Apple M1 Emulator — T8103 Research Project

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are exploratory, unimplemented and not required.

An open, incremental research project to model the **original Apple M1 (T8103)** at the CPU/SoC interface. The initial reference machine is the **2020 M1 Mac mini (J274)**. The intended production execution engine is **QEMU's AArch64 TCG**, extended with Apple-specific CPU behavior, a T8103 board, and validated peripheral models.

> **Current status: P001–P003 complete — target, independent fidelity and Linux boot-witness contracts defined and automatically checked.** See the [P001](docs/phases/P001.md), [P002](docs/phases/P002.md) and [P003 completion evidence](docs/phases/P003.md). This repository does **not** yet emulate an M1 CPU or boot macOS/Linux on a T8103 model. The P003 probe/checker tests use synthetic evidence; G4 remains unrun. Its executable ARM64 smoke test uses QEMU's generic `virt` board to validate the development toolchain. Do not mistake that test for M1 emulation.

## Project target

1. Execute ARM64 workloads with correct architectural state, exceptions, translation and memory ordering.
2. Present a supported subset of Apple Firestorm/Icestorm CPU identities and implementation-defined system registers.
3. Expose verified T8103 physical memory regions, an Apple UART, AIC interrupts, timers and SMP bring-up.
4. Boot an M1-targeted Linux kernel to a serial initramfs shell using **Apple-compatible interfaces**, not QEMU `virt` peripherals.
5. Later add DART/DMA, ANS/NVMe, selected coprocessors, and advanced research targets.

Cycle-accurate Firestorm simulation, fully functioning Apple AGX graphics, and unmodified macOS are **long-term exploratory goals**, not v0.1 deliverables.

## Start here

- [365-phase engineering roadmap](ROADMAP_365_PHASES.md) — exactly 365 individually tracked, dependency-ordered tasks.
- [Architecture and acceptance gates](docs/ARCHITECTURE.md) — design boundaries and the real Linux-boot milestone.
- [P001 target charter](docs/ARCHITECTURE.md#p001-target-charter) — exact SoC/board identity, exclusions and the automated consistency check.
- [P002 fidelity contract](docs/ARCHITECTURE.md#p002-fidelity-contract) — independent CPU, peripheral and whole-machine definitions; all 12 development/release gates classified.
- [P003 Linux boot milestone](docs/LINUX_BOOT_MILESTONE.md) — explicit G4 prerequisites, reproducible serial-shell witness and evidence requirements; actual Linux boot remains future work.
- [P004 exploratory scope](docs/EXPLORATORY_SCOPE.md) — explicit boundaries for timing, graphics and unmodified macOS; no runtime capability is established.
- [Hardware reference register](hardware/t8103.json) — sourced addresses, uncertainty, and schema-validated data.
- [Reference material](docs/REFERENCES.md) — authoritative upstream projects and publications.
- [Local development](docs/DEVELOPMENT.md) — Windows/WSL2/Linux setup and current smoke tests.
- [Contribution contract](AGENTS.md) — rules to keep changes measurable and reproducible.

## Verify target, fidelity, Linux milestone and scope contracts

Validate the target declarations, fidelity definitions, Linux witness contract, exploratory scope and planning metadata with Python 3.11+ and a POSIX host shell:

```sh
python3 tools/validate_target.py
python3 tools/validate_fidelity.py
python3 tools/validate_boot_milestone.py
python3 tools/validate_scope.py
python3 tools/validate_hardware.py
python3 tools/validate_roadmap.py
python3 -m unittest discover -s tests -v
```

## First runnable test (generic ARM64 only)

On Ubuntu/WSL2 with `qemu-system-aarch64`, `aarch64-linux-gnu-gcc`, `make` and Python 3:

```sh
make -C experiments/arm64-virt-smoke
python3 tools/run_arm64_smoke.py experiments/arm64-virt-smoke/build/hello.elf
```

The smoke test should print `ARM64 baseline OK` using the **QEMU `virt` PL011 UART**. It is deliberately isolated in `experiments/` until our actual Apple UART and custom T8103 machine exist.

## Fidelity policy

Only code exercised by a regression test can be called implemented. Any hardware address, instruction extension, privilege state, or device behavior without adequate public evidence is recorded as **unknown**. Shortcuts used for development must be marked as shortcuts and excluded from fidelity claims.

No Apple ROM, firmware, macOS image, encryption key, or proprietary SDK is included. Future owners must supply any lawfully obtained research inputs themselves; do not commit sensitive ADT fields or device identifiers.

## License

Project-authored documentation, tooling and standalone experiments use [MIT](LICENSE). Any future QEMU-derived source must comply with QEMU's applicable GPL terms and retain upstream notices. This repository does not currently vendor QEMU.
