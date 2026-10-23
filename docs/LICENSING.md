# P006 — Licensing and redistribution boundaries

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

**Review date:** 2026-10-23. **Scope:** the project source tree and its declared direct development inputs. The canonical P006 requirement is to distinguish MIT project-authored files, future GPL QEMU-derived code and Apple proprietary assets, and pass a dependency and redistribution review. This is a bounded engineering review, not a legal certificate or a complete transitive software bill of materials.

The reviewed repository distributes project-authored text sources, documentation, metadata and standalone experiments. It does not vendor QEMU or distribute a QEMU executable, Linux/BusyBox guest image, m1n1 build, Apple firmware, Boot ROM or operating-system image. Local installation or configuration of an external tool is recorded separately from redistribution. This phase implements no Apple CPU or device and awards no runtime fidelity gate.

## The three licensing boundaries

| Material | Applicable boundary | Project action |
|---|---|---|
| Original project documentation, Python/shell tooling, metadata and standalone experiments | The existing root [MIT license](../LICENSE) applies to the project's own contribution. Its copyright and permission notice must accompany copies or substantial portions. | Keep `LICENSE` intact and classify each reviewed file explicitly in [licensing.json](licensing.json). An unreviewed file does not inherit MIT merely because of its directory. |
| Future QEMU-derived or integrated emulator code | QEMU describes the complete emulator as GPL version 2, with individual files retaining their own terms. Its license policy assigns unlabelled files GPL version 2 or later; that fallback is an upstream policy, not permission to remove existing headers. | Preserve origin, applicable file notices and modification history. Review the resulting combined distribution under the applicable GPL terms. Do not label the entire emulator MIT. [Q1] |
| Apple proprietary firmware, ROMs, images and captures containing proprietary payloads | No permission is inferred from possession, a public URL, a successful download, or an emulator's ability to load an asset. | Do not commit, upload, bundle or redistribute these assets through this project. Sanitization of identifiers does not convert a proprietary payload into an open-source asset. [A1][A2] |

The root MIT grant cannot grant rights in someone else's material. It also does not change when a separately installed GPL tool runs a project-authored script. The existing smoke runner launches QEMU as a separate executable; the guest program and its build inputs remain independently classified. If a later design copies QEMU code, links an emulator library, shares internal structures or otherwise creates an integrated work, the integration itself requires review. A process boundary is not an automatic exemption for every conceivable design; GNU's GPL FAQ distinguishes ordinary communication from intimate program combination. [G2]

### QEMU and TCG are not one uniform file license

The reviewed QEMU license policy explicitly identifies mixed licenses. Although much of TCG is BSD/MIT licensed, some TCG parts have GPL or other terms. Its bundled firmware is treated separately from the emulator and carries its own licenses. Consequently, neither “TCG is permissive” nor “QEMU is GPL” is enough to classify a copied file, ROM or complete release archive. Inspect the actual selected files, dependencies and firmware at the selected revision. [Q1]

The QEMU evidence revision is `4fc49f46dc95d4a27de2509e7fceb2931e91faeb`, associated with the existing `v11.1.2` evidence snapshot. This pins the licensing text reviewed here. It does not pin the Ubuntu QEMU package, the setup script's overridable tag, a future source build, or a binary's linked dependencies. P017 and the later build/release phases retain those obligations.

## Declared direct dependency review

The table covers the acquisition and execution inputs declared by the current workflow, developer setup instructions and QEMU setup script. None is vendored or bundled in the project source distribution. The corresponding reviewed input hashes in `licensing.json` make changes to those declarations require another review.

