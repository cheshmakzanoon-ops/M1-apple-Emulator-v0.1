# Apple M1 / T8103 Emulator — 365-Phase Engineering Roadmap

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are exploratory, unimplemented and not required.

**Canonical project plan | Target: original M1 (T8103), Mac mini J274 | Host: Linux/WSL2 x86_64 | CPU: QEMU AArch64 TCG**

This roadmap deliberately separates a runnable ARM64 toolchain from an Apple M1-compatible system. **P001–P005 are complete; P006–P365 remain unchecked.** See the [P001](docs/phases/P001.md), [P002](docs/phases/P002.md), [P003](docs/phases/P003.md), [P004](docs/phases/P004.md) and [P005 completion evidence](docs/phases/P005.md). P003 freezes the G4 witness; it does not mark G4 passed. P004 freezes exploratory exclusions and grants no runtime capability. P005 selects the QEMU TCG foundation and tests its explicitly generic execution path; no Apple compatibility is awarded. A completed phase requires the check specified below, a commit, and the evidence described in `AGENTS.md`. The last five phases are independent formal release gates. The workstreams are dependency-ordered, although narrowly scoped investigation may happen in parallel without misreporting completed prerequisites.

### Dependency and evidence rules

- P001–P045 establish honest scope, reproducible host tooling, and **generic ARM64 only**. None proves M1 emulation.
- P046–P120 establish the Apple CPU personality, architectural correctness and T8103 board shell.
- P121–P210 implement Apple UART/AIC/timers/SMP/boot and culminate in the **Linux initramfs breakthrough**.
- P211–P285 extend verified DMA/storage/controllers and selected coprocessor interfaces.
- P286–P315 are high-risk **research tracks**, not v0.1 blockers and not promises of GPU or macOS functionality.
- P316–P365 provide differential conformance, performance characterization, integration, releases and independent milestone audits.

`**Check:**` is a testable exit condition, never merely a claim that code was written. Unknown silicon behavior must remain marked unknown until demonstrated. Sources: [`docs/REFERENCES.md`](docs/REFERENCES.md).

## WS01 — Scope, provenance and project governance (P001–P015)

Depends on: none. Outcome: a measurable, legally distributable, non-misleading scope.

- [x] **P001 — Define the original T8103 target** — Record M1/H13G, J274 and excluded variants in the architecture charter. **Check:** all project entrypoints identify the same first SoC and board.
- [x] **P002 — Separate CPU and SoC correctness** — Publish independent definitions for ISA accuracy, Apple CPU profile, peripherals and whole-machine compatibility. **Check:** each release gate identifies its fidelity level.
- [x] **P003 — Freeze the first Linux boot milestone** — Define the initramfs shell on Apple UART/AIC as the v0.1 success criterion. **Check:** G4 has explicit prerequisites and a reproducible witness test.
- [x] **P004 — Describe exploratory non-goals** — Isolate cycle accuracy, GPU graphics and unmodified macOS from required v0.1 scope. **Check:** no milestone falsely lists these as shipped features.
- [x] **P005 — Select upstream emulation foundation** — Document why AArch64 QEMU TCG is the initial executor rather than a second ISA interpreter. **Check:** architecture decision records limits and alternatives.
- [ ] **P006 — Record licensing boundaries** — Distinguish MIT project-authored files, future GPL QEMU-derived code and Apple proprietary assets. **Check:** dependency and redistribution review passes.
- [ ] **P007 — Establish a single main branch policy** — Document one authoritative development branch, safe review and tested commits. **Check:** contribution instructions do not demand auxiliary branches.
- [ ] **P008 — Create source evidence standards** — Require URLs, upstream revisions, confidence and independent validation for each hardware claim. **Check:** the sample T8103 map validates provenance.
- [ ] **P009 — Establish unknown-behavior labels** — Define reference-only, stubbed, tested, inferred and undocumented distinctions. **Check:** a deliberately unsourced device entry is rejected.
- [ ] **P010 — Define device register specification format** — Specify widths, reset values, masks, side effects and errors. **Check:** reviewers can reject an incomplete register specification mechanically.
- [ ] **P011 — Create risk and assumption register** — Track boot firmware, hidden sysregs, AIC, DART, AGX and licensing uncertainties. **Check:** each high-risk assumption has a validation method.
- [ ] **P012 — Establish trace privacy policy** — Forbid committing keys, serials, identifying ADT data, binary firmware and raw private dumps. **Check:** fixture publication instructions include redaction review.
- [ ] **P013 — Assign milestone evidence format** — Specify the exact command, revision, guest image hash, host environment and logs needed for completion. **Check:** a sample phase report satisfies every field.
- [ ] **P014 — Define release compatibility language** — Require terms such as generic ARM, partial T8103, and validated M1 device. **Check:** automated documentation audit catches unsupported full-emulator claims.
- [ ] **P015 — Approve foundation exit gate** — Audit charter, sources, licenses, phase numbering and setup documents. **Check:** governance review records G0 prerequisites and open gaps.

## WS02 — Host development and reproducible QEMU build (P016–P030)

Depends on: WS01. Outcome: deterministic builds and a cross-platform developer entrypoint.

- [ ] **P016 — Baseline supported host environments** — Specify Ubuntu x64 and Windows WSL2 version assumptions and resource budgets. **Check:** a clean host can identify missing prerequisites.
- [ ] **P017 — Pin a QEMU upstream release** — Record a verifiable immutable QEMU reference and official provenance. **Check:** a fresh checkout resolves to the documented tag/commit.
- [ ] **P018 — Bootstrap cross compilation** — Install AArch64 GCC, binutils and required host build tools. **Check:** an ARM64 object file compiles with no host architecture leakage.
- [ ] **P019 — Automate isolated QEMU checkout** — Keep large upstream sources outside tracked project files and detect unexpected versions. **Check:** bootstrap refuses silently changing an existing checkout.
- [ ] **P020 — Configure AArch64 system target** — Build a minimal QEMU AArch64 system binary with debug information. **Check:** its reported configuration contains `aarch64-softmmu`.
- [ ] **P021 — Verify baseline QEMU execution** — Execute a tiny ELF on standard QEMU `virt` without asserting Apple compatibility. **Check:** expected serial text appears on the host.
- [ ] **P022 — Add remote debugger workflow** — Document GDB attach, disassembly, registers and breakpoint use. **Check:** a scripted stop verifies the guest PC.
- [ ] **P023 — Add instruction and exception logging** — Configure isolated logs for guest instructions, CPU state and faults. **Check:** a known illegal instruction generates attributable evidence.
- [ ] **P024 — Introduce QMP monitoring** — Enable structured machine lifecycle and state queries. **Check:** a test can launch, query and stop QEMU without manual input.
- [ ] **P025 — Add deterministic build metadata** — Record compiler, QEMU commit, guest flags and toolchain versions. **Check:** CI artifacts include a complete reproducibility manifest.
- [ ] **P026 — Create Python test runner** — Provide timeouts, captured stdout/stderr and nonzero failures for guest tests. **Check:** a deliberately wrong guest marker fails the runner.
- [ ] **P027 — Establish GitHub Actions baseline** — Run documentation validators, Python units and QEMU `virt` smoke on Linux CI. **Check:** every job is green on a real hosted runner.
- [ ] **P028 — Add fault-injection CI job** — Confirm validation fails for duplicate phases, unsourced map entries and broken tests. **Check:** CI intentionally rejects each negative fixture.
- [ ] **P029 — Document offline reproducibility** — Specify what must be cached and what external sources remain necessary. **Check:** a repeat run uses pinned dependencies only.
- [ ] **P030 — Freeze the development foundation** — Review clean build, test output, debugger access and required tool versions. **Check:** a second fresh environment reproduces G0 results.

## WS03 — Generic ARM64 executable and conformance harness (P031–P045)

Depends on: WS02. Outcome: trusted instruction/exception test machinery, still **not Apple M1**.

