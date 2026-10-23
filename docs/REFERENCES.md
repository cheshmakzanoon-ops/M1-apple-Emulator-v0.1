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
