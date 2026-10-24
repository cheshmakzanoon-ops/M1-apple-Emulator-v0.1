# Primary technical references

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## P001 identity evidence

Reviewed 2026-10-23. These immutable source snapshots establish names and scope; they do not select a kernel version for future boot work. Source IDs match `hardware/t8103.json`.

| Source ID | Primary source and supported claim |
|---|---|
| `linux_apple_binding` | [Linux Apple ARM machine binding](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/devicetree/bindings/arm/apple.yaml): M1 marketing name, H13G internal name, T8103 SoC ID; Linux compatible naming; distinct T8103 boards and T6000/T6001/T6002 variants. |
| `linux_j274` | [Linux J274 board description](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/arch/arm64/boot/dts/apple/t8103-j274.dts): J274 target type, Mac mini product, ordered root compatible values. |
| `asahi_devices` | [Asahi device list](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/devices/device-list.md): Macmini9,1 device identifier, J274AP product identifier and T8103 mapping. |
| `asahi_soc_codenames` | [Asahi SoC names](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/soc/soc-codenames.md): corroborating M1/H13G/T8103 mapping and distinctions from A14, M1 variants and M2. |
| `apple_mac_mini_2020` | [Apple Mac mini (M1, 2020) specifications](https://support.apple.com/en-us/111894): product name/year and Apple M1 chip. This is a live support page without an immutable public revision; retrieval date is recorded above. |

Linux identity evidence is pinned to the `v6.12` commit `adc218676eef25575469234709c2d87185ca223a`; Asahi documentation is pinned to `0d1f8917fa88745d62a4c05d802c4a7298c8616b`. Linux and Asahi reflect related upstream research, so their agreement is corroboration, not a claim of two independent hardware measurements. Apple corroborates the product identity. No physical-hardware experiment was needed or performed for P001.

## P002 fidelity evidence

Reviewed 2026-10-23. These sources support separating architectural behavior, Apple CPU details, peripherals and whole-machine workloads. The level names, evidence requirements and gate mappings in [the P002 contract](ARCHITECTURE.md#p002-fidelity-contract) are project policy inferred from those boundaries; the sources do not certify any implementation in this repository.

| Primary source | Boundary supported |
|---|---|
| [Arm CPU architecture](https://www.arm.com/architecture/cpu) | The architectural contract covers instruction, exception and memory models; microarchitecture separately chooses pipeline, cache and performance implementation. A functional ISA result is not a cycle-timing result. Live vendor page; reviewed on the date above. |
| [Asahi Apple system-register research](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/cpu/system-registers.md) | Apple HID/EHID and other implementation-defined registers are a distinct guest-visible surface alongside architectural ID registers. The research includes uncertainty and unknown registers; it is not a complete silicon specification. |
| [Asahi AIC research](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/soc/aic.md) | Peripheral interrupt state and acknowledgment need device-specific testing; architectural timer delivery bypasses AIC and uses CPU FIQ. CPU execution and interrupt-controller correctness are separate obligations that meet in integration tests. |
| [QEMU generic ARM virt platform](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/virt.rst) | This intentionally virtual platform does not model a physical machine. Its PL011/GIC interfaces cannot establish T8103 UART/AIC fidelity. The documentation also distinguishes CPU feature support from features requiring machine support. |
| [QEMU VMApple model](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/vmapple.rst) | VMApple reproduces the Virtualization.framework device model, with documented Apple Silicon/macOS host requirements. That is a different target from physical J274/T8103 hardware. |
| [QEMU TCG instruction counting](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg-icount.rst) | Instruction counting and virtual time do not model actual per-instruction silicon timing. Determinism is not evidence of cycle accuracy. |
| [Linux AArch64 boot protocol](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/arch/arm64/booting.rst) | Linux entry has independent RAM, device-tree, image and CPU-state conditions, including DMA quiescence. A reproducible whole-machine witness must identify its platform and boot assumptions. |
| [Apple silicon boot process](https://support.apple.com/en-ca/guide/security/secac71d5623/web) | Apple describes Boot ROM, LLB, iBoot, firmware and LocalPolicy/Secure Enclave dependencies. A directly loaded Linux workload does not exercise that chain or establish macOS compatibility. Live vendor page; reviewed on the date above. |

QEMU evidence is pinned to `4fc49f46dc95d4a27de2509e7fceb2931e91faeb` (`v11.1.2`), verified through the upstream repository. Asahi and Linux use the same immutable revisions recorded for P001. Pins are evidence snapshots, not a new implementation dependency or a completed upstream-foundation phase. No new hardware values, Apple firmware, register implementation or physical-machine measurement is introduced by P002.

## P003 Linux witness evidence

Reviewed 2026-10-23. These primary sources support the source-observable profile and boot prerequisites in [the G4 witness specification](LINUX_BOOT_MILESTONE.md). The one-CPU profile, three trials, challenges and timeout budgets are project acceptance choices, not hardware facts. Linux source observations retain the immutable v6.12 revision above. Building/selecting the actual Linux/BusyBox inputs remains P196–P198 work.

| Source ID | Primary source and supported observation |
|---|---|
| `linux_boot` | [Pinned AArch64 boot protocol](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/arch/arm64/booting.rst), also [rendered for 6.12](https://docs.kernel.org/6.12/arch/arm64/booting.html): image placement, FDT/register handoff, privilege/MMU/cache/timer state, reservations and DMA quiescence. |
| `linux_j274` | [J274 DTS](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/arch/arm64/boot/dts/apple/t8103-j274.dts): root target compatibles and board-specific enabled devices. |
| `linux_t8103` | [T8103 DTSI](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/arch/arm64/boot/dts/apple/t8103.dtsi): Apple UART/AIC/timer connections and UART clock/power dependencies. Linux's UART node window and the broader reference-map survey are different scopes; P003 changes neither. |
| `linux_uart` | [Samsung/Apple serial driver](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/tty/serial/samsung_tty.c): `apple,s5l-uart`, `ttySAC` naming, physical `samsung-uart` driver and platform-device-named IRQ action. [Serial Kconfig](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/tty/serial/Kconfig) describes built-in serial/console options. |
| `linux_serial_core` | [Serial core](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/tty/serial/serial_core.c): the tty registration uses the serial port device as parent, not necessarily the physical UART. |
| `linux_serial_bus` | [Serial base bus](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/tty/serial/serial_base_bus.c): controller and port devices are nested below the physical device. The witness must check ancestry and the physical driver, rather than a guessed parent depth. |
| `linux_aic` | [Apple AIC driver](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/irqchip/irq-apple-aic.c): separate `AIC` and `AIC-FIQ` irqchip names; platform-specific initialization obligations. |
| `linux_timer` | [Architectural timer driver](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/clocksource/arm_arch_timer.c): `arch_timer` action names and per-CPU interrupt setup. |
| `linux_irq_proc` | [IRQ proc output](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/kernel/irq/proc.c): CPU columns, unsigned counters, chip/hardware-IRQ fields and action names. Runtime virtual IRQ numbers are not hardware constants. |
| `linux_initramfs` | [Initramfs documentation](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/filesystems/ramfs-rootfs-initramfs.rst), also [rendered for 6.12](https://docs.kernel.org/6.12/filesystems/ramfs-rootfs-initramfs.html): RAM-backed root, `/init` and cpio generation/file lists. [Reproducible builds](https://docs.kernel.org/6.12/kbuild/reproducible-builds.html) identifies additional toolchain/environment controls. |
| `asahi_aic` | [Pinned Asahi AIC research](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/soc/aic.md): device-source masking/acknowledgment and architectural timers bypassing AIC for CPU FIQ. |
| `busybox` | [Official BusyBox applet reference](https://busybox.net/downloads/BusyBox.html): small shell/system utilities for the guest probe and init. This live reference has no immutable version; actual BusyBox source/configuration/binary hashes are mandatory future evidence, not supplied runtime results. |

The review caught the Linux serial-core hierarchy distinction and the difference between aggregate UART IRQ activity and proof of RX causality. The former is exercised with synthetic sysfs fixtures; the latter remains an explicit G2/G3 trace prerequisite. No counter/string in a fabricated transcript can authenticate a device model. No physical machine was modified or measured.

## P004 exploratory scope evidence

Reviewed 2026-10-23. P004 reuses the existing immutable QEMU and Asahi evidence revisions. These sources support distinctions between functional emulation, timing, graphics and physical-machine boot; they do not certify this project. The explicit v0.1 exclusions and promotion criteria are project policy.

| Source ID | Primary evidence and relevance |
|---|---|
| `qemu-icount` | [Pinned QEMU instruction-counting documentation](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg-icount.rst) separates executed instructions/virtual time from real microarchitectural instruction latency. P102/P344 results cannot establish cycle fidelity. |
| `asahi-agx` | [Pinned Asahi AGX notes](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/soc/agx.md) describe the kernel-facing ASC/firmware, UAT, queue, work and event interfaces. The notes expressly exclude userspace shader/texture/pipeline details. A narrow device or framebuffer experiment does not establish a complete rendering stack. |
| `apple-boot` | [Apple silicon boot process](https://support.apple.com/en-ca/guide/security/secac71d5623/web) describes Boot ROM, LLB, iBoot, firmware and LocalPolicy/Secure Enclave responsibilities. The laboratory Linux loader does not exercise that physical-machine chain. Live vendor page, reviewed on the date above. |
| `qemu-vmapple` | [Pinned QEMU VMApple documentation](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/vmapple.rst) describes a Virtualization.framework-compatible device model, distinct from physical J274/T8103 hardware. Results on that virtual platform cannot validate the selected physical target. |

No new addresses, timing constants, device behavior, firmware payloads or reference-machine measurements are introduced. The [P004 scope specification](EXPLORATORY_SCOPE.md) records bounded research and the evidence needed before any future scope change.

## P005 emulation foundation evidence

Reviewed 2026-10-23. [ADR 0001](decisions/0001-qemu-tcg.md) selects full-system AArch64 TCG and records alternatives and limits. The decision and division of work are project judgments based on these upstream capabilities; the sources do not certify an Apple CPU or board implementation.

All QEMU evidence links below use the existing immutable source snapshot `4fc49f46dc95d4a27de2509e7fceb2931e91faeb`. The upstream `v11.1.2` tag object `ceaea6cb3e2a7d966f9ca97c7ebb5b88cd764dd0` was resolved to that commit again for P005. This verifies the repository mapping, not a cryptographic release-signature check or a completed P017 build pin. Local/CI distribution packages are separate executables whose actual versions belong in runtime evidence.

| Source ID | Primary evidence and supported claim |
|---|---|
| `Q1` | [QEMU modes](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/about/index.rst): full-system CPU/memory/device execution and user-mode process translation have different contracts; hardware accelerators execute guest code directly on the host CPU. |
| `Q2` | [QEMU emulation](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/about/emulation.rst): TCG supports software emulation of AArch64 on supported hosts, allowing execution across ISA boundaries. |
| `Q3` | [System introduction](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/introduction.rst): TCG host support, hardware-accelerator host constraints, character backends, QMP and debugging facilities. |
| `Q4` | [Translator internals](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg.rst): translated blocks, architectural state, exceptions, software MMU and MMIO callbacks. |
| `Q5` | [QEMU Object Model](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/qom.rst): typed objects and composition for future machine/device integration. |
| `Q6` | [Memory API](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/memory.rst): RAM, MMIO and address-space composition; the framework does not supply Apple register behavior. |
| `Q7` | [QTest](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/testing/qtest.rst): device emulation testing independent of normal guest instruction execution. |
| `Q8` | [User-mode emulation](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/user/main.rst): host syscall translation and process/thread behavior; a different execution layer from this project's guest kernel. |
| `Q9` | [VMApple](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/vmapple.rst): Virtualization.framework-compatible platform and documented Apple Silicon/macOS/HVF configuration, distinct from physical T8103. |
| `Q10` | [ARM virt](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/virt.rst): synthetic platform, PL011/GIC, generic CPU models and CPU/machine feature interaction. |
| `Q11` | [ARM CPU features](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/cpu-features.rst): configuration-dependent coverage and PAuth algorithm selection, including the default QEMU-specific noncryptographic algorithm. |
| `Q12` | [Multithreaded TCG](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/multi-thread-tcg.rst): host/guest memory order, scheduling, synchronization, absence of cache modeling and the documented exclusive-access ABA caveat. This motivates investigation, not a claim that a specific project test has already failed. |
| `Q13` | [Instruction counting](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg-icount.rst): virtual-time accounting is not silicon cycle timing; `icount` is incompatible with MTTCG. |
| `U1` | [Official Unicorn project](https://www.unicorn-engine.org/): QEMU-derived CPU emulation framework, embedding API and instrumentation; useful as a bounded alternative, not an automatically independent oracle. Live page reviewed on the date above. |
| `G1` | [gem5 O3CPU](https://www.gem5.org/documentation/general_docs/cpu_models/O3CPU): configurable detailed CPU model loosely based on Alpha 21264. The need for Apple-specific parameters is a project inference; this source is not a Firestorm timing specification. Live page reviewed on the date above. |

P005 introduces no hardware address, proprietary asset or new third-party source dependency. Foundation selection does not complete the later license review, immutable build selection, CPU conformance suite or T8103 implementation.

## P006 licensing evidence

Reviewed 2026-10-23. The [licensing and redistribution policy](LICENSING.md) records the source-only dependency review and the procedures required for future imports and binary releases. Its primary-evidence inventory also covers the declared development tools and CI actions. P006 classified exact project paths, twelve external/reference component groups and seven reviewed declaration/build/runner inputs; P007 extends the current [machine-readable inventory](licensing.json) to nine input surfaces. This is not a transitive build SBOM or a license grant for referenced material.

| Primary evidence | Review result |
|---|---|
| [QEMU LICENSE](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/LICENSE) and [COPYING](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/COPYING) | Separate whole-emulator GPLv2, file-specific terms, mixed TCG terms and firmware licenses. Future distribution needs the applicable notices and corresponding-source review. |
| [Linux COPYING](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/COPYING) and [file-license rules](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/process/license-rules.rst) | GPLv2-only kernel with the Linux syscall exception; copied files retain their own SPDX choices and notices. |
| [Asahi documentation LICENSE](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/LICENSE) | CC BY 3.0; copied or adapted expressive material cannot silently inherit project MIT terms. |
| [m1n1 README license section](https://github.com/AsahiLinux/m1n1/blob/7cde7d1a784d851ebfee5579fa363c38b14150c0/README.md) | Version-dependent licensing: MIT through 1.9.9, GPLv2-or-later from 2.0.0, plus separate embedded-component terms. This new pin records source review only; no m1n1 build is selected. |
| [BusyBox license policy](https://busybox.net/license.html) | GPLv2-only combined distribution; future guest binaries need their exact source, configuration, component and notice review. |
| [Asahi platform introduction](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/platform/introduction.md), [Apple agreement index](https://www.apple.com/legal/sla/) and [example macOS agreement](https://www.apple.com/legal/sla/docs/macOSTahoe.pdf) | Public access to firmware is not redistribution permission. The project excludes Apple proprietary assets; actual applicable agreements and open-source exceptions must be distinguished. |

The QEMU, Linux and Asahi evidence pins are unchanged from previous phases. All current source files remain project-authored text under the existing MIT grant; no third-party source, license text, executable, guest image or proprietary firmware is newly bundled. Primary-source links support the review and do not complete P017's immutable build pin, later guest preparation or a runtime gate.

## P007 contribution workflow evidence

Reviewed 2026-10-24 against the official Git command manuals and GitHub documentation below. These are live command/service references, not a new toolchain version pin. The policy is an original project decision derived from their documented behavior; it does not require auxiliary branches, configure GitHub protection or certify runtime fidelity.

| Primary source | Consequence for this project |
|---|---|
| [git-add](https://git-scm.com/docs/git-add), [git-diff](https://git-scm.com/docs/git-diff), [git-write-tree](https://git-scm.com/docs/git-write-tree) | Stage selected paths explicitly, review the index and record its immutable tree object before testing. Working files and the index are separate states. |
| [git-archive](https://git-scm.com/docs/git-archive) | Export attributes can affect contents. Compare every exported path, blob and executable bit with the selected tree before trusting tests of the export. |
| [git-commit](https://git-scm.com/docs/git-commit) | A plain commit uses the index, while automatic staging/file arguments and hooks can affect contents. Verify the resulting immutable commit's parent and tree before publication. |
| [git-merge](https://git-scm.com/docs/git-merge), [git-push](https://git-scm.com/docs/git-push) | Normal synchronization uses fast-forward-only merging. An explicit commit-to-main refspec and ordinary non-forced push preserve remote concurrency checks; divergence requires integration review and retesting. |
| [Git optional locks](https://git-scm.com/docs/git#Documentation/git.txt---no-optional-locks), [git-rev-parse](https://git-scm.com/docs/git-rev-parse) | The checkout guard disables optional index refreshes and resolves operation-state paths correctly for both ordinary and linked worktrees. |
| [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [workflow run logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs) | Inspect both required jobs and their logs for the exact push SHA. Push verification happens after publication; a detached pull-request merge run does not replace it. |
| [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) | Required PR reviews and status protection are server configuration, separate from this workflow. The documented direct-main procedure does not require PRs or weaken existing access controls. |

The executable guard, tests and contribution snippets use Python's standard library and already-declared external Git/host tools. No third-party implementation is imported. See the [contribution procedure](../CONTRIBUTING.md) and [P007 report](phases/P007.md) for the exact scope and observed checks.

## Other development references

These are working references, not complete specifications. For each implemented register or device, record an exact upstream revision and independently verify behavior where possible.

| Domain | Source |
|---|---|
| ARM ISA / privilege model | [Arm A-profile architecture](https://developer.arm.com/Architectures/A-Profile%20Architecture) |
| ARM wait and wake semantics | [AArch64 Wait for Interrupt mechanism](https://developer.arm.com/documentation/ddi0487/mc/-Part-D-The-AArch64-System-Level-Architecture/-Chapter-D1-The-AArch64-System-Level-Programmers--Model/-D1-7-Mechanisms-for-entering-a-low-power-state/-D1-7-2-Wait-for-Interrupt-mechanism) — wakeup and exception taking are separate |
| Apple CPU performance | [Apple CPU Optimization Guide](https://developer.apple.com/documentation/apple-silicon/cpu-optimization-guide) |
| Firestorm / Icestorm | [Dougall Johnson CPU research](https://dougallj.github.io/applecpu/firestorm.html) and [Icestorm](https://dougallj.github.io/applecpu/icestorm.html) |
| T8103 device tree | [Linux t8103.dtsi](https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/apple/t8103.dtsi) |
| Mac mini J274 | [Linux t8103-j274.dts](https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/apple/t8103-j274.dts) |
| Apple storage and DMA protection | [Linux Apple NVMe driver](https://github.com/torvalds/linux/blob/master/drivers/nvme/host/apple.c) — NVMMU/TCBs, tag-indexed submissions and SART-protected shared buffers |
| Physical addresses | [Asahi T8103 memory map](https://asahilinux.org/docs/hw/soc/memmap/) |
| Interrupts | [Asahi AIC notes](https://asahilinux.org/docs/hw/soc/aic/) |
| Apple CPU sysregs | [Asahi system register notes](https://asahilinux.org/docs/hw/cpu/system-registers/) |
| Hardware tracing | [m1n1 hypervisor](https://asahilinux.org/docs/sw/m1n1-hypervisor/) |
| Apple firmware DT | [Asahi ADT documentation](https://asahilinux.org/docs/fw/adt/) |
| Linux kernel entry | [Linux AArch64 boot protocol](https://cdn.kernel.org/doc/html/latest/arch/arm64/booting.html) |
| Boot ecosystem | [Asahi introduction](https://asahilinux.org/docs/platform/introduction/) and [Apple silicon boot security](https://support.apple.com/en-ca/guide/security/secac71d5623/web) |
| QEMU emulation | [QEMU ARM systems](https://www.qemu.org/docs/master/system/target-arm.html) and [QEMU tests](https://www.qemu.org/docs/master/devel/testing/main.html) |
| QEMU source baseline | [Official QEMU releases](https://www.qemu.org/download/) — setup targets `v11.1.2`; tag availability checked 2026-10-23 |
| QEMU VMApple | [VMApple documentation](https://www.qemu.org/docs/master/system/arm/vmapple.html) — *different device model, not T8103* |

Do not redistribute Apple ROMs, firmware, proprietary SDKs or unredacted reference-machine data. A QEMU fork must comply with upstream GPL licensing even though the independent code in this repository currently uses MIT.
