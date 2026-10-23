# Emulator architecture and acceptance gates

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## P001 target charter

The first machine is the **original Apple M1 SoC in the 2020 Mac mini board J274**. This selection is a project requirement, not a claim of implemented compatibility. `hardware/t8103.json` is the machine-readable identity record; the following names refer to different layers of that one target.

| Identity layer | Selected value | Evidence |
|---|---|---|
| Marketed SoC | Apple M1 | Linux Apple binding; Apple product specifications |
| SoC identifier | `T8103` | Linux Apple binding |
| Internal SoC name | `H13G` | Linux Apple binding; Asahi SoC names |
| Reference product | Mac mini (M1, 2020) | Apple specifications; Linux J274 description |
| Board / ADT target type | `J274` | Linux J274 description |
| Model identifier | `Macmini9,1` | Asahi device list |
| Product identifier | `J274AP` | Asahi device list |
| Linux root compatible, in order | `apple,j274`, `apple,t8103`, `apple,arm-platform` | Linux J274 description |

The exact source URLs and immutable revisions are recorded in [P001 identity evidence](REFERENCES.md#p001-identity-evidence). `H13G` is an internal SoC name, not a CPU instruction set or board. `J274AP` and `Macmini9,1` identify the product/model; neither replaces `J274` in the Linux board compatible. The Linux binding lowercases the ADT target type and SoC ID for compatible strings. The sources establish identity; they do not establish reset state, register semantics, ISA extension coverage or timing.

### Excluded variants and boards

P001 selects exactly one SoC/board pair. All other pairs are excluded from the initial target, including:

| Excluded hardware | Identifier or category | Scope decision |
|---|---|---|
| M1 Pro, M1 Max, M1 Ultra | `T6000`, `T6001`, `T6002`, respectively | Separate SoCs; the M1 family name does not extend T8103 coverage. |
| M1 MacBook Pro and MacBook Air | T8103 boards `J293` and `J313` | A shared SoC does not validate a different board. |
| M1 iMac, four-port and two-port models | T8103 boards `J456` and `J457`, respectively | Board-specific devices/configuration need separate work. |
| M2 and later M-series | All generations and variants after M1 | Outside the original T8103 target. |
| A-series products | All A-series SoCs and boards | Shared CPU lineage does not imply SoC compatibility. |
| Any other board or product | Every board other than J274, including other products marketed with M1 | No implicit expansion to an unlisted target. |

The pinned Linux Apple binding and Asahi device list support the named board and SoC distinctions. The broader exclusions are deliberate project scope decisions, not assertions that these machines can never be emulated.

Generic QEMU `virt` remains a toolchain experiment with different peripherals. QEMU `vmapple` is a separate virtual platform. Neither is an alternative spelling or implementation of the selected J274/T8103 machine; the [upstream QEMU references](REFERENCES.md#other-development-references) describe those platforms. Existing generic smoke-test results do not count as target validation.

### Entrypoint consistency contract

The project overview/setup entrypoints are `README.md`, `ROADMAP_365_PHASES.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md` and `docs/REFERENCES.md`. Each has one visible research-target declaration near the top. `hardware/t8103.json` carries the structured identity, source references and exclusions.

Run `python3 tools/validate_target.py` to check those declarations against the frozen P001 identity. The check also rejects malformed identity data, a missing source, altered compatible values and incomplete or contradictory exclusions. It reports paths/fields and exits nonzero on failure; CI runs it alongside the existing roadmap, hardware and unit checks. The regression suite mutates the metadata and each entrypoint to verify that failures are detected.

This is a declaration consistency check, not a semantic audit of all prose or a hardware probe. Internal assembly/linker files describe the generic experiment rather than an Apple target. A future project overview/setup entrypoint must be added to the validator inventory. Any future expansion of the first target needs an explicit charter change, revised evidence and corresponding tests; changing one banner is insufficient.

## Scope

**SoC:** original Apple M1 T8103/H13G. **Board:** 2020 M1 Mac mini/J274. **Host:** Linux x86_64/WSL2. **CPU execution:** QEMU AArch64 TCG plus Apple-specific identity and system registers. **Guest:** bare-metal tests, then a T8103-targeted Linux kernel and initramfs. **Release goal:** headless Linux boot using Apple-compatible peripherals, not generic QEMU `virt` hardware.

The `experiments/arm64-virt-smoke` executable runs on QEMU **`virt` only**; it establishes a reproducible toolchain and must not be called M1 emulation.

## Functional architecture

```mermaid
flowchart TD
    Guest[ARM64 guest] --> Loader[Laboratory direct loader]
    Loader --> CPU[QEMU TCG with Apple CPU profile]
    CPU <--> Bus[T8103 address space]
    Bus <--> RAM[RAM and reservations]
    Bus <--> Devices[UART and platform devices]
    Devices --> AIC[AIC external IRQs and AIC IPIs]
    AIC -->|IRQ| CPU
    Timers[Architectural timers] -->|Separate FIQ path| CPU
    DMA[Later PCIe devices] --> DART[DART DMA translation]
    DART --> RAM
    ANS[Later ANS storage] --> NVMMU[Embedded NVMMU command checks]
    NVMMU --> RAM
```

QEMU handles ordinary ARM64 instruction execution and memory translation. Project-specific code handles the M1 CPU profile, board initialization, MMIO state machines and Apple-specific guest-visible interfaces. Instruction-accurate emulation does not require replicating Firestorm's internal out-of-order pipeline or cycle timing.

The M1 architectural timers bypass AIC and signal CPU FIQ. Linux's AIC driver also dispatches these FIQs, but that software integration must not be mistaken for timer routing through AIC hardware. Apple fast-IPI system-register pathways are separate from AIC-generated IPIs and need their own source-backed model if advertised. See the [Asahi AIC notes](https://asahilinux.org/docs/hw/soc/aic/) and [system-register notes](https://asahilinux.org/docs/hw/cpu/system-registers/).

Do not attach every DMA-capable device to DART by analogy. T8103 ANS has an embedded NVMMU with command-tag-indexed TCBs; SART separately authorizes RTKit shared-memory regions and applicable vendor-command buffers. The Apple NVMe submission array is indexed by command tag, not an ordinary NVMe submission ring. Preserve these distinctions when modeling storage; see the [Linux Apple NVMe driver](https://github.com/torvalds/linux/blob/master/drivers/nvme/host/apple.c).

## Hardware-modeling contract

1. Use `hardware/t8103.json` for source-linked, confidence-marked physical-address facts. An address is not proof of register semantics.
2. For every implemented register, specify reset state, read/write width, mask, side effects, invalid accesses, and tests; model W1C/W1S, level/edge and interrupt acknowledgment correctly.
3. Never silently return zero from all missing MMIO. Unknown accesses need explicit diagnostics and consistent fault/stub policy.
4. Only advertise ARM/Apple architectural features that are implemented and tested. Implementation-defined registers must have observed behavior or clearly documented stubs.
5. Never mark a phase done from source code alone; record tests and, if possible, sanitized physical-hardware comparison traces.

## Boot strategy

**Laboratory boot:** Load test ELF or decompressed Linux Image into RAM, set PC, registers and initial state, supply the DTB physical address in `x0` under the AArch64 Linux boot protocol. This explicitly bypasses Apple's normal Boot ROM/iBoot/SEP startup and is *not* full firmware emulation.

**Apple-compatible preboot:** Later reproduce the state expected by an M1-targeted kernel or m1n1 payload, model ADT/FDT distinctions, initialize peripherals and optional coprocessors; do not distribute Apple-proprietary firmware.

**macOS:** Separate exploratory track outside v0.1. QEMU `vmapple` virtual-machine support is not a physical T8103 model and requires an Apple Silicon macOS host in its documented configuration.

## Measurable development gates

| Gate | Required observable test | Fidelity status |
|---|---|---|
| G0 | `ARM64 baseline OK` on QEMU `virt` | Toolchain only; **not M1** |
| G1 | Original ARM64 test ELF executes on new `apple-m1-lab` machine | First Apple CPU/board skeleton |
| G2 | Serial output via verified T8103 Apple UART MMIO | First M1 peripheral |
| G3 | AIC device IRQ, separate timer FIQ and two-core IPI acknowledge correctly | Apple interrupt subsystem |
| G4 | T8103-targeted Linux reaches BusyBox shell via Apple UART/AIC | **v0.1 breakthrough** |
| G5 | Sanitized M1 hardware traces match emulator device tests | Validated coverage |
| G6 | Persistent root filesystem through ANS/NVMMU with required SART/RTKit initialization | Extended headless system |

## Important risks

- **CPU gaps:** Apple-specific ID/sysregs, permissions, pointer authentication and exception behavior may differ from generic QEMU CPU profiles. Trap, characterize and test.
- **Firmware state:** M1 Linux expects much pre-kernel initialization. Start with directly configured Linux and progressively recreate required states, rather than claiming stock boot.
- **Apple AIC:** Do not substitute ARM GIC and claim hardware fidelity. Model its masks, targeting, acknowledgment and IPI delivery.
- **MMIO uncertainty:** Cross-check Asahi documentation, Linux DT/driver source and real-mac traces. Separate observed facts from hypotheses.
- **Long tail:** AGX, SEP, RTKit, macOS and cycle-accurate microarchitecture remain independent open-ended research efforts.

## Differential validation workflow

On a safe, isolated owner-controlled M1 research installation, run a narrowly scoped experiment; collect m1n1 CPU/MMIO events; **sanitize device identifiers, keys and all unrelated data**; replay the same operations on QEMU; compare register results, interrupts and state transitions; add regression tests. Preserve source revisions and firmware/kernel version in trace metadata. Never change NOR flash or production boot policies merely to gather an emulator trace.