- [ ] **P031 — Implement bare-metal ELF linker layout** — Place code/data at a known RAM address under generic ARM `virt`. **Check:** linker map and loaded PC match.
- [ ] **P032 — Test integer arithmetic instructions** — Cover adds, subtracts, shifts, bit operations and flag effects. **Check:** golden register/NZCV vectors pass.
- [ ] **P033 — Test conditional branches** — Exercise conditional jumps, compares, loop termination and branch displacement. **Check:** taken/not-taken paths produce expected traces.
- [ ] **P034 — Test scalar loads and stores** — Cover byte/halfword/word/doubleword accesses and alignments. **Check:** memory images match expected endianness.
- [ ] **P035 — Test call and return state** — Verify `BL`, `BLR`, `RET`, link register and SP alignment. **Check:** nested calls preserve callee/caller state.
- [ ] **P036 — Test SIMD register transfer** — Verify NEON vector moves, packed data and lane extraction. **Check:** compare all destination lanes bit-for-bit.
- [ ] **P037 — Test floating-point exceptional cases** — Cover rounding, NaNs, infinities and FPSR/FPCR effects. **Check:** specified corner cases match independent expected results.
- [ ] **P038 — Test multiply and divide boundaries** — Include signed/unsigned wide products and divide-by-zero semantics. **Check:** comparison vectors expose overflow mistakes.
- [ ] **P039 — Test exclusive load/store loops** — Exercise LDXR/STXR contention and reservation invalidation. **Check:** retries eventually preserve a shared counter.
- [ ] **P040 — Test architectural barriers** — Exercise DMB, DSB and ISB in minimal self-checking guests. **Check:** instruction completion and required ordering observations hold.
- [ ] **P041 — Add exception test payloads** — Intentionally trigger undefined instruction and alignment faults. **Check:** exception syndrome and return paths are logged.
- [ ] **P042 — Add MMU translation payload** — Set EL1 translation tables and compare virtual-to-physical effects. **Check:** mapped page succeeds and unmapped page faults.
- [ ] **P043 — Verify generic timer behavior** — Program architectural timers on `virt` and observe interrupts. **Check:** timer interrupt and acknowledgment tests pass.
- [ ] **P044 — Collect golden baseline artifacts** — Save compact, deterministic expected-state fixtures, not private firmware dumps. **Check:** known mutants are detected by the comparison tool.
- [ ] **P045 — Audit generic ISA test coverage** — Report covered features and unsupported extensions without overstating completeness. **Check:** the ARM-only suite passes and is labeled non-M1.

## WS04 — Apple CPU identity and feature model (P046–P060)

Depends on: WS03. Outcome: defensible Firestorm/Icestorm guest-visible CPU profile.

- [ ] **P046 — Catalog Firestorm core identity** — Collect public MIDR/feature-register evidence for M1 performance cores. **Check:** each exposed ID field has a source and validation status.
- [ ] **P047 — Catalog Icestorm core identity** — Record M1 efficiency-core identity and variant-specific differences. **Check:** E-core evidence does not inherit unsupported P-core features.
- [ ] **P048 — Identify supported ARM architecture extensions** — Build an evidence-backed FEAT_* matrix for original M1. **Check:** each advertised bit has an instruction or trap test.
- [ ] **P049 — Define Apple CPU profile configuration** — Separate P/E identities from the generic TCG instruction executor. **Check:** alternate virtual cores return their configured identity.
- [ ] **P050 — Implement MIDR and MPIDR presentation** — Configure topology/affinity registers for the first Apple CPU profile. **Check:** a bare-metal guest enumerates consistent identities.
- [ ] **P051 — Implement architecture ID register masks** — Expose only the subset actually supported by the emulator. **Check:** guest feature probing never selects an unsupported path.
- [ ] **P052 — Build sysreg trap inventory** — Enumerate unknown `MRS`/`MSR` encodings hit by test guests. **Check:** diagnostics include opcode, EL and core ID.
- [ ] **P053 — Prioritize HID/EHID register study** — Classify implementation-defined control registers by access and observed use. **Check:** undocumented bit definitions remain explicitly unknown.
- [ ] **P054 — Model safe Apple sysreg stubs** — Add narrowly justified values/traps for early boot without pretending functionality. **Check:** tests distinguish stubbed from verified behavior.
- [ ] **P055 — Validate pointer authentication profile** — Test advertised PAuth operations and key/state effects. **Check:** authentication success and failure vectors pass.
- [ ] **P056 — Validate SIMD and crypto exposure** — Confirm Apple-advertised SIMD/CRC/AES paths have executable behavior. **Check:** feature bits correlate with known-answer tests.
- [ ] **P057 — Specify cache-identification registers** — Represent discoverable cache geometry separately from simulated timing. **Check:** guest cache enumeration matches the declared profile.
- [ ] **P058 — Add CPU reset contract** — Define initial PC, PSTATE, exception level and relevant reset register values. **Check:** repeat reset produces identical architectural state.
- [ ] **P059 — Add mixed P/E CPU profile tests** — Verify distinct CPU identities in a shared virtual machine. **Check:** per-core feature reads remain consistent across scheduling.
- [ ] **P060 — Audit Apple CPU profile claims** — Review every implementation-defined response and unknown. **Check:** no unsupported feature is advertised as complete.

## WS05 — Exceptions, privilege and system registers (P061–P075)

Depends on: WS04. Outcome: correct transitions through the guest-visible privilege architecture.

- [ ] **P061 — Define EL1 exception-state fixtures** — Snapshot SPSR, ELR, ESR and FAR around traps. **Check:** exception reports match ARM architectural expectations.
- [ ] **P062 — Exercise synchronous exception vectors** — Validate SVC, illegal opcode and instruction abort entry. **Check:** guest handler receives correct vector class.
- [ ] **P063 — Exercise IRQ and FIQ vectors** — Route injected signals through configured VBAR vectors. **Check:** masking and delivery differ correctly.
- [ ] **P064 — Implement controlled ERET paths** — Validate status restoration and return address handling. **Check:** guest resumes at exact expected EL/PC.
- [ ] **P065 — Test privileged system register access** — Probe permitted and forbidden MRS/MSR from EL0 and EL1. **Check:** privilege violations trap with correct syndrome.
- [ ] **P066 — Test EL2 initial-state options** — Model the supported hypervisor entry mode and relevant HCR behavior. **Check:** controlled EL2-to-EL1 transition passes.
- [ ] **P067 — Verify virtual exception routing** — Exercise HCR-controlled routing of IRQ/FIQ and synchronous traps. **Check:** recorded target EL matches configuration.
- [ ] **P068 — Audit SPSR/PSTATE flags** — Test interrupt masking, condition flags and mode bits under nested exceptions. **Check:** post-return PSTATE equals expected snapshot.
- [ ] **P069 — Implement timer access permissions** — Validate counter/timer exposure from permitted exception levels. **Check:** forbidden access traps, allowed reads progress.
- [ ] **P070 — Model kernel sysreg initialization** — List precisely which system register writes early M1-oriented code requires. **Check:** boot trace has no unexplained register failures.
- [ ] **P071 — Test debug-break exceptions** — Exercise BRK/single-step interfaces needed for GDB. **Check:** debugger receives a stable guest stop reason.
- [ ] **P072 — Validate WFI and WFE semantics** — Separate event state, wake conditions and exception taking, including architecturally permitted early completion. **Check:** predicate-based wait loops make progress and tolerate spurious wakeups without losing notifications.
- [ ] **P073 — Test nested exception handling** — Generate controlled nested interrupts/traps with defined priority. **Check:** return stack restores correct context.
- [ ] **P074 — Add exception trace comparison** — Compare expected/observed ESR, FAR, ELR and PSTATE changes. **Check:** a one-bit wrong syndrome fails the test.
- [ ] **P075 — Gate privileged execution support** — Review EL1/EL2 known gaps and minimum kernel startup requirements. **Check:** privilege suite passes before T8103 boot work.

## WS06 — Virtual memory and cache-coherence semantics (P076–P090)

Depends on: WS05. Outcome: reliable architectural memory, not cycle-level cache simulation.

- [ ] **P076 — Specify stage-one page-table modes** — Document relevant TCR granules, translation levels and address widths. **Check:** every enabled mode has a walk test.
- [ ] **P077 — Verify TTBR selection** — Exercise low/high virtual-address regions and configured TTBR roots. **Check:** mappings resolve through the intended base table.
- [ ] **P078 — Test page permissions** — Cover read/write/execute, user/kernel and execute-never combinations. **Check:** forbidden accesses cause correct faults.
- [ ] **P079 — Test memory attribute indexing** — Validate MAIR and shareability interpretation for normal/device memory. **Check:** device accesses preserve ordered side effects.
- [ ] **P080 — Validate translation fault syndromes** — Cover missing descriptor, access flag and permission failure. **Check:** ESR/FAR contain expected stage and access data.
- [ ] **P081 — Verify TLB maintenance operations** — Change page mappings then invalidate the correct scope. **Check:** stale translations disappear when specified.
- [ ] **P082 — Test cache maintenance instructions** — Cover architected clean/invalidate and instruction synchronization behavior. **Check:** self-modifying test code becomes visible correctly.
- [ ] **P083 — Distinguish physical and virtual watchpoints** — Record translation when tracing guest memory. **Check:** trace identifies source VA and resulting PA.
- [ ] **P084 — Add guard-page fault fixtures** — Place unmapped regions around guest stacks/buffers. **Check:** out-of-range accesses fault deterministically.
- [ ] **P085 — Stress virtual address aliasing** — Map one physical page at multiple virtual addresses. **Check:** writes through one alias appear through the other.
- [ ] **P086 — Test atomics across page boundaries** — Exercise architecturally legal/illegal atomic alignment scenarios. **Check:** memory and syndrome outcomes match specification.
- [ ] **P087 — Validate instruction/data coherency** — Modify executable memory and synchronize as the architecture requires. **Check:** subsequent fetch sees exactly expected instructions.
- [ ] **P088 — Check big-endian feature policy** — Explicitly support or reject non-target endianness modes. **Check:** unsupported modes cannot be accidentally advertised.
- [ ] **P089 — Prepare DMA-visible memory abstractions** — Separate CPU translation from future peripheral IOMMU translation. **Check:** a fake device accesses physical buffers independently.
- [ ] **P090 — Gate architectural memory correctness** — Execute MMU, TLB, privilege and aliasing regression suites. **Check:** baseline tests pass before board mapping starts.

