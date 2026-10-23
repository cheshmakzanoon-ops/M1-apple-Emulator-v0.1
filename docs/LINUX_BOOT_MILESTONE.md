# P003 — First Linux boot milestone

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

> v0.1 scope: cycle accuracy, GPU graphics and unmodified macOS are exploratory, unimplemented and not required.

## Status and acceptance boundary

**G4 is the v0.1 functional success criterion: a T8103-targeted Linux kernel reaches an interactive BusyBox initramfs shell through Apple UART and Apple AIC.** It uses the custom `apple-m1-lab` machine, QEMU TCG and explicitly labelled laboratory direct loading. The architectural timer retains its separate FIQ route.

This document freezes the test, its prerequisites and the evidence needed to assess that result. **G4 has not been run or passed.** The T8103 machine, Apple CPU/device implementations, Linux configuration, final DTB, initramfs and live boot runner do not yet exist here. P196–P209 implement the Linux integration; P210 certifies G4; P363 independently reproduces it on a fresh host. The probe and offline checker delivered by P003 are test tooling, with synthetic regression evidence only.

The contract is [boot-milestone.json](boot-milestone.json), checked by `python3 tools/validate_boot_milestone.py`. The tables below are a complete rendering of its policy fields. They contain requirements, not recorded runtime outcomes. This specification refines the existing [P002 fidelity contract](ARCHITECTURE.md#p002-fidelity-contract) without changing G4's observable test or granting a different fidelity level.

## Frozen contract

<!-- P003-CONTRACT-BEGIN -->
### Frozen profile

| Field | Requirement |
|---|---|
| phase | P003 |
| gate | G4 |
| fidelity | machine-linux |
| success_criterion | T8103-targeted Linux reaches BusyBox shell via Apple UART/AIC |
| target.soc | T8103 |
| target.board | J274 |
| target.machine | apple-m1-lab |
| target.accelerator | tcg |
| target.boot_mode | laboratory-direct |
| target.architecture | aarch64 |
| target.linux_compatible | apple,j274, apple,t8103, apple,arm-platform |
| target.console | ttySAC0 |
| target.serial_driver | samsung-uart |
| target.root_filesystem | BusyBox initramfs |
| witness.profile | linux-v6.12-observables-v1 |
| witness.guest_script | experiments/linux-boot-witness/probe.sh |
| witness.checker | tools/check_g4_transcript.py |
| witness.guest_script_path | /g4-probe.sh |
| witness.binding_helper | experiments/linux-boot-witness/serial-binding.sh |
| witness.binding_helper_path | /g4-serial-binding.sh |
| witness.cold_boots | 3 |
| witness.online_cpus | 1 |
| witness.boot_timeout_seconds | 300 |
| witness.interaction_timeout_seconds | 30 |
| witness.guest_sleep_seconds | 1 |
| witness.nonce_hex_characters | 32 |
| witness.operand_min | 1 |
| witness.operand_max | 999999 |
| witness.shell_followup | product-after-probe |
| witness.uart_irq_chip | AIC |
| witness.uart_irq_action | 235200000.serial |
| witness.timer_irq_chip | AIC-FIQ |
| witness.timer_irq_action | arch_timer |

### Prerequisite evidence

| ID | Roadmap owners | Required evidence |
|---|---|---|
| G0 | P016-P045 | Identified host and cross tools reproduce the generic ARM64 smoke test; this is toolchain evidence only. |
| G1 | P046-P120 | Tested Apple CPU profile and T8103 board execute the original ELF; record feature exposure, RAM, reset state and all stubs. |
| G2 | P121-P135 | Apple UART TX, RX, FIFO and IRQ regressions pass; reviewed trace establishes host RX to UART to AIC delivery and acknowledgment. |
| G3 | P136-P180 | AIC device IRQ, separate architectural timer FIQ and two-core IPI acknowledgment pass independently; a one-core Linux witness does not waive this prerequisite. |
| boot-handoff | P181-P195 | Entry-state probe, reviewed FDT, nonoverlapping image/initramfs/RAM reservations and explicit clock, power and firmware-state assumptions pass together. |
| linux-integration | P196-P209 | Pinned source/configuration/patches, deterministic initramfs, active Apple drivers, scheduler, serial shell and bounded fresh-process capture are reproducible. |

### Required observations

| ID | Requirement |
|---|---|
| fresh-process | Three independent cold QEMU processes use identical hashed inputs and unique challenges; no snapshot, migration restore or recycled console log. |
| interactive-shell | After READY the host sends a fresh nonce and two operands through Apple UART; the probe returns their sum, exits, and a second command through the returned shell produces their product after END. |
| active-drivers | Guest reports aarch64, exact J274/T8103 compatible sequence, ttySAC0 as active console, samsung-uart binding and one online CPU. |
| uart-irq | Raw before/after interrupt snapshots retain the same AIC UART row and show increased activity across the input exchange; G2/G3 trace supplies RX causality. |
| timer-fiq | The separate AIC-FIQ arch_timer row advances and guest uptime advances at least one second across sleep; G3 independently proves the hardware FIQ route. |
| bounded-run | A monotonic host deadline covers startup and each exchange; timeout, premature process exit, panic, malformed or missing response and hash mismatch fail. |
| reviewed-evidence | Full serial, host-input events, emulator stderr, command, manifests, input hashes and prerequisite traces are retained and independently reviewed at P210. |

### Evidence record fields

| Record | Required fields |
|---|---|
| source | repository_url, commit, patch_series_sha256, configuration_sha256 |
| artifact | relative_path, size_bytes, sha256 |
| host | os, architecture, compiler_versions, build_commands, environment |
| invocation | argv, cwd, machine, cpu_profile, memory_layout, boot_mode, kernel_cmdline, entry_state, device_inventory, shortcuts |
| prerequisite | id, revision, command, result, evidence_sha256, limitations |
| run | id, fresh_process, nonce, left, right, serial_sha256, host_events_sha256, stderr_sha256, elapsed_seconds, termination_reason, checker_result |
| review | reviewer, date, prerequisite_review, device_route_review, limitations, verdict |

Required hashed artifacts: qemu-binary, linux-image, linux-config, linux-patch-series, dtb, dt-sources, dt-patch-series, busybox-binary, busybox-config, initramfs, init-script, probe-script, serial-binding-script, build-manifest.

Excluded substitutes: virt, vmapple, PL011, GIC, virtio-console, semihosting-console, snapshot-resume, host-root-filesystem.
<!-- P003-CONTRACT-END -->

## How the source profile was selected

The `linux-v6.12-observables-v1` profile records observable names verified in the pinned Linux source at `adc218676eef25575469234709c2d87185ca223a`. Its J274 tree identifies the target; its Samsung serial driver implements `apple,s5l-uart`; its AIC driver separates the `AIC` and `AIC-FIQ` chips. The timer action is `arch_timer`. The UART action comes from the platform device name `235200000.serial`, rather than the console name `ttySAC0`. See the [P003 primary sources](REFERENCES.md#p003-linux-witness-evidence).

These source snapshots define a test profile. They are **not a claim that P196 selected and built a working kernel**. A future baseline with different observable names needs a reviewed profile/schema update and regression evidence; silently broadening the checker to accept GIC, PL011 or arbitrary names is not allowed. BusyBox's official applet documentation supplies the shell/tool interface; P198 must still pin and build its exact redistributable version and configuration. No unverified downloaded binary is an input to this phase.

One online Linux CPU is the initial witness profile, with its exact Apple core identity and feature set recorded in the launch manifest. This bounds the first integrated workload and does not describe the physical M1's full topology. G3 still needs its independent two-core IPI evidence. The eight-core workstream and all other prerequisite phases retain their original checks.

## Prerequisite details

### CPU, UART, interrupts and time

Before trying the witness, retain passing G0–G3 evidence at the tested emulator revision or prove that intervening changes preserve that evidence. The Apple CPU profile must implement every exposed feature and required Apple system-register access used by the chosen kernel. A renamed generic CPU or a target-looking DT string is insufficient.

G2/G3 must include a receive-interrupt regression or trace that follows injected serial input through UART state, AIC assertion, CPU IRQ delivery, acknowledgment, device-source clearing and unmasking. The live witness also requires increasing UART IRQ counts, but that aggregate can include TX events; it alone does not establish RX interrupt causality. Likewise, the `AIC-FIQ` timer counter and advancing uptime show integrated scheduling activity; G3's separate FIQ-routing evidence establishes the hardware path. No external AIC IRQ-bank substitution for timer FIQ is permitted.

Required UART clocks and power state must be implemented or declared as reviewed laboratory pre-initialization. The stock device tree contains clock/power dependencies; deleting them until Linux boots without documenting the change would hide a dependency. No guessed MMIO reset values, frequency, load address or CPU profile string is selected by P003.

### Laboratory entry and device tree

P184–P195 must implement and verify the pinned [AArch64 boot protocol](https://docs.kernel.org/6.12/arch/arm64/booting.html). The initial profile uses a little-endian uncompressed `Image`, placed according to its header and recorded RAM reservations. Pass the physical FDT pointer in `x0`, zero `x1`–`x3`, mask DAIF, disable the MMU and record nonsecure EL1 or EL2 entry. Observe cache cleanliness, timer setup, coherency, DMA quiescence and every applicable feature-dependent register condition. The FDT must meet its alignment/size constraints; Image and initramfs must satisfy their shared physical-window requirement. The entry-state probe records the actual values and image/DTB/initramfs bounds.

A stock compiled J274 DTB is not a finished lab input. Its shared sources include loader-populated memory and CPU-release placeholders and devices outside this milestone. P185–P188 must produce a reviewed final FDT with valid RAM/reservations, initramfs start/end, `/chosen` command line and `stdout-path`, serial alias, CPU availability and Apple interrupt bindings. Preserve source provenance and every overlay/fixup. Disable unimplemented devices explicitly and retain all dependencies of active devices. Record the final DTB hash and inspect the runtime tree. FDT is not Apple's firmware ADT; neither a sanitized ADT dump nor a generic `virt` DTB is a replacement.

### Kernel and initramfs artifacts

P196/P197 must provide exact kernel source commit, config, ordered patch series, compiler/binutils versions and build commands. Record an empty patch series explicitly when there are no patches. Review the final `.config` after dependency resolution; setting symbols in a fragment alone is not evidence that they survived.

Required built-in support includes `CONFIG_ARM64`, `CONFIG_ARCH_APPLE`, `CONFIG_APPLE_AIC`, `CONFIG_ARM_ARCH_TIMER`, `CONFIG_SERIAL_SAMSUNG`, `CONFIG_SERIAL_SAMSUNG_CONSOLE`, `CONFIG_TTY`, `CONFIG_BLK_DEV_INITRD`, `CONFIG_BINFMT_ELF`, `CONFIG_BINFMT_SCRIPT`, `CONFIG_PROC_FS`, `CONFIG_SYSFS` and `CONFIG_DEVTMPFS`, plus the chosen filesystem and compression options. An early console can help diagnostics, but the full serial driver, input path and interrupts must work before success. This is a requirements list, not a complete boot-tested `.config`.

P198 must build a static AArch64 BusyBox with `ash` (`/bin/sh`), 64-bit shell arithmetic and the probe's applets: `cat`, `uname`, `tty`, `readlink` (including `-f`), `tr`, `stty` and `sleep`. Initialization additionally needs `mount`, `mkdir`, `setsid` and `cttyhack`. Enable the ash builtins used by the script, including `read -r -t`, `printf`, `test` and `trap`. Record the BusyBox source revision/archive hash, complete config, compiler/libc inputs, binary and applet inventory. Do not silently depend on host libraries or a host-shared root filesystem.

The initramfs must contain executable `/init`, `/bin/busybox`, `/bin/sh`, the needed applet links, the repository's unchanged probe at `/g4-probe.sh`, its helper at `/g4-serial-binding.sh`, necessary mount points and `/dev/console`. `/init` mounts procfs, sysfs and devtmpfs explicitly; an initramfs must not assume devtmpfs is automatically mounted. It then starts the interactive shell with its controlling terminal and all three standard descriptors on `/dev/ttySAC0`, for example via `setsid cttyhack /bin/sh -i` with explicit UART redirection. Record the exact `/init` and all archive entries, modes and links. `/init` must not run the probe automatically or preprint its responses.

Build a deterministic `newc` archive with stable ownership, timestamps, paths and ordering. Linux's `gen_init_cpio` file list can express device nodes without running a privileged archive builder. Pin toolchain/environment inputs and compare rebuilt artifacts before claiming byte reproducibility; a fixed timestamp alone is insufficient. Keep binaries/build outputs outside tracked project files unless their redistribution and provenance have been reviewed. See the [initramfs](https://docs.kernel.org/6.12/filesystems/ramfs-rootfs-initramfs.html) and [reproducible-build](https://docs.kernel.org/6.12/kbuild/reproducible-builds.html) documentation.

## Reproducible live procedure

**Execution is blocked until the prerequisites above are implemented.** The commands below specify the future witness interface. They cannot turn the currently available generic smoke experiment into a T8103 boot.

### 1. Lock the inputs and launch configuration

Resolve a clean project revision and the exact emulator source/build revision. Copy or reference the required artifacts by safe relative paths in a self-contained evidence directory. Compute SHA-256 and byte size for every artifact; hash the source/configuration/patch/build records too. Preserve licenses and source availability for redistributable Linux/BusyBox binaries. Reject missing, changed or unhashed inputs before starting QEMU.

The invocation record contains the exact argv array, working directory, relevant environment, TCG configuration, CPU profile, RAM/entry-state layout, kernel command line, device inventory and all laboratory shortcuts. Use one online CPU and a RAM-backed root. The required baseline kernel arguments are `console=ttySAC0,115200n8 rdinit=/init panic=0`; record any additional diagnostic arguments. Do not enable an alternate console that carries the witness.

The future lab loader must support the standard QEMU input interface represented by this template. All `M1_` values come from the reviewed artifact/launch record, not guessed defaults:

```sh
"$M1_QEMU" -M apple-m1-lab -accel tcg -cpu "$M1_CPU_PROFILE" \
  -m "$M1_RAM_MIB" -smp 1 -display none -monitor none \
  -serial stdio -no-reboot \
  -kernel "$M1_IMAGE" -dtb "$M1_DTB" -initrd "$M1_INITRAMFS" \
  -append 'console=ttySAC0,115200n8 rdinit=/init panic=0'
```

P209 supplies the live host runner. It must use separate stdin, serial stdout and stderr streams, pass argv without a shell, and start a new QEMU process with no saved-state options for each trial. An early process exit is a failure even if the exit code is zero. Keep the monitor away from the serial channel. No human keyboard input may race the scripted exchange.

### 2. Establish a live shell and challenge

For each cold boot, generate a fresh 128-bit nonce (`secrets.token_hex(16)`) and two independent integers (`secrets.randbelow(999999) + 1`), and record them. Across the three trials, reject reused nonces. Nonces prevent accidental replay; they do not authenticate an emulator against a malicious producer.

Within 300 seconds measured by a monotonic host clock, wait for the initialized interactive UART shell, then send this command with the validated nonce substituted:

```sh
/bin/sh /g4-probe.sh NONCE
```

The probe verifies its real terminal, reports the CPU/target/driver/console information, captures raw interrupt and uptime data, disables terminal echo and emits `G4-READY NONCE`. Its binding helper resolves the physical platform UART and verifies that the tty belongs beneath it, including Linux 6.12's intermediate serial-core devices. It checks the physical `samsung-uart` binding and `apple,s5l-uart` compatible instead of mistaking the intermediate `port` driver for the physical driver. **Only after receiving that ready frame**, generate or release the two operands to the guest by sending this line over the same UART:

```text
NONCE LEFT RIGHT
```

The probe reads with a 20-second timeout, checks canonical decimal operands, waits one guest second, captures the after snapshots and prints the computed sum in `G4-RESULT NONCE SUM`, followed by `G4-END NONCE`. The host must bound this exchange by 30 seconds regardless of whether the guest timer advances. Preserve raw CPU-column interrupt snapshots and two-field uptime readings; never replace them with manually supplied totals.

### 3. Prove the shell remains usable

After observing `G4-END NONCE`, let the probe return to the interactive shell and send a second command with the same validated nonce/operands:

```sh
[ "$?" -eq 0 ] && printf '\nG4-SHELL %s %s\n' NONCE "$((LEFT * RIGHT))"
```

Substitute the numeric `LEFT` and `RIGHT` literals in the arithmetic expression; do not precompute or transmit the expected product. Preserve the literal `$?` test: it requires the probe's exit status to be zero, and no intervening command may replace that status. Require `G4-SHELL NONCE PRODUCT` as a complete response line within another 30-second host deadline. The probe never emits that frame. The two different computations plus recorded send/receive ordering distinguish an executed probe and returned shell from a static boot banner or echo of the commands.

### 4. Check, retain and repeat

Run the shipped checker on the complete received serial transcript for that boot, with the recorded challenge values:

```sh
python3 tools/check_g4_transcript.py evidence/boot-1/serial.txt \
  --nonce "$M1_NONCE" --left "$M1_LEFT" --right "$M1_RIGHT"
```

It rejects missing/duplicated/reordered protocol frames, wrong target/driver/terminal, nonmatching nonce/arithmetic, unchanged or malformed interrupt snapshots, insufficient uptime progress and known panic/error signatures. It accepts ordinary surrounding boot text and the returned shell's prompt/command echo only where the protocol permits them. LF and serial CRLF line endings are supported. A malformed or absent capture is never a pass.

Preserve the complete byte capture, emulator stderr and a separate event log with monotonic timestamps and direction for every host write and received frame. The event log must prove the challenge was not supplied before READY and the product command was not supplied before END. The live runner also checks input hashes, actual argv, source/guest versions, cold-process lifecycle, deadlines and error output. **The offline text checker cannot prove those facts.** Unexpected diagnostics, panic, host/guest timeout, early exit or a required unavailable prerequisite make the trial fail or remain blocked, regardless of checker output.

After the final response, stop the otherwise-running guest deliberately from the host and record this as harness termination after success, not a guest shutdown or reset result. Repeat twice more from entirely fresh QEMU processes, using identical artifact hashes/configuration and new challenges. All three trials must meet every condition. A warm reset or a resumed machine cannot replace a cold boot.

### 5. Independent acceptance review

P210 reviews all six prerequisite groups, the three runs and the evidence field inventory. Match active UART and interrupt paths against the emulator device inventory, final DTB, kernel logs and prerequisite tests/traces. Check that full RX/TX uses the Apple UART, devices use AIC IRQ, timers use the separate FIQ path and no excluded substitute carries any required part of the workload. Identify unresolved MMIO accesses, kernel/emulator patches and lab shortcuts. Any unresolved dependency remains explicit; no metadata flag can override it.

Only this combined evidence can support a bounded G4 `machine-linux` result. The transcript checker reports **protocol consistency only**. Target strings, driver names, integer counters and JSON can be fabricated; an independent reviewer must assess provenance and causal device evidence. The contract validator likewise checks published requirements, not the truth of arbitrary prose or the authenticity of measurements.

## Failure classification and evidence layout

| Outcome | Meaning |
|---|---|
| Blocked | Machine, artifact, source record or prerequisite evidence does not exist or is not validated. G4 remains unrun. |
| Failed trial | A launched run times out, exits early, panics, mismatches hashes, uses a forbidden path or fails any witness observation. |
| Protocol-consistent transcript | The offline checker accepts the text and challenge. Live provenance, deadlines and prerequisites still require review. |
| Accepted G4 evidence | P210 review accepts all prerequisite evidence and all three fresh trials for the exact recorded workload and lab profile. |

Keep one bundle per candidate revision: `inputs/` for source/config/build manifests and artifact inventory, `prerequisites/` for G0–G3 and boot/integration evidence, `boot-1/` through `boot-3/` for serial/stderr/events/challenge/checker records, and `review/` for the independent decision and limitations. The outer artifact inventory hashes the build manifest; no manifest must include its own hash. The evidence fields are an inventory, not a prematurely completed P013 global report schema or P194 artifact-loader implementation. Use full immutable revisions and lowercase 64-digit SHA-256 values. An explicit empty patch series is valid; placeholder hashes, implicit defaults and success words without source evidence are not.

## What this milestone leaves outside its claim

This workload has no persistent-storage requirement: ANS/NVMMU/SART/RTKit and a persistent root filesystem belong to G6. It bypasses Apple Boot ROM, iBoot, SEP and authenticated firmware startup. It does not demonstrate macOS, GPU graphics, complete M1 device coverage, all eight Linux CPUs, cycle accuracy, native performance or full ISA conformance. P004 and later phases retain their separate scope and acceptance checks.

The hardware address registry remains reference-only. P003 implements no MMIO register, changes no hardware value and performs no physical-machine experiment. Its executable acceptance tooling is ready for the later implementation to exercise; its synthetic tests cannot award G4.

## P004 scope boundary

The [exploratory scope contract](EXPLORATORY_SCOPE.md) preserves every prerequisite and witness obligation above. Cycle accuracy, GPU graphics and unmodified macOS remain unimplemented and are not required for G4 or the v0.1 release. Correct functional timers, Apple UART/AIC behavior and the documented cold-boot evidence remain mandatory.
