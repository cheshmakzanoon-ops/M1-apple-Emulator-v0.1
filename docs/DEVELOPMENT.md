# Building and testing

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Target and metadata checks

Python 3.11+ and a POSIX host shell are sufficient for the P001 target check, P002 fidelity contract, P003 witness contract, P004 scope policy and synthetic regression suite. Run these commands from the repository root:

```sh
python3 tools/validate_target.py
python3 tools/validate_fidelity.py
python3 tools/validate_boot_milestone.py
python3 tools/validate_scope.py
python3 tools/validate_hardware.py
python3 tools/validate_roadmap.py
python3 -m unittest discover -s tests -v
```

The target validator checks the machine-readable identity and exclusions in `hardware/t8103.json` and the eight visible target declarations listed in the [P001 charter](ARCHITECTURE.md#p001-target-charter), including the P003 witness and P004 scope specifications. It exits nonzero for missing, malformed or conflicting declarations. Its default paths are relative to the script, so invoking it by absolute path also works from another directory. `--root PATH` checks a separate repository snapshot without modifying it. The check is offline and does not inspect a physical Mac or prove device compatibility.

## Fidelity policy check

`docs/fidelity.json` defines seven independent classifications and the 12 named development/formal release gates. The [P002 architecture contract](ARCHITECTURE.md#p002-fidelity-contract) publishes the definitions, required evidence, exclusions and gate tables; the five final roadmap phases carry matching annotations. `tools/validate_fidelity.py` rejects missing, duplicate, unknown, malformed or mismatched entries, including promotion of the generic smoke test to Apple or Linux compatibility. Tests exercise those failures against modified repository snapshots.

The checker uses no third-party packages or network and supports `--root PATH`, including invocation from another working directory. Edit the manifest and its published definitions/tables together when the reviewed policy changes. The pure rendering helpers `render_levels(raw)` and `render_gates(raw, kind)` in the validator produce the expected Markdown from valid JSON; they do not write files. Additions or changes to gate scope also need the validator's explicit inventory and regression tests reviewed. `machine-macos` is defined for claim separation and is awarded by no v0.1 gate.

This validates a published policy, not the truth of arbitrary prose, the authenticity of linked sources or runtime compatibility. It does not boot a guest, compare silicon or mark gates passed. P003 supplies the [reproducible Linux witness specification](LINUX_BOOT_MILESTONE.md).

## Linux milestone and witness checks

`docs/boot-milestone.json` freezes the G4 target, prerequisites, test limits, required observations and evidence inventory. `tools/validate_boot_milestone.py` checks the schema, bounded scope, immutable source profile and matching visible specification. It also supports `--root PATH` and invocation from another directory. The shell/protocol tests are synthetic and require neither QEMU nor a guest image; they exercise malformed evidence, missing dependencies, serial-core device ancestry, arithmetic challenges and UART/timer distinctions.

The guest probe and serial-binding helper under `experiments/linux-boot-witness/` are inputs for the future P198 initramfs. `tools/check_g4_transcript.py` verifies a recorded serial exchange against independently recorded nonce/operand arguments. Its successful output means protocol consistency only. Read the [complete procedure](LINUX_BOOT_MILESTONE.md#reproducible-live-procedure) for required host event ordering, artifact hashes, three fresh processes, deadlines and independent G0–G3/device-route review.

The T8103 machine and boot artifacts are still unavailable. Do not run the probe on the host as though it were an M1 test, substitute QEMU `virt`, or call a synthetic fixture a G4 pass. P209 supplies live capture/timeout enforcement and P210 certifies actual runtime evidence.

## Exploratory scope check

`python3 tools/validate_scope.py` checks the three exclusions in `docs/scope.json`, their [published specification](EXPLORATORY_SCOPE.md), all 12 named gate boundaries and the optional WS20/WS21 phase annotations. It also runs the P002/P003 contract validators and checks root/docs Markdown plus structured gate prose for explicit contradictory feature claims. `--root PATH` validates a separate snapshot. `render_contract(raw)` returns the expected specification block without writing files.

The [scope-check regression suite](../tests/test_scope.py) exercises false capability promotion, coordinated gate/prose edits, malformed policy, hidden declarations, optional research completion and CLI errors. This bounded lint does not replace review or certify runtime success; P014 remains separate future work.

## Generic ARM64 baseline

On Ubuntu or Windows 11 with WSL2 Ubuntu, install Python 3.11+, GNU Make, QEMU ARM system emulation, AArch64 cross GCC/binutils, Git, Meson and Ninja:

```sh
sudo apt-get update
sudo apt-get install -y git make python3 qemu-system-arm gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu build-essential meson ninja-build pkg-config libglib2.0-dev libpixman-1-dev
```

Compile and run the existing Phase 0 experiment after the metadata checks:

```sh
make -C experiments/arm64-virt-smoke
python3 tools/run_arm64_smoke.py experiments/arm64-virt-smoke/build/hello.elf
```

This baseline runs **QEMU `virt`**, not an Apple M1 machine. It is solely the portable CI/smoke-test foundation.

## QEMU source checkout

Use a fixed QEMU `v11.1.2` upstream baseline for future T8103 device and machine integrations:

```sh
sh tools/setup_qemu.sh
```

The script places the checkout/build under the ignored `vendor/` directory. Do not copy upstream QEMU into this repository without preserving license and source provenance. Actual Apple board integration and tests are future roadmap phases.

## Research-device safety

Ordinary development should not require changes to your physical Mac's NOR flash, macOS boot policy, or production partitions. If using m1n1 later, follow current Asahi reference-machine guidance, maintain backups, and sanitize traces and ADT dumps; they can expose secrets and identifiers.