## WS07 — Atomics, ordering, events and CPU correctness (P091–P105)

Depends on: WS06. Outcome: consistent shared-memory execution before SMP drivers.

- [ ] **P091 — Verify LDXR/STXR reservation model** — Build contended loops and failed-exclusive paths. **Check:** exclusive writes fail on conflicting modifications.
- [ ] **P092 — Verify acquire and release operations** — Test LDAR/STLR ordering using guarded producer-consumer exchange. **Check:** stale protected reads are forbidden.
- [ ] **P093 — Validate LSE atomic instructions** — Include CAS, SWP and LDADD variants when advertised. **Check:** return values and atomic updates match oracle.
- [ ] **P094 — Implement memory-order litmus harness** — Run bounded litmus tests for allowed/disallowed AArch64 outcomes. **Check:** forbidden outcomes never appear under stress.
- [ ] **P095 — Test cache-line crossing operations** — Exercise accesses near alignment and region boundaries. **Check:** split accesses are handled or fault according to contract.
- [ ] **P096 — Validate SEV and SEVL behavior** — Wake target WFE loops using events and local event state. **Check:** wakeup is deterministic without unrelated IRQ.
- [ ] **P097 — Verify WFI wakeup routing** — Test pending interrupts before and during WFI with explicit EL routing and PSTATE masks. **Check:** a PSTATE-masked eligible interrupt can end the wait without taking its exception; unmasking permits delivery as specified.
- [ ] **P098 — Model core-local exclusive monitors** — Keep reservation state correctly scoped to each CPU. **Check:** independent cores cannot corrupt one another's reservations.
- [ ] **P099 — Audit memory visibility on reset** — Confirm CPU reset, system reset and RAM persistence semantics. **Check:** documented reset scopes produce expected data retention.
- [ ] **P100 — Extend bounded CPU stress suite** — Generate repeatable concurrent arithmetic, atomic and barrier workloads. **Check:** fixed seeds reproduce failures.
- [ ] **P101 — Add differential register comparisons** — Compare completed guest CPU states to known architectural reference results. **Check:** any mismatched flag or register fails with a concise diff.
- [ ] **P102 — Validate instruction count accounting** — Measure retired guest instructions without confusing them with real Firestorm cycles. **Check:** simple known-length programs report consistent counts.
- [ ] **P103 — Add reset-versus-interrupt race tests** — Inject reset near atomic and IRQ sequences. **Check:** guest never observes impossible half-reset state.
- [ ] **P104 — Document CPU limitations explicitly** — Classify unsupported PAuth/AMX/PMU and other extensions as unknown or unimplemented. **Check:** feature documentation matches the actual probes.
- [ ] **P105 — Freeze foundational CPU test gate** — Run the combined instruction, sysreg, memory and synchronization suite. **Check:** G1 CPU prerequisites pass with reproducible logs.

## WS08 — QEMU T8103 board and physical address decoder (P106–P120)

Depends on: WS07. Outcome: a distinct Apple machine model instead of renamed `virt`.

- [ ] **P106 — Define T8103 machine QOM type** — Register an `apple-m1-lab` board model with a unique machine identifier. **Check:** QEMU enumerates the new machine by name.
- [ ] **P107 — Reconcile published physical map** — Cross-check Asahi survey and Linux T8103 DTS with exact source revisions. **Check:** every declared region has non-overlapping ranges and provenance.
- [ ] **P108 — Create memory-region topology** — Instantiate mapped DRAM, reserved regions and a deliberate unmapped policy. **Check:** address-decoding test distinguishes all three.
- [ ] **P109 — Add safe lab memory sizing** — Support small guest RAM for testing without asserting physical retail M1 equivalence. **Check:** configuration warns when using a reduced fidelity profile.
- [ ] **P110 — Model board-specific J274 description** — Separate generic T8103 SoC blocks from Mac mini board devices. **Check:** machine configuration selects the documented J274 device set.
- [ ] **P111 — Instantiate one Apple CPU** — Create P-core profile and reset PC/state under the new machine. **Check:** bare-metal test executes without any `virt` board creation.
- [ ] **P112 — Implement board reset sequencing** — Reset all mapped peripherals and CPU state through QEMU lifecycle. **Check:** two consecutive boots produce identical initial snapshots.
- [ ] **P113 — Add unmapped MMIO diagnostics** — Record read/write address, width, value, CPU and PC for unknown transactions. **Check:** bogus address triggers an attributable diagnostic.
- [ ] **P114 — Define MMIO width and alignment policy** — Respect device-specific 8/16/32/64-bit access constraints. **Check:** invalid-width guest access has a tested outcome.
- [ ] **P115 — Register stub peripheral placeholders** — Reserve only documented ranges, without pretending they function. **Check:** guest detects unsupported access rather than fabricated success.
- [ ] **P116 — Add machine configuration introspection** — Expose chosen core count, memory size and device availability to test harness. **Check:** QMP/output matches actual instantiated topology.
- [ ] **P117 — Validate physical mapping boundaries** — Probe first, last and adjacent bytes around each known MMIO window. **Check:** no accidental overlaps or aliasing occur.
- [ ] **P118 — Add one-core execution smoke** — Boot a simple ELF through the custom machine at selected RAM address. **Check:** G1 proves instruction execution on T8103 board shell.
- [ ] **P119 — Add machine-wide snapshot fixture** — Serialize deterministic reset/device state for differential regression. **Check:** restoring a snapshot does not change observable base state.
- [ ] **P120 — Gate board identity and map** — Audit machine separation, physical ranges, stubs and reset semantics. **Check:** G1 passes with no generic `virt` peripheral dependency.

## WS09 — Apple serial UART and console subsystem (P121–P135)

Depends on: WS08. Outcome: a real Apple-addressed host-visible console.

- [ ] **P121 — Research T8103 UART block** — Extract register offsets, access widths and clock assumptions from drivers and traces. **Check:** initial register sheet identifies evidence for each used offset.
- [ ] **P122 — Specify UART reset registers** — Define transmitter status, FIFO and control defaults. **Check:** post-reset reads match the modeled known state.
- [ ] **P123 — Implement TX data register** — Send guest bytes written to Apple UART MMIO to a host character backend. **Check:** a one-byte guest write produces one host byte.
- [ ] **P124 — Implement TX ready/busy behavior** — Respond to status polling without invented perpetual readiness. **Check:** tight guest transmit loops complete predictably.
- [ ] **P125 — Implement RX register behavior** — Accept injected host bytes with correct empty/nonempty status. **Check:** guest reads preserve byte ordering.
- [ ] **P126 — Add UART FIFO semantics** — Model documented queue depth, overflow and clear operations. **Check:** boundary tests detect FIFO overflow behavior.
- [ ] **P127 — Implement baud and line-control stubs** — Document which configuration bits matter for functional serial semantics. **Check:** unsupported settings remain visible as limitations.
- [ ] **P128 — Connect UART interrupts to AIC placeholder** — Route TX/RX event levels through a typed interrupt interface. **Check:** device IRQ toggles on tested queue changes.
- [ ] **P129 — Validate endianness and widths** — Test legal transmit widths, illegal widths and partial writes. **Check:** serial output cannot be corrupted by silently accepted bad accesses.
- [ ] **P130 — Add minimal M1 UART guest** — Replace the generic PL011 experiment with Apple-addressed MMIO writes. **Check:** serial text appears only under the custom T8103 machine.
- [ ] **P131 — Implement QTest UART register suite** — Exercise reset, TX/RX, FIFO, status and interrupt transitions. **Check:** all modeled registers have unit tests.
- [ ] **P132 — Compare UART behavior with physical M1** — Gather safe trace/driver evidence for relevant transitions. **Check:** identical TX sequence produces equivalent register results.
- [ ] **P133 — Handle guest serial errors** — Document breaks, invalid configuration and disconnected backend behavior. **Check:** malformed input does not crash QEMU.
- [ ] **P134 — Add console-based boot capture** — Capture serial transcripts as CI artifacts with repeatable log framing. **Check:** a missing success marker fails automatically.
- [ ] **P135 — Approve first authentic M1 peripheral** — Audit register coverage and external evidence. **Check:** G2 prints via T8103 Apple UART at its verified address.

## WS10 — Apple Interrupt Controller, AICv1 (P136–P150)