| Declared input | Where and why it is used | Current licensing disposition |
|---|---|---|
| `actions/checkout@v4` | `.github/workflows/verify.yml`; obtains this repository in both jobs | The action's own root license is MIT. The referenced tag is mutable; no action implementation or its dependency bundle is redistributed here. [C1] |
| `actions/setup-python@v5`; Python `3.12` | Workflow metadata job; provisions the test interpreter | The action's root license is MIT. Python and the action's bundled dependencies have separate notices; the action's MIT license does not cover the installed interpreter. No interpreter is bundled here. [C2] |
| `ubuntu-24.04` | Both hosted jobs | A hosted operating-system environment containing many separately licensed packages; not a single-license project component or an exported image. |
| `git` | Development instructions and QEMU checkout | Upstream GPL version 2 by default unless otherwise stated; external tool only. Review the selected package's actual copyright records before bundling. [H1] |
| `make`, `build-essential` | Development instructions; guest compilation and host build prerequisites | GNU Make is GPL version 3 or later. `build-essential` is a distribution metapackage, not one license for all dependencies. No toolchain is redistributed. [H2] |
| `python3` | Development instructions; standard-library validators/tests | Python has the PSF license and historical/incorporated-component terms. Current project imports are standard-library or local modules; no third-party Python package is required. [H3] |
| `gcc-aarch64-linux-gnu`, `binutils-aarch64-linux-gnu` | Workflow and development instructions; assemble/link the standalone smoke guest | GCC/binutils tools have GPL version 3 or later and component-specific terms. The GCC runtime exception applies only where granted. The guest recipe uses `-nostdlib -nostartfiles`; this does not classify all future compiler output or runtime libraries. [H4][H5] |
| `qemu-system-arm` | Workflow and development instructions; provides `qemu-system-aarch64` for the generic TCG smoke run | External distribution package with QEMU and potentially separately licensed runtime/firmware inputs. The upstream whole-emulator GPL boundary does not replace the selected package's notices. |
| `meson`, `ninja-build` | Development instructions; configure/build QEMU | Upstream projects use Apache 2.0; their packaged dependencies still need their own review. They are external build tools, not distributed project source. [H6][H7] |
| `pkg-config` | Development instructions; discover installed libraries | Provider-dependent package name: Ubuntu 24.04's package is supplied by `pkgconf`, with its own permissive and per-file terms. Do not assign the original freedesktop implementation's license solely from the command name. [H8] |
| `libglib2.0-dev`, `libpixman-1-dev` | Development instructions; QEMU build dependencies | GLib's main license is LGPL 2.1 or later; pixman identifies MIT. A future linked build must review actual versions, linking/relinking requirements, per-file terms and bundled files. [H9][H10] |
| QEMU checkout from `https://github.com/qemu/qemu.git`; default `QEMU_REF=v11.1.2` | `tools/setup_qemu.sh`; configures `aarch64-softmmu` under `vendor/qemu/build-m1` | Upstream source remains under its own licenses. The script configures the checkout and prints a Ninja build instruction; it does not vendor it into this repository or certify its full dependency closure. [Q1] |

Package names and action tags above describe declared inputs, not a locked installation. Ubuntu package revisions, recommended packages, shared libraries, firmware, QEMU subprojects and configure-selected dependencies can change. Before distributing any of them, collect the actual package/source identities, installed copyright/license files (normally under `/usr/share/doc/<package>/copyright` on Debian-derived systems), upstream notices, and build configuration. The current direct-input review cannot substitute for that artifact-specific record. Debian's copyright-file specification describes those package records and their per-file scope. [D1]

Ignored local `vendor/`, build outputs, logs and private research inputs are not distributed simply because they exist in a developer's checkout. Conversely, an ignore rule does not prevent a forced Git addition, inclusion in a release ZIP, container image, CI artifact or installer. Each outgoing artifact needs its own complete inventory. This repository's current workflow compiles and runs the generic guest; it has no release or artifact-upload step.

## References, imported material and future guest inputs

Hardware facts and original summaries are recorded with citations. A citation is not a license to copy expressive source code, documentation, images or data files. Record whether a new contribution is an original implementation informed by evidence, an adapted source file, a copied documentation passage, or a generated artifact; a filename or SPDX label alone cannot establish that distinction.

