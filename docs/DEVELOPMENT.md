# Building and testing

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Target and metadata checks

Python 3.11+, Git and a POSIX host shell are sufficient for the P001 target check, P002 fidelity contract, P003 witness contract, P004 scope policy, P006 source licensing review, P007 contribution checks and synthetic regression suite. Use the [main contribution workflow](../CONTRIBUTING.md) for review, exact staged-tree verification and publication. Run these commands from the repository root:

```sh
python3 tools/validate_target.py
python3 tools/validate_fidelity.py
python3 tools/validate_boot_milestone.py
python3 tools/validate_scope.py
python3 tools/validate_licensing.py
python3 tools/validate_branch_policy.py
python3 tools/validate_hardware.py
python3 tools/validate_roadmap.py
python3 -m unittest discover -s tests -v
```

The target validator checks the machine-readable identity and exclusions in `hardware/t8103.json` and the eleven visible target declarations listed in the [P001 charter](ARCHITECTURE.md#p001-target-charter), including the P003 witness, P004 scope, P005 executor, P006 licensing and P007 contribution specifications. It exits nonzero for missing, malformed or conflicting declarations. Its default paths are relative to the script, so invoking it by absolute path also works from another directory. `--root PATH` checks a separate repository snapshot without modifying it. The check is offline and does not inspect a physical Mac or prove device compatibility.

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

## Source licensing checks

`python3 tools/validate_licensing.py` checks [licensing.json](licensing.json) against the Git working tree, including tracked ignored files and nonignored untracked source. It requires an explicit inventory entry for each source file, preserves the MIT permission notice, rejects conflicting SPDX headers and unreviewed asset/import paths, and checks SHA-256 digests of the nine reviewed dependency declaration/build/runner inputs. P007 adds the contribution procedure and local Git guard to the original seven surfaces. Read the [licensing policy](LICENSING.md) before adding files or updating those digests; a new hash is a recorded human review, not automatic permission to copy code.

Use `python3 tools/validate_licensing.py --root /path/to/clean-export --archive` on an extracted source archive. This explicit mode scans every file without Git ignore rules and rejects Git metadata; it needs no Git executable. Run it before compiling or running Python in that export, since generated ELF files and bytecode are outside the source inventory. Default mode requires a Git root and never silently falls back after a Git error. Both modes read working files, not staged blobs; verify the exact staged export or committed tree before publication.

The check is offline and uses the Python standard library. It records the current source-only boundary, not a transitive package SBOM, proof of authorship or approval of future binary releases. Adding a third-party source file, guest image, QEMU binary, ROM, library or container needs the policy's separate provenance and redistribution review.

## Main branch contribution checks

`python3 tools/validate_branch_policy.py` checks the visible contribution contract, links from the README, engineering rules and this guide, common contradictory instructions and unsafe shell examples, and the workflow's explicit main-only push/main-targeted optional pull-request triggers. CI runs this offline mode, which also works in source exports and detached checkouts. The trigger check intentionally accepts the current simple YAML event block; changing that supported form requires reviewing the validator and tests together. No third-party YAML parser is introduced.

`python3 tools/validate_branch_policy.py --checkout` adds a read-only local preflight: an existing attached `main` at the selected Git root, no unresolved index/operation, no unstaged tracked or nonignored untracked files, and a cached `origin/main` that is an ancestor of `HEAD`. Staged changes and unrelated existing refs are allowed. `--root PATH` selects another snapshot or checkout. The guard disables optional index writes, filesystem-monitor hooks and lazy fetching, and stops before an active configured clean/process filter could execute. Unused driver definitions, such as installed Git LFS configuration without matching attributes, are allowed. Use a complete local checkout; unsupported active filters need separate review. The guard never creates branches, changes refs, commits or pushes. Its cached ancestry check cannot prove remote freshness.

The [contribution procedure](../CONTRIBUTING.md) supplies the separate review and exact staged-tree export/test/commit/publish steps. The linter is bounded: it recognizes the published contract and common shell/prose patterns, not arbitrary shell programs or every contradictory sentence. Neither mode certifies that review or tests actually happened, configures remote protection, or awards a runtime gate. Hosted verification must be checked against the exact published commit SHA; a detached pull-request run is not the authoritative push result.

## Generic ARM64 baseline

[ADR 0001](decisions/0001-qemu-tcg.md) selects QEMU **full-system AArch64 TCG** for the Linux/WSL2 x86_64 development baseline. The runner passes `-accel tcg` explicitly, with no KVM/HVF fallback. `qemu-aarch64` user-mode translation, an accelerated VMApple machine and the future T8103 machine are different execution targets; they cannot substitute for this command's evidence.

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

This baseline runs **QEMU `virt`** with a generic Cortex-A57 and PL011 UART. It is solely the portable CI/smoke-test foundation. The payload prints its marker then idles, so the runner deliberately ends it after the timeout (eight seconds by default). `--timeout SECONDS` must be finite, positive and at most 300 seconds; the bound avoids platform timeout overflow and is a smoke-test budget, not a hardware timing claim. Missing tools/files, emulator launch errors, missing markers and nonzero emulator failures return nonzero; a marker cannot hide an emulator failure. A deliberate timeout kill after the marker is the expected looping-payload completion path.

The focused runner tests are available independently of QEMU:

```sh
python3 -m unittest discover -s tests -p test_arm64_smoke.py -v
```

Those tests use controlled subprocess results; they verify command selection and failure handling, not ARM architectural behavior. The full suite remains required. Actual generic guest execution needs the compiler and emulator above, and later Apple-target evidence needs its own machine and artifacts.

## QEMU source checkout

The existing setup scaffold defaults to the QEMU `v11.1.2` tag for future T8103 device and machine integrations:

```sh
sh tools/setup_qemu.sh
```

The script places the checkout/build under the ignored `vendor/` directory. Its tag-based check does not yet establish P017's immutable dependency pin or P019's complete checkout verification. The ADR's source commit pins reviewed evidence only; distribution QEMU used by the generic smoke job can have a different version. Record the actual executable version with runtime results. Do not copy upstream QEMU into this repository without preserving license and source provenance. Actual Apple board integration and tests are future roadmap phases.

## Research-device safety

Ordinary development should not require changes to your physical Mac's NOR flash, macOS boot policy, or production partitions. If using m1n1 later, follow current Asahi reference-machine guidance, maintain backups, and sanitize traces and ADT dumps; they can expose secrets and identifiers.