Depends on: WS09. Outcome: Apple-style IRQ/IPI routing without ARM GIC substitution.

- [ ] **P136 — Catalog AICv1 registers** — Map interrupt count, masks, targets, reasons and IPIs from Asahi/Linux. **Check:** each modeled offset links to source evidence.
- [ ] **P137 — Define pending/masked state** — Represent per-source pending bits, masking and level/edge information. **Check:** synthetic events update only intended state.
- [ ] **P138 — Implement AIC reset state** — Initialize mask, target and pending registers deterministically. **Check:** QTest reset comparisons pass across restarts.
- [ ] **P139 — Implement write-one-to-set masks** — Support SET register behavior without erasing unrelated bits. **Check:** sequential partial mask writes preserve previous bits.
- [ ] **P140 — Implement write-one-to-clear masks** — Support CLR register behavior and IRQ re-evaluation. **Check:** clearing one mask leaves others intact.
- [ ] **P141 — Model hardware IRQ input lines** — Connect a device-raised source to the AIC pending state. **Check:** raising and lowering a line changes observation correctly.
- [ ] **P142 — Implement per-core IRQ target masks** — Route sources only to configured CPU affinities. **Check:** non-targeted cores see no unexpected IRQ.
- [ ] **P143 — Implement IRQ reason read** — Encode pending IRQ identity and acknowledgment side effects as documented. **Check:** guest reads observe the expected selected source.
- [ ] **P144 — Implement IRQ acknowledgment sequence** — Honor hardware-source clear and AIC unmask ordering. **Check:** uncleared level IRQ reasserts as specified.
- [ ] **P145 — Implement software-generated interrupts** — Model SW_GEN_SET/CLR effects separately from device lines. **Check:** software IRQ can be raised and cleared without a device.
- [ ] **P146 — Implement per-core IPI send** — Support local/remote interprocessor interrupt targeting. **Check:** destination receives one pending IPI with correct reason.
- [ ] **P147 — Implement per-core IPI acknowledge** — Honor IPI ack and mask sequence. **Check:** re-enabled pending IPI behaves deterministically.
- [ ] **P148 — Connect AIC output to ARM CPUs** — Drive AIC's IRQ output through QEMU CPU interrupt APIs; keep timer FIQ wiring separate. **Check:** a guest IRQ handler receives the injected AIC interrupt without a timer FIQ.
- [ ] **P149 — Stress AIC mask/ack races** — Randomize interrupts, target changes and acknowledgments with fixed seeds. **Check:** no lost or phantom IRQ remains after quiescence.
- [ ] **P150 — Gate Apple interrupt correctness** — Run register, guest handler and silicon comparison suites. **Check:** documented AIC test scenarios pass before timer/SMP work.

## WS11 — ARM and Apple timer interfaces (P151–P165)

Depends on: WS10. Outcome: reproducible interrupt-driven timekeeping.

- [ ] **P151 — Inventory M1 counter sources** — Record architected CNT* registers and AIC mirrored timer reads. **Check:** mapping distinguishes CPU register and MMIO views.
- [ ] **P152 — Define virtual time epoch** — Relate QEMU virtual clock to architected counter without wall-clock dependence. **Check:** deterministic virtual time advances counter predictably.
- [ ] **P153 — Implement frequency register policy** — Provide a sourced/declared CNTFRQ value compatible with guest code. **Check:** frequency and counter-derived durations agree.
- [ ] **P154 — Test physical counter reads** — Validate CNTPCT monotonicity and access permissions. **Check:** sequential guest reads never regress.
- [ ] **P155 — Test virtual counter reads** — Validate CNTVCT and its configured offset. **Check:** expected counter delta matches injected virtual time.
- [ ] **P156 — Implement physical timer compare** — Assert timer condition at programmed CVAL/TVAL threshold. **Check:** early/late boundary tests pass.
- [ ] **P157 — Implement virtual timer compare** — Maintain separate virtual timer state per core. **Check:** each CPU receives only its own programmed timer event.
- [ ] **P158 — Respect enable and mask bits** — Gate each timer output using its architected control and sourced Apple mask behavior. **Check:** timer status and FIQ output obey their separate enable/mask semantics.
- [ ] **P159 — Connect the separate timer FIQ path** — Route M1 architectural timers to CPU FIQ rather than through AIC's MMIO IRQ source bank. **Check:** guest receives a timer FIQ while AIC external IRQ pending state remains unchanged.
- [ ] **P160 — Model counter-wrap arithmetic** — Handle compare operations around 64-bit counter boundaries. **Check:** synthetic wrap fixture gives correct event ordering.
- [ ] **P161 — Test timer reprogramming** — Update future and expired compare values during active time. **Check:** no stale event survives replacement.
- [ ] **P162 — Test timer cancellation on reset** — Reset counter-related guest state and pending timer events correctly. **Check:** reboot cannot receive an old timer interrupt.
- [ ] **P163 — Implement deterministic timer fixture** — Step virtual clock through specified deadlines with QTest. **Check:** observed timer FIQ timeline equals expected fixture.
- [ ] **P164 — Compare guest delays against M1 behavior** — Characterize software-visible timer state with reference traces. **Check:** functional sequencing matches within declared tolerances.
- [ ] **P165 — Gate timekeeping and interrupt integration** — Exercise timer FIQs alongside independently acknowledged AIC IRQs over thousands of timer/IRQ iterations. **Check:** stable guest tick count, correct interrupt classes and no unexpected pending sources.

## WS12 — Heterogeneous multicore bring-up and SMP (P166–P180)

Depends on: WS11. Outcome: correct four-P/four-E visible topology with functional IPIs.

- [ ] **P166 — Specify M1 eight-core topology** — Document four Firestorm and four Icestorm affinity IDs. **Check:** CPU enumeration matches the declared original M1 profile.
- [ ] **P167 — Instantiate all CPU objects** — Create configurable one/two/eight CPU profiles before full release. **Check:** machine introspection lists exact instances.
- [ ] **P168 — Define secondary CPU reset state** — Keep nonboot cores halted until the selected startup mechanism. **Check:** no secondary executes before release.
- [ ] **P169 — Research Apple CPU startup handshake** — Identify the required wake/release registers and firmware assumptions. **Check:** every implemented transition has a trace or driver reference.
- [ ] **P170 — Implement secondary CPU release** — Resume a selected core at a supplied startup address. **Check:** guest core acknowledges launch with correct MPIDR.
- [ ] **P171 — Validate two-core shared memory** — Run atomic handoff and data exchange between distinct virtual CPUs. **Check:** no stale or torn values appear.
- [ ] **P172 — Validate P-core/E-core feature isolation** — Probe identity and Apple sysregs concurrently on unlike cores. **Check:** one core cannot contaminate another's configuration.
- [ ] **P173 — Implement targeted IPI ring** — Cycle messages across a subset of cores. **Check:** exact expected message count reaches each target.
- [ ] **P174 — Implement broadcast IPI testing** — Send to multiple destinations and verify per-core acks. **Check:** no destination is missed or duplicated.
- [ ] **P175 — Test WFE/SEV synchronization** — Exercise predicate-based core parking, event-register consumption and SEV notifications. **Check:** no notification is lost and permitted early WFE completion cannot violate the shared-state protocol.
- [ ] **P176 — Stress multicore scheduling interleavings** — Replay seeded atomic/IRQ workloads under varied TCG scheduling. **Check:** externally visible state remains valid.
- [ ] **P177 — Handle independent per-core timers** — Verify timer registration and interrupt affinity on each core. **Check:** two timer schedules do not cross-trigger.
- [ ] **P178 — Test multicore reset and shutdown** — Quiesce all cores, IRQs and timers during machine reset. **Check:** no stale work executes after reset.
- [ ] **P179 — Add SMP coverage metrics** — Count tested core pairings, IPI patterns, barriers and race cases. **Check:** published matrix matches actual CI tests.
- [ ] **P180 — Gate eight-core Apple topology** — Run SMP smoke with four P and four E profile identities. **Check:** every core executes, acknowledges an IPI and exits cleanly.

## WS13 — Boot loader, memory handoff and Apple device trees (P181–P195)

Depends on: WS12. Outcome: reproducible guest entry without claiming SecureROM emulation.

