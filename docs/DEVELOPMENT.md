# Building and testing

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Target and metadata checks

Python 3.11+ is sufficient for the P001 target check, P002 fidelity contract and metadata regression suite. Run these commands from the repository root:

```sh
python3 tools/validate_target.py
python3 tools/validate_fidelity.py
python3 tools/validate_hardware.py
python3 tools/validate_roadmap.py
python3 -m unittest discover -s tests -v
```

The target validator checks the machine-readable identity and exclusions in `hardware/t8103.json` and the six visible target declarations listed in the [P001 charter](ARCHITECTURE.md#p001-target-charter). It exits nonzero for missing, malformed or conflicting declarations. Its default paths are relative to the script, so invoking it by absolute path also works from another directory. `--root PATH` checks a separate repository snapshot without modifying it. The check is offline and does not inspect a physical Mac or prove device compatibility.

## Fidelity policy check

`docs/fidelity.json` defines seven independent classifications and the 12 named development/formal release gates. The [P002 architecture contract](ARCHITECTURE.md#p002-fidelity-contract) publishes the definitions, required evidence, exclusions and gate tables; the five final roadmap phases carry matching annotations. `tools/validate_fidelity.py` rejects missing, duplicate, unknown, malformed or mismatched entries, including promotion of the generic smoke test to Apple or Linux compatibility. Tests exercise those failures against modified repository snapshots.

The checker uses no third-party packages or network and supports `--root PATH`, including invocation from another working directory. Edit the manifest and its published definitions/tables together when the reviewed policy changes. The pure rendering helpers `render_levels(raw)` and `render_gates(raw, kind)` in the validator produce the expected Markdown from valid JSON; they do not write files. Additions or changes to gate scope also need the validator's explicit inventory and regression tests reviewed. `machine-macos` is defined for claim separation and is awarded by no v0.1 gate.

This validates a published policy, not the truth of arbitrary prose, the authenticity of linked sources or runtime compatibility. It does not boot a guest, compare silicon or mark gates passed. P003 retains responsibility for the reproducible Linux witness specification.

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