| Source or future input | Reviewed boundary | Required treatment before importing or distributing |
|---|---|---|
| Linux source and device trees | The pinned kernel `COPYING` declares GPL version 2 only with the Linux syscall exception; individual files can have additional or alternative permissions. The reviewed J274 DTS header, for example, offers `GPL-2.0+ OR MIT`. [L1][L2][L3] | Preserve the chosen file's actual license, notices and provenance. A permissive DTS option does not make the entire kernel MIT; the syscall exception does not permit arbitrary reuse of kernel code. |
| Asahi documentation | The reviewed documentation repository is CC BY 3.0. [S1] | Attribute copied/adapted material under the applicable terms and retain its classification. Do not silently place copied Asahi prose under the root MIT label. Original factual summaries still cite their evidence. |
| m1n1 | A reference/research tool, not a selected build input. The reviewed upstream README distinguishes MIT releases through 1.9.9 from GPL version 2 or later starting with 2.0.0, and lists separately licensed bundled components. [S2] | Choose and pin a version before import; inspect its files and components. Do not carry an old “m1n1 is MIT” assumption into a different revision. |
| Linux and BusyBox boot artifacts | Future P196–P198 inputs; none is included here. BusyBox describes its combined distribution as GPL version 2 only, while individual source files may offer wider choices. [B1] | Record actual kernel/BusyBox versions, configurations, patches, libc/toolchain and image contents. Review each component and provide corresponding source/notices for distributed GPL binaries. |
| Arm and Apple documentation | Cited vendor evidence, not a bundled documentation dependency | Link and write original source-grounded explanations. Any copied diagrams, substantial passages or files require their own permission/license review. Public access alone does not assign MIT rights. |
| Reference-machine traces and Apple Device Tree captures | No physical capture is distributed by this phase | Check provenance, contents and redistribution rights; remove secrets and personal/device identifiers. Keep firmware bytes, keys and proprietary images out of the repository and published evidence. |

### Apple assets remain excluded

The project prohibition covers Apple firmware and firmware payloads, Boot ROM dumps, iBoot/SEP images, IPSW/DMG operating-system images, proprietary kernel collections and containers carrying those contents. It applies equally to test fixtures, release attachments, generated installers, hosted downloads and CI uploads. Do not add code that silently acquires and republishes them as test dependencies.

Asahi's platform introduction explicitly distinguishes access to Apple's public firmware CDN from permission to redistribute system firmware. Apple's example macOS Tahoe agreement separately addresses firmware/Boot ROM and open-source components. The governing agreement must be identified for the actual asset; Apple's license index warns that the applicable agreement may differ from the posted example. These sources support a conservative project exclusion; they do not establish permission for every private experiment or a universal legal conclusion about every Apple file. [A1][A2][A3]

## Procedure for a future source import

Before accepting copied, adapted or generated third-party material:

1. Identify every incoming path, upstream URL, exact revision or release archive hash, original copyright notice, actual license/exception and modification status. Record any selected alternative in a dual license; do not invent an `OR` choice that upstream did not offer.
2. Keep upstream license texts and file notices with the imported material. Record modifications and dates where required. Preserve separate licenses for subprojects, generated tables, documentation, firmware and tests.
3. Describe how the material is used: separate tool, copied source, linked library, integrated QEMU module, guest content, or data. Review compatibility for the resulting distribution, including any source-code obligations.
4. Update the explicit inventory and this review. Unknown origin, unclear permission, unresolved license compatibility, or a prohibited Apple payload blocks inclusion; do not replace missing evidence with an MIT header.
5. Review code and provenance independently, run the inventory checks, and record the result in the relevant phase/change evidence. Current policy admits the reviewed project-authored text tree only; future third-party imports require an explicit policy/validator update as well as their own substantive review.

Writing a new module inside QEMU does not remove the combined emulator's GPL obligations. Original, separately distributed project tooling can retain its MIT license, while the integrated emulator and imported files retain their applicable terms. The import record must make those scopes understandable to recipients.

## Procedure for a future binary or source release