- [ ] **P181 — Specify laboratory boot mode** — Document directly loaded guest images and non-authentic preboot assumptions. **Check:** boot logs explicitly identify lab versus fidelity mode.
- [ ] **P182 — Parse ELF load segments safely** — Load appropriate ARM64 program headers and reject malformed or overlapping segments. **Check:** adversarial ELF fixtures cannot escape guest RAM.
- [ ] **P183 — Add flat binary payload support** — Map raw firmware or kernel payloads to configured guest addresses. **Check:** entry PC and image bytes are verified before transfer.
- [ ] **P184 — Define boot parameter contract** — Specify initial registers, EL, PSTATE, MMU state and RAM reservations. **Check:** a guest startup probe confirms all declared values.
- [ ] **P185 — Implement Linux DTB handoff** — Place a valid FDT in guest RAM and pass its physical pointer in `x0`. **Check:** a tiny guest parses the supplied DTB root node.
- [ ] **P186 — Convert T8103 source bindings to FDT** — Use published SoC and J274 DTS as a starting point without fabricating active devices. **Check:** `dtc` validates the emitted binary tree.
- [ ] **P187 — Model disabled-device declarations** — Keep unimplemented controllers disabled or explicitly unsupported in laboratory DTs. **Check:** Linux does not probe nonexistent working devices.
- [ ] **P188 — Define dynamic memory descriptors** — Populate memory size, reserved carveouts and initramfs bounds consistently. **Check:** Linux sees no overlap between memory and boot payloads.
- [ ] **P189 — Study Apple Device Tree format** — Record ADT container structure, byte order and protected/private fields. **Check:** decoder tests accept synthetic sanitized ADT fixtures.
- [ ] **P190 — Create ADT sanitization tool plan** — Strip serials, keys and unique identities from captured firmware trees. **Check:** scanning sample redacted ADT finds no sensitive properties.
- [ ] **P191 — Document m1n1 handoff expectations** — Compare actual Asahi m1n1 startup state to the lab loader. **Check:** every discovered difference is tracked as a dependency.
- [ ] **P192 — Reproduce required early firmware state** — Initialize only measured clocks, cache-related settings or controllers needed by the first guest. **Check:** unexpected preboot dependency triggers a diagnostic.
- [ ] **P193 — Implement boot failure reasons** — Distinguish missing image, invalid FDT, illegal PC and unsupported entry state. **Check:** each negative fixture fails with a specific message.
- [ ] **P194 — Add repeatable kernel-image manifest** — Store hashes, Linux configuration and DT version without bundling proprietary blobs. **Check:** boot runner rejects a mismatched manifest.
- [ ] **P195 — Gate testable M1-targeted boot setup** — Verify image loader, FDT, memory layout and initial CPU state together. **Check:** pre-kernel probe executes on T8103 machine without `virt` shortcuts.

## WS14 — Apple-compatible Linux early boot (P196–P210)

Depends on: WS13. Outcome: a headless Linux shell using Apple MMIO and interrupts.

- [ ] **P196 — Choose reproducible Linux source baseline** — Pin a kernel tree with published T8103, UART and AIC support. **Check:** commit hash, config and patches are recorded.
- [ ] **P197 — Build minimal T8103 kernel configuration** — Enable required ARM64, serial, interrupt and timer drivers without unrelated hardware. **Check:** kernel Image and symbols build cleanly.
- [ ] **P198 — Build deterministic initramfs** — Create a minimal BusyBox-style init and test scripts using redistributable sources. **Check:** archive inventory and build hashes are recorded.
- [ ] **P199 — Validate FDT Linux compatibility strings** — Confirm J274/T8103 matching and disabled placeholders. **Check:** early kernel detects the intended machine family.
- [ ] **P200 — Establish early console route** — Configure kernel bootargs and supported Apple serial output. **Check:** first kernel messages appear through emulated UART.
- [ ] **P201 — Debug ARM64 exception startup** — Trace early page tables, EL handoff and fault handlers. **Check:** startup reaches kernel initialization without an unexplained trap.
- [ ] **P202 — Bring up Linux Apple AIC driver** — Make controller initialization observe required revision/mask state. **Check:** kernel creates interrupt domain without errors.
- [ ] **P203 — Bring up Linux clocksource** — Ensure counter frequency and timer device satisfy kernel expectations. **Check:** calibrated scheduling ticks advance after boot.
- [ ] **P204 — Resolve early boot CPU topology** — Advertise only supported cores and startup pathways. **Check:** selected core count matches Linux `/proc/cpuinfo` semantics.
- [ ] **P205 — Reach scheduler initialization** — Eliminate hangs in timers, softirq and first task scheduling. **Check:** kernel executes scheduled work for bounded test interval.
- [ ] **P206 — Mount RAM-backed root filesystem** — Pass and unpack initramfs without real ANS/NVMe dependency. **Check:** `/init` executes on the emulated system.
- [ ] **P207 — Reach interactive initramfs shell** — Wire input/output through Apple serial device and process console. **Check:** scripted guest command returns its expected response.
- [ ] **P208 — Remove temporary guest patches** — Replace narrow kernel accommodations with corrected emulator behavior where feasible. **Check:** each deleted patch has a passing hardware regression.
- [ ] **P209 — Automate cold Linux boot regression** — CI boots a pinned redistributable kernel/initramfs with bounded timeout. **Check:** cold boot reliably reaches a unique shell marker.
- [ ] **P210 — Certify G4 Linux-boot breakthrough** — Independently audit Apple CPU profile, T8103 board, UART, AIC and timer use. **Check:** interactive initramfs shell works without generic `virt` devices.

## WS15 — Apple DART IOMMU and DMA subsystem (P211–P225)

Depends on: WS14. Outcome: source-verified device DMA address translation.

- [ ] **P211 — Inventory T8103 DART instances** — Enumerate documented controller windows and device attachments. **Check:** address list agrees with selected Linux DTS revision.
- [ ] **P212 — Document DART register map** — Record enable, stream selection, translation tables and invalidation behavior. **Check:** each modeled register cites an upstream driver or trace.
- [ ] **P213 — Define DMA transaction abstraction** — Expose device read/write through IOVA-to-physical translation, not guest virtual memory. **Check:** invalid IOVA cannot access host memory.
- [ ] **P214 — Implement stream ID isolation** — Maintain translation state independently for each configured DMA stream. **Check:** one stream cannot read another's mapping.
- [ ] **P215 — Implement DART page-table walks** — Translate supported entries, sizes and access permissions. **Check:** known IOVA fixtures resolve to expected RAM offsets.
- [ ] **P216 — Implement translation enable/bypass modes** — Respect documented DART control settings and fallback behavior. **Check:** before/after enable tests access expected buffers.
- [ ] **P217 — Implement DART TLB invalidation** — Apply required invalidation and completion semantics after mapping updates without requiring stale entries to persist beforehand. **Check:** DMA issued after completed invalidation uses the updated translation and cannot observe an obsolete mapping.
- [ ] **P218 — Model DMA access faults** — Report invalid, forbidden and malformed transactions through documented status. **Check:** guest driver receives an attributable fault.
- [ ] **P219 — Validate scatter/gather DMA buffers** — Map multi-page buffers with noncontiguous host physical backing. **Check:** device reads and writes match expected bytes.
- [ ] **P220 — Wire DMA interrupt signaling** — Connect fault and completion events through AIC as appropriate. **Check:** guest handles an injected DMA completion IRQ.
- [ ] **P221 — Test translation permissions** — Verify read-only/write-only streams and protected regions. **Check:** unauthorized device write cannot modify RAM.
- [ ] **P222 — Fuzz invalid DART descriptors** — Exercise malformed addresses, overflow, alignment and cyclic tables. **Check:** emulator does not crash or access host memory out of bounds.
- [ ] **P223 — Build DART software-driver probe** — Initialize controller through a small guest driver. **Check:** target IOVA roundtrip succeeds from guest.
- [ ] **P224 — Compare DART traces with real M1** — Use sanitized reference activity for page tables, flushes and faults. **Check:** modeled state changes match selected known sequences.
- [ ] **P225 — Gate device-visible memory translation** — Exercise multiple streams and hot remaps under repeatable test load. **Check:** permissions, translation and fault suites all pass.

## WS16 — Apple ANS and NVMe-backed storage (P226–P240)

Depends on: WS14 and the DMA safety/test abstractions from WS15, not a DART attachment for ANS. Outcome: persistent disk reads/writes through Apple storage interfaces. T8103 ANS uses its embedded NVMMU and SART-protected RTKit/shared-memory paths; establish the minimal mailbox contract here before generalizing coprocessors in WS19.

