# ADR 0001 — Use QEMU AArch64 TCG as the initial executor

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are exploratory, unimplemented and not required.

**Status:** accepted for P005. **Decision date:** 2026-10-23. **Scope:** execution foundation; no runtime compatibility gate is awarded.

## Context and decision drivers

The first required system workload is the [G4 Linux initramfs shell](../LINUX_BOOT_MILESTONE.md) on the selected Apple UART/AIC platform. It requires privileged guest execution, address translation, exceptions, interrupts and a board model. Running an isolated ARM64 application under a host kernel is insufficient. The development host is Linux x86_64, including Ubuntu under Windows WSL2; an Apple machine must not be required for ordinary development.

The important selection criteria are cross-ISA execution, integration with custom memory and peripherals, observable faults, maintainable changes and reproducible tests. Neither a particular frame rate nor native M1 performance is an established requirement. The reasoning below is a project engineering judgment based on the [primary evidence register](../REFERENCES.md#p005-emulation-foundation-evidence); no upstream project certifies this emulator.

## Decision

Use **QEMU full-system AArch64 emulation with the Tiny Code Generator (TCG)** as the initial production executor. The intended build target is `aarch64-softmmu`, the executable is `qemu-system-aarch64`, and baseline guest-execution tests must select `-accel tcg` explicitly. Do not allow an accelerator fallback list to silently replace TCG with KVM or HVF. Device-only QTest runs have their own execution context and are not subject to this guest-execution rule.

Extend QEMU with a separately tested Apple CPU personality and a distinct T8103/J274 machine. The roadmap's `apple-m1-lab` name describes the future board; no such machine is supplied by this phase. Keep the existing `virt`/`cortex-a57`/PL011 experiment as generic toolchain evidence. Do not rename that platform or select `-cpu max` and report an M1 implementation.

QEMU distinguishes full-system emulation from user-mode execution. Its system facilities cover CPU, memory and devices; TCG supplies cross-architecture software translation. Hardware acceleration executes guest code on compatible host hardware and does not translate an AArch64 guest into x86_64 instructions. These are the reasons this project selects full-system TCG for its x86_64 host. [Q1][qemu-about] [Q2][qemu-emulation] [Q3][qemu-system]

## Why reuse this executor

TCG translates guest instructions into an intermediate representation and host code, reuses translated blocks, and coordinates execution with architectural state and exceptions. System emulation includes a software MMU and routes MMIO accesses to device callbacks. These facilities address the ordinary AArch64 execution and memory-access problem while leaving room for the Apple-specific research. They are reusable implementation machinery, not an independent proof of architectural conformance. [Q4][qemu-tcg]

A second production interpreter would make this project responsible for instruction decoding, register and flag semantics, floating point/SIMD behavior, privilege transitions, faults, page-table walks, atomics and debugging before it could investigate the missing T8103 interfaces. That is an engineering cost inference, not a measured schedule or a claim that an interpreter is impossible. A small independent semantic oracle may still be useful for individual tests; it does not need to become another system executor.

QEMU also supplies object composition, RAM/MMIO regions and device-test infrastructure. Reusing them avoids creating a separate board framework just to attach an Apple UART, AIC and later DMA devices. QTest can exercise device state independently of the guest instruction stream; guest payloads remain necessary to demonstrate CPU/device integration. [Q5][qemu-qom] [Q6][qemu-memory] [Q7][qemu-qtest]

The tradeoff is an ongoing dependency on QEMU's APIs, upstream defects and release changes. Keep changes focused, retain upstream provenance, and rerun relevant regressions when the foundation changes. A mature upstream implementation reduces duplicated work; it does not remove the project's verification obligations.

## Alternatives considered

| Alternative | Assessment and decision for this project |
|---|---|
| New AArch64 interpreter or translator | Maximum control, but duplicates the architectural execution and validation work described above. Not selected as the production foundation. Independently written, narrowly scoped expected-result generators remain useful. |
| KVM or HVF acceleration | Potentially useful for separate research on compatible hosts. Neither supplies AArch64-to-x86_64 translation; HVF's host OS is macOS. They do not meet the portable baseline. A future accelerated path would need its own feature/execution evidence. [Q1][qemu-about] [Q3][qemu-system] |
| QEMU user-mode emulation | Useful for individual compatible-ABI processes. It translates guest system calls to host operations and does not provide this project's booting guest kernel and physical-machine environment. Not selected as the system executor. [Q1][qemu-about] [Q8][qemu-user] |
| Unicorn | A QEMU-derived CPU emulation framework with an embedding API and instrumentation. Useful for snippets and bounded experiments; integrating the required board, devices and system workload would remain project work. Its QEMU ancestry also prevents assuming it is an independent architectural oracle. [U1][unicorn] |
| A detailed simulator such as gem5, or custom RTL | A possible separate timing-research tool. Detailed pipeline/cache models need defensible Apple parameters and a platform model before they can support M1 timing claims. The documented gem5 O3 model is loosely based on Alpha 21264, not a measured Firestorm design. Additional modeling cost does not serve the initial functional Linux milestone. [G1][gem5] |
| QEMU VMApple | Models the virtual platform associated with Apple's Virtualization.framework. Its documented Apple Silicon/macOS/HVF configuration targets a different machine. A VMApple workload cannot establish physical J274/T8103 compatibility. [Q9][qemu-vmapple] |
| Generic QEMU `virt` as the final machine | Useful as the existing development smoke platform. Its virtual platform, GIC and PL011 interfaces differ from the required physical target. Retain it only as a separate toolchain experiment. [Q10][qemu-virt] |

## Responsibility boundary

| Layer | Reused foundation | Project responsibility and evidence |
|---|---|---|
| Architectural executor | AArch64 translation, architectural state, exception and software-MMU machinery | Select the tested feature subset; investigate differences and test faults, privilege, FP/SIMD, atomics and ordering. QEMU selection alone grants no ISA-wide conformance. |
| Apple CPU personality | CPU object and system-register mechanisms | Source and test Firestorm/Icestorm identities, topology, feature masks and implementation-defined registers; label unknowns/stubs. This work remains P046–P105. |
| T8103/J274 board and peripherals | Object composition, address spaces, device lifecycle and character backends | Implement source-backed mappings, reset, UART/AIC state, timer FIQ routing and board-specific behavior. Begin the distinct board in P106–P120; UART/AIC/timers follow. |
| Guest boot and integration | Image loading, debugging and monitoring facilities | Specify entry state, DTB, kernel/initramfs and lab shortcuts; satisfy the P003 witness with actual artifacts. Later direct Linux loading does not establish Apple's firmware boot chain. |
| Research evidence | Traces, QTest, GDB/QMP facilities | Build the required harnesses in their own phases, preserve provenance, use independent expectations and sanitize reference-machine captures. Availability upstream is not completed integration here. |

Do not change ordinary architectural semantics merely to suppress an unexplained Apple boot failure. First identify whether the missing behavior belongs to the CPU feature profile, an implementation-defined register, a device, loader state or an upstream defect. Add a reduced regression before changing the corresponding layer. The laboratory boot and any future strict-fidelity path must remain distinguishable.

## Limits and consequences

1. **No automatic Apple personality.** A generic Cortex-A57 or `max` CPU is not a sourced Firestorm/Icestorm profile. `max` reflects QEMU's supported features and some features additionally need machine support. Only advertise behavior established by the project's feature tests. [Q10][qemu-virt] [Q11][qemu-features]

2. **Pointer authentication needs algorithm-level review.** QEMU documents a default implementation-defined, noncryptographic PAuth algorithm unless another supported algorithm is selected. Enabling a PAuth feature bit is therefore insufficient evidence of Apple's algorithm or key/state behavior. P055 still requires source-backed success/failure vectors. [Q11][qemu-features]

3. **Atomics and memory ordering are not inherited proofs.** The MTTCG design discusses host/guest ordering, synchronization and an ABA caveat in exclusive-access implementation: a value can change and return to its earlier value between observations. This is a source-identified risk to investigate for the selected backend/revision, not a demonstrated bug in this repository. Preserve P039 and P091–P105 tests and reference comparisons; passing a bounded corpus cannot enumerate all allowed interleavings. [Q12][qemu-mttcg]

4. **Functional execution does not model silicon timing.** TCG instruction counts and virtual time are not Firestorm/Icestorm cycles, pipelines or cache-latency measurements. QEMU's `icount` mode also conflicts with multithreaded TCG. A future experiment must state its scheduling/time mode; single-thread execution alone does not establish deterministic replay, while MTTCG does not promise repeatable interleavings. No such mode is being certified in P005. [Q12][qemu-mttcg] [Q13][qemu-icount]

5. **Board compatibility remains a separate problem.** Reusing translation does not supply Apple UART, AIC, DART, ANS or firmware initialization. The preserved [fidelity classifications](../ARCHITECTURE.md#p002-fidelity-contract) distinguish CPU, peripheral and whole-machine evidence. The [exploratory exclusions](../EXPLORATORY_SCOPE.md) remain binding; GPU graphics and unmodified macOS are unimplemented and outside required v0.1 scope.

6. **Cross-ISA speed is not guaranteed.** This phase contains no performance measurements or throughput promise. Later measurements must record the host, emulator revision, feature profile and workload. Optimize only after correctness and profiling identify a bottleneck; retain a reference path when changing execution strategy.

7. **Source revisions and dependencies require separate control.** The evidence below reuses QEMU commit `4fc49f46dc95d4a27de2509e7fceb2931e91faeb` (`v11.1.2`). That pins the reviewed text, not the local executable, CI package or a completed reproducible build. The existing setup script's tag default remains scaffolding: P017 must establish and verify the immutable build dependency; P019/P020 cover isolated checkout/configuration. No QEMU source is vendored here. P006 records the separate [licensing and redistribution boundaries](../LICENSING.md); future third-party imports and binary packages still need their own review.

## Executable expression of the decision

The existing runner now constructs this command using a subprocess argument list, with no shell expansion or alternate accelerator:

```sh
qemu-system-aarch64 -accel tcg -M virt -cpu cortex-a57 -m 128M -smp 1 \
  -nographic -monitor none -serial stdio -no-reboot \
  -kernel experiments/arm64-virt-smoke/build/hello.elf
```

Use `python3 tools/run_arm64_smoke.py experiments/arm64-virt-smoke/build/hello.elf` after compiling the existing payload. It prints `ARM64 baseline OK` and then intentionally waits forever; the runner bounds execution with a finite, positive timeout of at most 300 seconds (eight seconds by default). The cap is a project smoke-test budget that also avoids platform timeout overflow, not a hardware timing value. The marker with a normal zero exit, or with the runner's deliberate timeout termination, is a smoke success. A nonzero emulator failure after the marker is a failure, as are missing inputs, launch failures and absence of the marker. This is a deliberately small toolchain witness, not a general guest-success protocol or an M1 correctness test.

The focused regressions check explicit TCG selection, safe argument boundaries and these success/failure paths. The existing target validator also checks this decision's identity declaration. No mechanical check can decide whether the tradeoff reasoning is correct; source and independent human/agent review remain part of the phase evidence.

## Reconsideration criteria and handoff

Reopen this decision with a new, linked ADR if a reduced test demonstrates a required guest-visible semantic that cannot reasonably be implemented in this foundation, if a measured requirement cannot be met after profiling, or if maintaining the necessary upstream changes becomes impractical. Present a working alternative, its target/host coverage, independently checked results and migration cost. An unexplained boot failure or an attractive benchmark alone does not identify the correct replacement.

P005 is complete when this decision records the selected executor, alternatives and limits, its narrow executable enforcement passes regression checks, and the [phase report](../phases/P005.md) records verification. P006 and P016–P030 retain their own acceptance conditions; none becomes complete through this ADR. The Apple CPU/board phases and G4 remain future work.

## Primary sources

QEMU links are immutable evidence snapshots. The Unicorn and gem5 pages are live primary project documentation, reviewed 2026-10-23; they are not selected dependencies. The [reference register](../REFERENCES.md#p005-emulation-foundation-evidence) records each source's supported claim.

[qemu-about]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/about/index.rst
[qemu-emulation]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/about/emulation.rst
[qemu-system]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/introduction.rst
[qemu-tcg]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg.rst
[qemu-qom]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/qom.rst
[qemu-memory]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/memory.rst
[qemu-qtest]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/testing/qtest.rst
[qemu-user]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/user/main.rst
[qemu-vmapple]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/vmapple.rst
[qemu-virt]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/virt.rst
[qemu-features]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/cpu-features.rst
[qemu-mttcg]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/multi-thread-tcg.rst
[qemu-icount]: https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg-icount.rst
[unicorn]: https://www.unicorn-engine.org/
[gem5]: https://www.gem5.org/documentation/general_docs/cpu_models/O3CPU
