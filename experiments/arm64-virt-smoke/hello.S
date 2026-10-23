/* First executable toolchain test only: uses the QEMU virt PL011 at 0x09000000.
 * NOT an Apple M1 or T8103 peripheral model. */
.section .text.boot, "ax"
.global _start
_start:
    ldr x0, =message
    ldr x1, =0x09000000
1:
    ldrb w2, [x0], #1
    cbz w2, 2f
    str w2, [x1]
    b 1b
2:
    wfe
    b 2b

.section .rodata
message:
    .asciz "ARM64 baseline OK\r\n"