- [ ] **P226 — Research ANS/NVMe register and mailbox paths** — Catalog ANS startup, tag-indexed submissions, embedded NVMMU and SART-protected RTKit buffers from the T8103 DTS and Apple NVMe driver. **Check:** each path has separate source-backed ownership and address-protection rules.
- [ ] **P227 — Define persistent block backend** — Use an isolated QEMU disk image behind a device model. **Check:** host backing file changes only from intended guest writes.
- [ ] **P228 — Implement ANS initialization states** — Model reset, firmware-ready and controller-ready transitions. **Check:** driver polling follows expected state sequence.
- [ ] **P229 — Implement storage mailbox and SART handshake** — Model the minimum ANS RTKit startup messages and SART allowed-memory ranges without distributing coprocessor firmware. **Check:** permitted shared-buffer transfers work, denied ranges fail and unsupported messages are diagnosed.
- [ ] **P230 — Expose NVMe identity/configuration** — Return consistent capabilities and controller identification. **Check:** Linux storage probe accepts the declared parameters.
- [ ] **P231 — Implement Apple tag-indexed submissions** — Use command-tag-indexed arrays and MMIO tag triggers with the documented admin/IO shared-tag constraints. **Check:** valid tags submit correctly and invalid or conflicting tags cannot corrupt queue memory.
- [ ] **P232 — Implement completion queues** — Produce completion records with proper status, head and phase behavior. **Check:** guest consumes completions in order.
- [ ] **P233 — Implement embedded ANS NVMMU authorization** — Validate command-tag TCB registration, DMA direction, length and PRP buffer mappings separately from SART-protected shared-memory paths. **Check:** registered reads reach the intended buffer and unregistered or inconsistent commands are rejected safely.
- [ ] **P234 — Implement read command data path** — Support sector-aligned reads and error signaling. **Check:** known disk patterns match guest readback.
- [ ] **P235 — Implement write command data path** — Persist changed blocks through the host backend. **Check:** a write survives emulator restart.
- [ ] **P236 — Handle flush and barriers** — Honor guest flush requests and backend durability semantics. **Check:** completed flush precedes observable persistent data.
- [ ] **P237 — Implement controller interrupt completion** — Route configured queue notification through AIC. **Check:** driver wakes and acknowledges completed I/O.
- [ ] **P238 — Test malformed storage commands** — Reject invalid LBAs, DMA sizes and queue pointers safely. **Check:** host filesystem stays intact after fuzz fixtures.
- [ ] **P239 — Integrate Linux filesystem mounting** — Add a root filesystem on emulated Apple storage path. **Check:** guest mounts and reads an ext4 filesystem.
- [ ] **P240 — Gate persistent Apple storage** — Cold boot, modify file, power off and relaunch with the same disk image. **Check:** guest reads the modified file through ANS with NVMMU command/data checks and the required SART-protected RTKit setup.

## WS17 — PCIe, USB and host-peripheral pathways (P241–P255)

Depends on: WS16. Outcome: narrow, traceable support for platform I/O expansion.

- [ ] **P241 — Inventory M1 PCIe root complexes** — Identify documented controllers, MMIO windows, lanes and interrupts. **Check:** register map is matched to J274 sources.
- [ ] **P242 — Model PCIe root control state** — Implement reset, link training and status bits used by first guest probe. **Check:** driver sees consistent link state.
- [ ] **P243 — Implement PCIe configuration access** — Serve supported device capability/configuration fields. **Check:** guest enumeration returns expected vendor/class values.
- [ ] **P244 — Implement PCIe address translation windows** — Map config, MMIO and DMA apertures safely. **Check:** BAR accesses reach the selected emulated device only.
- [ ] **P245 — Implement MSI and interrupt mapping** — Connect supported PCIe interrupts through Apple interrupt domains. **Check:** a test device issues an observable interrupt.
- [ ] **P246 — Integrate PCIe DMA with DART** — Apply device-associated translation/permission rules. **Check:** blocked PCIe DMA cannot bypass stream isolation.
- [ ] **P247 — Research Apple USB controller topology** — Locate hardware IP blocks, power and phy prerequisites. **Check:** only verified J274 controllers appear in machine inventory.
- [ ] **P248 — Model minimal USB host controller state** — Implement or reuse compatible controller behavior with correct Apple glue. **Check:** driver completes controller reset and probe.
- [ ] **P249 — Implement USB port change signals** — Present connect/disconnect events to guest. **Check:** guest detects a synthetic attachment change.
- [ ] **P250 — Validate USB transfers through mapped buffers** — Exercise supported control/bulk transactions and DMA. **Check:** bounded test transfer returns expected bytes.
- [ ] **P251 — Add device hotplug safety** — Make detach during pending I/O fail gracefully. **Check:** no host crash or stale DMA follows removal.
- [ ] **P252 — Distinguish physical and virtual peripherals** — Identify any lab-only shortcuts in device enumeration. **Check:** strict mode refuses unadvertised generic devices.
- [ ] **P253 — Add PCIe/USB fault cases** — Inject link loss, bad BAR and failed transfer completion. **Check:** guest receives expected recoverable errors.
- [ ] **P254 — Compare selected initialization traces** — Check register write/ack ordering against Linux or physical silicon. **Check:** every supported probe event is explainable.
- [ ] **P255 — Gate constrained expansion I/O** — Verify documented PCIe enumeration and one USB transaction path. **Check:** hardware coverage lists supported and missing subfeatures.

## WS18 — Power manager, GPIO, watchdog and system reset (P256–P270)

Depends on: WS17. Outcome: stable system controls needed by peripheral drivers.

- [ ] **P256 — Catalog T8103 PMGR clock domains** — Identify documented control registers and dependencies. **Check:** no fabricated domain is marked tested.
- [ ] **P257 — Implement power-domain state machine** — Track enabled/disabled domains and reset dependencies. **Check:** domain enable permits intended controller access.
- [ ] **P258 — Handle powered-down MMIO accesses** — Define and test behavior when a controller's domain is off. **Check:** unsupported powered-down operation is diagnosable.
- [ ] **P259 — Implement clock gate changes** — Model firmware/driver-visible controls needed for current devices. **Check:** switching a supported gate changes documented state.
- [ ] **P260 — Catalog GPIO controller capabilities** — Record pin counts, direction, muxing and interrupt source groups. **Check:** pin bank geometry matches T8103 evidence.
- [ ] **P261 — Implement GPIO direction/value bits** — Support input/output operations for a small verified subset. **Check:** toggling guest output changes modeled level.
- [ ] **P262 — Implement GPIO edge detection** — Raise an event on selected pin transitions. **Check:** rising and falling tests trigger only configured edges.
- [ ] **P263 — Model GPIO debounce if required** — Specify timing behavior only if supported by evidence. **Check:** either verified debounce works or capability remains unadvertised.
- [ ] **P264 — Define watchdog register state** — Capture reset/enable/timeout/clear controls from the Linux driver. **Check:** reset readings and write effects match specification.
- [ ] **P265 — Implement watchdog timeout event** — Schedule expiry in QEMU virtual time. **Check:** guest neglecting service triggers expected watchdog action.
- [ ] **P266 — Implement watchdog pet/rearm** — Cancel or extend a pending deadline using documented access. **Check:** repeated pets prevent premature timeout.
- [ ] **P267 — Integrate soft system reset** — Quiesce CPU, DMA, UART and AIC while preserving configured storage. **Check:** reset returns devices to documented initial state.
- [ ] **P268 — Test PMGR and IRQ interactions** — Disable/re-enable a peripheral domain with pending interrupt. **Check:** interrupt state stays consistent with device lifecycle.
- [ ] **P269 — Stress power/reset boundary conditions** — Randomize enable, disable and watchdog events with fixed seeds. **Check:** no stuck IRQ or orphaned timer remains.
- [ ] **P270 — Gate basic platform control** — Complete documented PMGR/GPIO/WDT tests under kernel activity. **Check:** integrated system reset and timed watchdog scenario pass.

## WS19 — SMC, coprocessor mailboxes and RTKit contracts (P271–P285)

Depends on: WS18. Outcome: bounded, documented interfaces for auxiliary controllers.

- [ ] **P271 — Inventory Apple mailbox endpoints** — Identify known T8103 coprocessor command and notification channels. **Check:** each reported endpoint has a source and ownership model.
- [ ] **P272 — Define shared mailbox abstraction** — Represent endpoint queues, interrupts and message buffers independently of firmware. **Check:** synthetic producer/consumer roundtrip preserves messages.
- [ ] **P273 — Implement mailbox doorbell registers** — Raise and acknowledge notifications with documented state changes. **Check:** guest receives the intended doorbell event exactly once.
- [ ] **P274 — Handle mailbox queue backpressure** — Define behavior for full, empty and cancelled queues. **Check:** overflow cannot corrupt unrelated guest RAM.
- [ ] **P275 — Research Apple SMC protocol** — Extract relevant transport and key-value command behavior from public Linux sources. **Check:** protocol table separates observed from unknown commands.
- [ ] **P276 — Model minimal SMC identity response** — Return a small consistent set of non-sensitive documented values. **Check:** guest enumerates SMC without fabricated private data.
- [ ] **P277 — Model SMC notification path** — Provide status changes and interrupts for supported keys/events. **Check:** guest observes one state transition per injected event.
- [ ] **P278 — Implement SMC read/write validation** — Reject unsupported keys, invalid lengths and unexpected messages. **Check:** malformed request produces an appropriate error.
- [ ] **P279 — Document RTKit framing and negotiation** — Record public message header, endpoint and version expectations. **Check:** synthetic RTKit frame parser rejects corrupt headers.
- [ ] **P280 — Implement bounded RTKit handshake** — Support only a verified subset used by a selected peripheral. **Check:** guest handshake reaches expected terminal state.
- [ ] **P281 — Define coprocessor firmware boundary** — Explicitly separate emulated responses from execution of proprietary firmware. **Check:** no proprietary blob is required by initial coprocessor tests.
- [ ] **P282 — Test mailbox concurrency** — Interleave two independent endpoints and reset events. **Check:** no cross-channel reply or stale completion appears.
- [ ] **P283 — Add transport failure injection** — Simulate timeout, short packet and unsupported protocol versions. **Check:** guest detects failure without freezing emulator.
- [ ] **P284 — Compare sanitized coprocessor traces** — Validate a narrow supported command sequence against reference drivers. **Check:** request/response order and state changes match.
- [ ] **P285 — Gate supported auxiliary interfaces** — Publish an explicit SMC/mailbox/RTKit coverage matrix. **Check:** listed working commands have repeatable guest tests.