The following is project release policy. It applies to an installer, archive, container, downloadable guest, CI artifact or release attachment as well as a conventional package:

1. Inventory the **actual outgoing files**, with hashes and origins. Include linked or bundled libraries, firmware/option ROMs, guest files, generated assets, configuration and scripts. Compare that inventory with a clean, reproducible build record and the source-import reviews.
2. Include all applicable license texts, copyright notices, required attribution and modification notices. Preserve the MIT notice for the project-authored portions without implying that the whole package is MIT.
3. For distributed GPLv2 executables, use this project's selected **accompanying complete corresponding source** route. Supply the precise source, modifications, interface definitions and scripts controlling compilation/installation for that binary, together with configuration and dependency records sufficient to identify the build. Publish it alongside the binary with equivalent access. A casual link to an upstream homepage, an unrelated tag, or a patch alone is not this project's fulfillment record. GPLv2 section 3 describes additional routes and a system-component exception; neither is automatically selected or presumed applicable here. [G1]
4. Review non-GPL components separately, including LGPL linking/relinking requirements where applicable and the independent licenses of firmware and guest content. Do not treat a source bundle as permission to distribute an otherwise prohibited asset.
5. Verify a recipient can retrieve the source/notices, match them to the released binary, and follow the recorded build steps. Record who reviewed the exact artifact, remaining restrictions and the final redistribution decision before upload.

The GPL also requires preservation of license/warranty notices and notices of modified files; a combined derivative distribution has obligations beyond the origin of an individual new file. [G1] This checklist is intentionally stricter than merely retaining a dependency URL. It does not declare any future binary approved in advance.

## Offline inventory validation

Run from the repository root:

```sh
python3 tools/validate_licensing.py
python3 -m unittest discover -s tests -p test_licensing.py -v
```

`docs/licensing.json` records the explicit reviewed file list, ownership/license boundary, direct dependency review and hashes of the reviewed dependency-input files. `tools/validate_licensing.py` checks that contract without fetching remote content. Default Git mode examines tracked files plus nonignored untracked files, so newly written source must be classified before it can pass. Tracked files that violate the ignored-artifact boundary are rejected even when force-added. The check rejects unreviewed files, malformed/contradictory records, symlinks/submodules, unsafe paths and binary/non-text payloads in the current source-only scope.

`--root PATH` checks a different checkout. For a clean source export without Git metadata or local generated outputs, select archive mode explicitly:

```sh
python3 tools/validate_licensing.py --root /path/to/source-export --archive
```

Archive mode examines every file in the export, including files that a Git ignore rule would otherwise hide. This prevents an export's ignored contents from silently escaping its inventory. Do not use archive mode on a development checkout containing `.git` or local build/vendor directories and interpret those additional files as distributable project sources.

The validator is a consistency and scope gate. It cannot prove authorship, recognize every copied passage or disguised proprietary payload, discover all transitive dependencies, authenticate a remote license, determine whether a particular integration is legally a derivative work, or certify a release artifact that it has not inventoried. Ignored, untracked local research/build directories are outside default Git mode. Human source review and the artifact-specific release procedure remain necessary. Test results and the final P006 decision are recorded separately in the phase report.

## Primary licensing evidence

The immutable links below identify reviewed text, not verified build inputs. Live references and floating action tags were reviewed on 2026-10-23; their current contents require rereview when used in a later import or release.

