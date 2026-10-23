# P004 exploratory non-goals

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are exploratory, unimplemented and not required.

The required v0.1 workload is the **headless J274/T8103 Linux initramfs shell through Apple UART/AIC**, with the CPU, timer, interrupt and boot evidence defined by [P002](ARCHITECTURE.md#p002-fidelity-contract) and [P003](LINUX_BOOT_MILESTONE.md). P004 adds an enforceable boundary around three independent research areas. It neither implements them nor certifies a runtime gate.

These exclusions are release-scope decisions, not statements that the research is impossible. Functional correctness still includes instruction results, exceptions, permitted memory ordering, device side effects, interrupt delivery and observable timer behavior. A missing required UART, AIC or timer behavior cannot be excused as an exploratory non-goal.

[scope.json](scope.json) is the machine-readable policy. The following three capability records and all 12 gate exclusions must match it. Both implementation and v0.1 requirement flags are strictly false. No metadata field is an emulator result.

## Published scope contract

### cycle-accuracy — Cycle accuracy

**Required for v0.1:** no. **Implemented:** no.

**Boundary:** Firestorm/Icestorm pipeline, cache, speculation and per-instruction silicon timing are exploratory and unimplemented. Functional architectural results, observable timer behavior and causal event ordering remain mandatory.

**Allowed research:** P102 measures executed instructions and P344 reports host performance. Neither result establishes M1 cycle timing or native throughput; these functional/accounting tasks are not made optional by this exclusion.

**Evidence before changing this policy:** Any future timing claim needs a separately reviewed model, a declared core/workload subset, independently measured reference traces, reproducible experiments and explicit error bounds. Deterministic virtual time alone is insufficient.

**Related roadmap phases:** `P102`, `P344`.

**Sources:** [qemu-icount](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/devel/tcg-icount.rst).

### gpu-graphics — GPU graphics

**Required for v0.1:** no. **Implemented:** no.

**Boundary:** AGX graphics, GPU acceleration and macOS GUI operation are exploratory and unimplemented. The required Linux witness is headless and uses the Apple serial console.

**Allowed research:** WS20 permits source study, discovery/MMIO prototypes, no-op submissions, shader subsets, fence tests and an independent framebuffer. These bounded experiments do not establish functional AGX rendering or a macOS GUI.

**Evidence before changing this policy:** Any future graphics claim needs an explicit command/firmware/shader/display subset, original workloads, independent expected images or compute results, synchronization and fault tests, provenance and recorded unsupported operations.

**Related roadmap phases:** `P286`, `P287`, `P288`, `P289`, `P290`, `P291`, `P292`, `P293`, `P294`, `P295`, `P296`, `P297`, `P298`, `P299`, `P300`.

**Sources:** [asahi-agx](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/hw/soc/agx.md).

### unmodified-macos — Unmodified macOS

**Required for v0.1:** no. **Implemented:** no.

**Boundary:** Unmodified macOS boot, Apple physical boot-chain compatibility, SEP services, GUI and general applications are exploratory and unimplemented. G4 direct-loaded Linux establishes none of these results.

**Allowed research:** WS21 permits feasibility study and separately justified kernel experiments. Kernel entry, completed boot, user space, GUI and applications require separate witnesses; VMApple represents a different platform from J274/T8103.

**Evidence before changing this policy:** Any future macOS claim needs reviewed input provenance and applicable test permissions, exact host/model/guest artifacts, a reproducible workload and documented boot, security and device assumptions. The P315 go/no-go decision cannot block v0.1.

**Related roadmap phases:** `P301`, `P302`, `P303`, `P304`, `P305`, `P306`, `P307`, `P308`, `P309`, `P310`, `P311`, `P312`, `P313`, `P314`, `P315`.

**Sources:** [apple-boot](https://support.apple.com/en-ca/guide/security/secac71d5623/web), [qemu-vmapple](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/docs/system/arm/vmapple.rst).

### Gate exclusion inventory

| Gate | Excluded capabilities; no implementation credit |
|---|---|
| G0 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G1 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G2 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G3 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G4 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G5 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| G6 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| P361 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| P362 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| P363 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| P364 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |
| P365 | `cycle-accuracy`, `gpu-graphics`, `unmodified-macos` |

## Meaning of limited experiments

| Observation | What it can establish | What remains outside the result |
|---|---|---|
| Executed instruction count or repeatable virtual time | The declared accounting or repeatability property | Firestorm/Icestorm pipeline timing and native throughput |
| Correct timer FIQ delivery | The specified functional timer/interrupt behavior | Cycle-accurate silicon performance |
| AGX discovery registers or a no-op queue result | The named register or command path | General shader execution and rendered graphics |
| A shader decoder or one arithmetic kernel | The tested encoding or computation subset | General AGX graphics compatibility |
| P296 framebuffer pattern | The declared independent framebuffer output | AGX shader support, DCP fidelity or macOS GUI |
| XNU kernel entry | That exact entry-state experiment, if independently witnessed | Completed macOS boot, user space, GUI and applications |
| QEMU VMApple guest execution | A result on the separate virtual platform | Physical J274/T8103 hardware compatibility |
| G4 Linux serial shell | The versioned laboratory Linux witness | Apple's physical boot/security chain and unmodified macOS |

The distinctions above follow the [reviewed primary sources](REFERENCES.md#p004-exploratory-scope-evidence). QEMU instruction counting explicitly omits real instruction latency. Asahi's kernel-facing AGX notes describe an ASC/firmware, memory, queue and event interface while leaving shader and other userspace details outside their scope. Apple describes a physical-machine boot and security chain that the laboratory direct loader does not exercise. The scope choices and the evidence demanded here are this project's requirements; the sources do not certify an emulator implementation.

## Roadmap and release treatment

- **P102 and P344 remain accounting/performance tasks.** Their relation to timing research does not make their existing functional checks optional or establish cycle fidelity. P165's repeated timer/IRQ iterations concern functional progress.
- **P286–P300 (WS20) remain optional graphics research.** Each phase has an explicit nonrequired annotation. A proven narrow phase can be checked off without changing the full graphics exclusion.
- **P301–P315 (WS21) remain optional macOS research.** The P315 decision cannot delay or redefine the headless release. Study of a boot protocol is distinct from exercising it.
- **G0–G6 and P361–P365 exclude all three capabilities.** They retain their P002 classifications and P003 obligations. Neither an evidence-audit gate nor P365 publication automatically completes the exploratory workstreams.

To change a boundary, first record a specific workload and observable result, independent evidence, the unsupported remainder, relevant provenance and a reviewed scope decision. Then revise this policy, its published contract, applicable gate definitions and regression cases together. An arbitrary checkbox, upstream driver, screenshot, timing number or renamed machine cannot substitute for that evidence. This is a future review requirement, not a present capability or a promised delivery date.

## Mechanical checks and their limits

Run from the repository root:

```sh
python3 tools/validate_scope.py
python3 -m unittest discover -s tests -p 'test_scope.py' -v
```

The validator uses only the Python standard library and supports `--root PATH` and invocation from another working directory. It checks the closed schema, exact exclusions, related phases and reviewed source URLs; the visible published contract and five scope declarations; the optional annotations on all 30 research phases; and the unchanged P002/P003 contract checks. It scans root Markdown and all Markdown below `docs/`, including newly added release notes, plus each structured gate's test and scope text. Explicit statements making a named gate depend on WS20/WS21 or their phases are also rejected.

A targeted claims lint rejects explicit affirmative shipping, implementation and requirement statements about the excluded capabilities. It handles ordinary Markdown formatting, selected Unicode hyphens and locally negated clauses. Code examples and HTML comments are not visible scope declarations. Source descriptions and conditional future research need to remain clearly attributable.

This is **bounded consistency checking**, not proof of the truth of arbitrary English, source authenticity, an inferred dependency graph, private branches or documents outside the checked repository paths. Human review of all milestones remains part of completion and release review. P014's broader compatibility-language audit remains future work. A passing P004 check establishes no hardware, graphics, macOS or timing compatibility and does not award G4.