## WS20 — Apple GPU, display and accelerators: exploratory track (P286–P300)

Depends on: WS14 and selected WS15/WS19 models. Outcome: research prototypes only, not required for v0.1.

- [ ] **P286 — Define AGX fidelity levels** — Distinguish command submission, firmware protocol, shader execution and actual rendering. **Check:** public goals use precise compatibility terminology. **Scope:** exploratory; not required for v0.1.
- [ ] **P287 — Study Asahi/Mesa GPU source** — Build a source-linked inventory of publicly known command structures. **Check:** no undocumented packet is declared implemented. **Scope:** exploratory; not required for v0.1.
- [ ] **P288 — Research GPU virtual memory** — Characterize device-side address translation and synchronization. **Check:** a synthetic mapping test has explicit protection outcomes. **Scope:** exploratory; not required for v0.1.
- [ ] **P289 — Define GPU work submission model** — Specify queues, command buffers, fences and interrupts. **Check:** a deterministic test can submit and complete a no-op job. **Scope:** exploratory; not required for v0.1.
- [ ] **P290 — Implement skeletal AGX MMIO device** — Expose only verified discovery and status registers. **Check:** device reports honest partial implementation state. **Scope:** exploratory; not required for v0.1.
- [ ] **P291 — Research shader ISA behavior** — Inventory publicly reconstructed GPU instruction forms and gaps. **Check:** an instruction corpus identifies unsupported encodings. **Scope:** exploratory; not required for v0.1.
- [ ] **P292 — Prototype minimal shader decoding** — Parse a narrowly defined instruction subset into an intermediate representation. **Check:** decode/re-encode roundtrip preserves the supported bits. **Scope:** exploratory; not required for v0.1.
- [ ] **P293 — Evaluate software shader interpreter** — Execute a tiny arithmetic kernel without claiming general AGX support. **Check:** reference output values match for selected test vectors. **Scope:** exploratory; not required for v0.1.
- [ ] **P294 — Evaluate host GPU backend translation** — Compare Vulkan/other backend requirements against observable AGX behavior. **Check:** a written compatibility gap analysis supports the decision. **Scope:** exploratory; not required for v0.1.
- [ ] **P295 — Research display-controller protocols** — Map DCP/mailbox interactions, framebuffer and scanout ownership. **Check:** a documented minimal handshake can be isolated. **Scope:** exploratory; not required for v0.1.
- [ ] **P296 — Prototype virtual framebuffer path** — Expose a test framebuffer independent of full AGX shader support. **Check:** known pixel pattern is captured unambiguously. **Scope:** exploratory; not required for v0.1.
- [ ] **P297 — Model GPU fence and event completion** — Verify synchronization ordering for a tiny synthetic workload. **Check:** fence transitions occur in expected order. **Scope:** exploratory; not required for v0.1.
- [ ] **P298 — Establish graphics differential corpus** — Store only original shaders and expected synthetic outputs. **Check:** harness reports per-operation pass/fail independently. **Scope:** exploratory; not required for v0.1.
- [ ] **P299 — Assess media and neural engine boundaries** — Inventory publicly documented drivers versus unknown proprietary accelerators. **Check:** limitations are classified by required research effort. **Scope:** exploratory; not required for v0.1.
- [ ] **P300 — Publish a candid graphics feasibility report** — Summarize proven commands, untested interfaces and estimated missing work. **Check:** review finds no unsupported claim of functional AGX/macOS GUI. **Scope:** exploratory; not required for v0.1.

## WS21 — macOS and secure-boot compatibility: research only (P301–P315)

Depends on: WS14 and legal/source review; not required by v0.1. Outcome: feasibility evidence, no false macOS boot claim.

- [ ] **P301 — Review Apple macOS licensing** — Document host, virtualization and redistribution restrictions for contemplated tests. **Check:** proposed experiments have an explicit compliance review. **Scope:** exploratory; not required for v0.1.
- [ ] **P302 — Inventory Apple secure boot stages** — Describe Boot ROM, LLB/iBoot, LocalPolicy, SEP and firmware handoffs from primary sources. **Check:** dependency graph cites official documentation. **Scope:** exploratory; not required for v0.1.
- [ ] **P303 — Delineate emulator and firmware responsibility** — Define which boot stages would be modeled versus externally provided, lawfully obtained inputs. **Check:** architecture design never implies possession of Apple keys. **Scope:** exploratory; not required for v0.1.
- [ ] **P304 — Study kernelcache container structure** — Review publicly described Mach-O/IMG4 formats without distributing payloads. **Check:** documentation identifies exact research scope and legal constraints. **Scope:** exploratory; not required for v0.1.
- [ ] **P305 — Inventory XNU early-boot interfaces** — List hardware and boot arguments observed in documented XNU development paths. **Check:** missing peripherals have explicit issue records. **Scope:** exploratory; not required for v0.1.
- [ ] **P306 — Compare Linux versus XNU entry state** — Record differences in ADT, memory carveouts, privilege and system registers. **Check:** comparison names concrete incompatible assumptions. **Scope:** exploratory; not required for v0.1.
- [ ] **P307 — Analyze boot-policy trust dependencies** — Identify what cannot be reproduced merely by loading a kernel binary. **Check:** feasibility report separates cryptographic from functional requirements. **Scope:** exploratory; not required for v0.1.
- [ ] **P308 — Compare physical M1 and VMApple model** — Explain why QEMU `vmapple` guest hardware differs from a real T8103. **Check:** no design doc treats VMApple as an M1 SoC model. **Scope:** exploratory; not required for v0.1.
- [ ] **P309 — Model non-secret ADT fixture** — Create an original minimal ADT-like test tree where permitted. **Check:** fixture contains no machine identity or cryptographic material. **Scope:** exploratory; not required for v0.1.
- [ ] **P310 — Assess XNU CPU-specific register usage** — Classify implementation-defined registers required by early code. **Check:** every reported requirement is backed by disassembly or public source evidence. **Scope:** exploratory; not required for v0.1.
- [ ] **P311 — Assess SEP dependency surface** — Distinguish optional runtime services from security-policy requirements. **Check:** unsupported SEP protocols are not silently mocked as valid security claims. **Scope:** exploratory; not required for v0.1.
- [ ] **P312 — Assess display and GUI blockers** — Map AGX, DCP, WindowServer and framework expectations at a high level. **Check:** GUI scope is not confused with bare kernel execution. **Scope:** exploratory; not required for v0.1.
- [ ] **P313 — Form a lawful kernel research harness** — Specify tests restricted to appropriate Apple hosts or redistributable original payloads. **Check:** inputs are tracked with license/provenance metadata. **Scope:** exploratory; not required for v0.1.
- [ ] **P314 — Publish macOS feasibility risk assessment** — Quantify confidence and open unknowns without giving an unsupported completion date. **Check:** independent review can reproduce all factual claims. **Scope:** exploratory; not required for v0.1.
- [ ] **P315 — Decide whether to advance macOS exploration** — Require evidence that licensing and technical blockers are sufficiently understood. **Check:** documented go/no-go decision does not affect v0.1 release. **Scope:** exploratory; not required for v0.1.

## WS22 — Silicon differential validation and research tooling (P316–P330)

Depends on: stable WS09–WS19 device models. Outcome: evidence-based behavioral fidelity.