- **[Q1]** QEMU [license policy](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/LICENSE) and [COPYING](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/COPYING), evidence revision `4fc49f46dc95d4a27de2509e7fceb2931e91faeb`: whole-emulator, per-file, TCG and firmware boundaries.
- **[G1]** [GPL version 2 as published by QEMU](https://www.qemu.org/license-gpl-2/), sections 1–3; the pinned QEMU `COPYING` above is the immutable companion text.
- **[G2]** GNU [GPLv2 FAQ on aggregation and combinations](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.en.html#MereAggregation): communication mechanism and semantics both matter. This is the license author's guidance, not an automatic classification of every future design.
- **[L1]** Linux [COPYING](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/COPYING), evidence revision `adc218676eef25575469234709c2d87185ca223a`.
- **[L2]** Linux [licensing rules](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/Documentation/process/license-rules.rst): per-file SPDX identifiers, exceptions and dual licensing.
- **[L3]** Linux [J274 device-tree source](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/arch/arm64/boot/dts/apple/t8103-j274.dts): the cited file's own dual-license header.
- **[S1]** Asahi documentation [LICENSE](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/LICENSE), evidence revision `0d1f8917fa88745d62a4c05d802c4a7298c8616b`.
- **[S2]** m1n1 [upstream README, license section](https://github.com/AsahiLinux/m1n1/blob/7cde7d1a784d851ebfee5579fa363c38b14150c0/README.md), evidence revision `7cde7d1a784d851ebfee5579fa363c38b14150c0`: version-dependent project license and separately licensed components; no project build version selected.
- **[B1]** BusyBox [license policy](https://busybox.net/license.html): distribution and source-availability requirements; live upstream reference.
- **[A1]** Asahi [platform introduction](https://github.com/AsahiLinux/docs/blob/0d1f8917fa88745d62a4c05d802c4a7298c8616b/docs/platform/introduction.md): system firmware, public CDN access and redistribution limits.
- **[A2]** Apple [macOS Tahoe software license agreement](https://www.apple.com/legal/sla/docs/macOSTahoe.pdf), English sections 2J–2M: firmware/Boot ROM and separately governed open-source components. This is a reviewed example agreement, not a license for all possible assets.
- **[A3]** Apple [software license agreement index](https://www.apple.com/legal/sla/): identify the agreement applicable to the actual software and acquisition.
- **[C1]** [actions/checkout LICENSE at v4](https://github.com/actions/checkout/blob/v4/LICENSE); floating action reference, not an immutable execution pin.
- **[C2]** [actions/setup-python LICENSE at v5](https://github.com/actions/setup-python/blob/v5/LICENSE); floating action reference, not an immutable execution pin.
- **[D1]** Debian [machine-readable copyright-file specification](https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/): package copyright, license and per-file records. Distribution package metadata is supporting evidence, not a replacement for upstream terms or review of the actual outgoing files.
- **[H1]** Git [COPYING](https://github.com/git/git/blob/master/COPYING): upstream default and exceptions; live upstream reference.
- **[H2]** GNU [Make project page](https://www.gnu.org/software/make/): GPL version 3 or later; live upstream reference.
- **[H3]** Python [license and copyright record](https://docs.python.org/3/license.html): PSF, historical and incorporated-software terms; live upstream reference.
- **[H4]** GCC [driver source license](https://github.com/gcc-mirror/gcc/blob/master/gcc/gcc.cc) and [runtime library exception 3.1](https://www.gnu.org/licenses/gcc-exception-3.1.en.html): component-specific terms and limits; live upstream references.
- **[H5]** Binutils [upstream project page](https://sourceware.org/binutils/wiki/HomePage) and the selected distribution's `/usr/share/doc/binutils/copyright`: tool and component notices; review actual package revision before redistribution.
- **[H6]** Meson [COPYING](https://github.com/mesonbuild/meson/blob/master/COPYING): Apache 2.0; live upstream reference.
- **[H7]** Ninja [COPYING](https://github.com/ninja-build/ninja/blob/master/COPYING): Apache 2.0; live upstream reference.
- **[H8]** Ubuntu Noble [pkg-config package metadata](https://packages.ubuntu.com/en/noble/pkg-config) and pkgconf [COPYING](https://github.com/pkgconf/pkgconf/blob/main/COPYING): distinguish the package provider and its file-level terms; live distribution/upstream references.
- **[H9]** GLib [upstream reference documentation](https://docs.gtk.org/glib/): LGPL 2.1 or later; live upstream reference.
- **[H10]** pixman [upstream project page](https://pixman.org/): MIT; live upstream reference.