- [ ] **P316 — Define normalized hardware trace schema** — Include timestamp class, CPU, address, width, operation, value, and event type. **Check:** validator rejects malformed event records.
- [ ] **P317 — Build safe trace redaction pipeline** — Strip identifying ADT properties, keys and user-specific system values. **Check:** seeded synthetic secrets are removed from output.
- [ ] **P318 — Add m1n1 reference-trace ingestion** — Parse supported exported MMIO event syntax without executing untrusted data. **Check:** a sanitized fixture imports deterministically.
- [ ] **P319 — Add QEMU MMIO trace export** — Emit normalized device events with guest PC and logical time. **Check:** a UART write appears exactly once in exported trace.
- [ ] **P320 — Implement trace alignment algorithm** — Pair logically equivalent transactions despite unrelated event interleaving. **Check:** a shuffled fixture finds correct matching events.
- [ ] **P321 — Compare register value semantics** — Detect mismatched readback, masks, side effects and reset states. **Check:** injected bad register result generates a concise diff.
- [ ] **P322 — Compare interrupt causality** — Track source assertion, AIC delivery, handler acknowledgment and deassertion. **Check:** a missing or reordered IRQ step is detected.
- [ ] **P323 — Support nondeterministic value masks** — Define allowed variation for truly variable counters or unrelated metadata. **Check:** masks cannot hide unapproved differences.
- [ ] **P324 — Create UART trace corpus** — Curate TX/RX/status experiments with original inputs and sanitized M1 outcomes. **Check:** model matches all approved UART traces.
- [ ] **P325 — Create AIC trace corpus** — Curate mask, target, IRQ and IPI transitions from reference evidence. **Check:** state machine passes golden event sequences.
- [ ] **P326 — Create timer trace corpus** — Capture enable, compare, clear and rearm behavior at logical deadlines. **Check:** timed model passes causal events and documented tolerances.
- [ ] **P327 — Create DART/storage trace corpus** — Record non-sensitive stream setup and I/O transaction transitions. **Check:** reference fixtures contain no disk contents or identities.
- [ ] **P328 — Add version-aware fixtures** — Attach SoC, firmware, macOS/Linux, Asahi and QEMU revisions to each trace. **Check:** harness warns when comparing incompatible versions.
- [ ] **P329 — Produce coverage/confidence report** — Summarize which device transitions are silicon-observed, source-derived or only synthetic. **Check:** report totals match fixture inventory.
- [ ] **P330 — Gate trace-backed conformance** — Rerun all mandatory reference traces and track unexplained deltas. **Check:** no high-severity mismatch is ignored in a release claim.

## WS23 — Performance, determinism, observability and debugging (P331–P345)

Depends on: WS14 and WS22. Outcome: usable iterative research environment without false cycle accuracy.

- [ ] **P331 — Establish baseline boot timing** — Measure wall time and guest instruction count separately. **Check:** benchmark output identifies host and QEMU versions.
- [ ] **P332 — Add deterministic virtual-clock mode** — Make timer/IRQ tests repeatable independent of host scheduling. **Check:** repeated seeded runs produce identical event sequences.
- [ ] **P333 — Profile QEMU execution hotspots** — Attribute time to TCG, MMIO callbacks and device timer work. **Check:** profile report names top measurable bottlenecks.
- [ ] **P334 — Optimize MMIO dispatch lookups** — Reduce hot path overhead without bypassing access checks. **Check:** performance gain preserves all register tests.
- [ ] **P335 — Optimize serial buffering** — Prevent per-byte host I/O from dominating boot tests while maintaining order. **Check:** high-throughput test shows no dropped bytes.
- [ ] **P336 — Add device event counters** — Count MMIO reads/writes, IRQs, timeouts and unknown accesses. **Check:** counters match a controlled workload.
- [ ] **P337 — Add boot-stage breadcrumbs** — Log tagged milestones across machine creation, kernel entry, early console and init. **Check:** failed boot identifies last reached stage.
- [ ] **P338 — Create guest panic triage helper** — Parse ESR/FAR/ELR and nearest symbol from known guest debug information. **Check:** artificial panic yields correct offending instruction.
- [ ] **P339 — Add snapshot/replay evaluation** — Test whether supported device state can be saved and restored coherently. **Check:** restored test continues with same guest-visible state.
- [ ] **P340 — Limit memory usage in lab profile** — Enforce configurable RAM size and bounded snapshot buffering. **Check:** host memory stays within a documented test budget.
- [ ] **P341 — Stress long-running idle operation** — Run timer-driven headless guest over extended simulated time. **Check:** no unexpected interrupt growth or unbounded allocations.
- [ ] **P342 — Stress repeated cold boots** — Restart the same guest hundreds of times with fixed inputs. **Check:** pass/fail outcome and console marker remain stable.
- [ ] **P343 — Add regression bisect playbook** — Define how to reproduce a boot or MMIO regression from a commit. **Check:** one known injected failure is localized.
- [ ] **P344 — Report performance honestly** — State TCG slowdowns and lack of precise M1 cycle/timing fidelity. **Check:** benchmarks never claim native M1 throughput.
- [ ] **P345 — Gate engineering stability** — Combine repeated boots, memory limits, deterministic tests and diagnostics. **Check:** published stability suite meets documented thresholds.

## WS24 — Security, documentation, packaging and sustainable releases (P346–P360)

Depends on: core gates G0–G4 and evidence work. Outcome: trustworthy, maintainable emulator releases.

- [ ] **P346 — Threat-model untrusted guest input** — Inventory ELF loader, device descriptor, DMA, mailbox and trace parser attack surfaces. **Check:** written threat model assigns mitigations to each parser.
- [ ] **P347 — Fuzz critical binary parsers** — Exercise guest ELF, DTB, device queues and trace inputs with sanitizer builds. **Check:** known crashing fixtures are regression-tested.
- [ ] **P348 — Add memory sanitizer jobs** — Run ASan/UBSan or equivalent on project-specific C code in relevant builds. **Check:** targeted corpus completes without sanitizer errors.
- [ ] **P349 — Check dependency licenses** — Verify QEMU GPL, upstream drivers, firmware restrictions and third-party assets. **Check:** legal notices and SBOM match shipped contents.
- [ ] **P350 — Document binary provenance** — Record source, checksums and build options for redistributable kernel/guest test images. **Check:** fresh build produces a verifiable provenance manifest.
- [ ] **P351 — Build release artifact layout** — Package emulator binaries, tests, docs and sample redistributable guests. **Check:** no proprietary image or secret enters archive.
- [ ] **P352 — Document supported machines** — State exactly which T8103 variants and peripheral subsets are implemented. **Check:** compatibility file derives status from passing tests.
- [ ] **P353 — Write troubleshooting guide** — Cover failure modes including wrong QEMU version, missing toolchain, bad DTB and absent UART output. **Check:** each common failure has a reproducible diagnostic.
- [ ] **P354 — Publish hardware coverage table** — Track register counts, tested transitions and source confidence by device. **Check:** no incomplete device receives a complete badge.
- [ ] **P355 — Publish reproducible demo command** — Start the Apple T8103 machine with a redistributable guest in one documented command. **Check:** clean install reaches declared milestone.
- [ ] **P356 — Add release changelog discipline** — Link code changes to roadmap phases, tests and known gaps. **Check:** every significant device change appears in release notes.
- [ ] **P357 — Introduce compatibility versioning** — Version machine model and guest-visible contracts as capabilities evolve. **Check:** incompatible changes are detected/documented.
- [ ] **P358 — Audit continuous integration gates** — Make roadmap, hardware validation, unit, qtest and integration checks required. **Check:** intentionally failing fixture blocks release.
- [ ] **P359 — Prepare first research release** — Create a tagged candidate with evidence bundle and limitations, once G4 is real. **Check:** independent tester reproduces the serial Linux shell.
- [ ] **P360 — Conduct project readiness review** — Reassess scope, security, source citations and test credibility. **Check:** external reviewer can distinguish implemented from merely planned phases.

## Formal release acceptance phases (P361–P365)

Each gate below declares its independent fidelity level(s) from the [P002 fidelity contract](docs/ARCHITECTURE.md#p002-fidelity-contract). These labels describe the scope of required evidence, not a passed result.

The [P004 scope contract](docs/EXPLORATORY_SCOPE.md) excludes cycle accuracy, GPU graphics and unmodified macOS from every named gate. These last gates do not grant automatic completion of exploratory WS20/WS21. They verify that the **headless M1 research release** is honest, reproducible and safe.

- [ ] **P361 — Independently reproduce CPU and board gates** — Execute G1/G2 on a fresh host with source-linked T8103 map. **Check:** Apple machine runs its own UART ELF without generic `virt` substitution. **Fidelity:** `isa`, `apple-cpu`, `peripheral`.
- [ ] **P362 — Independently reproduce interrupts and SMP** — Run G3 with timers and two-core IPI protocol in isolation. **Check:** no lost, duplicate or stuck interrupt remains. **Fidelity:** `isa`, `apple-cpu`, `peripheral`.
- [ ] **P363 — Independently reproduce Linux breakthrough** — Boot exact published T8103 kernel/image artifacts from cold reset. **Check:** G4 reaches interactive initramfs shell over Apple UART. **Fidelity:** `machine-linux`.
- [ ] **P364 — Audit fidelity, licensing and trace evidence** — Recheck hardware provenance, sanitizer results, limitations, GPL notices and excluded Apple blobs. **Check:** release contains no secret data or unsupported compatibility claims. **Fidelity:** `evidence-audit`.
- [ ] **P365 — Publish v0.1 final acceptance report** — Release a complete reproducibility record, passed gates, open defects and future research queue. **Check:** an independent reviewer can verify the published evidence end to end. **Fidelity:** `evidence-audit`.
