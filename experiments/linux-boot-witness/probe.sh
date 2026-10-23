#!/bin/sh
# P003 witness workload for a future BusyBox ash initramfs, not a boot result.
# Source profile: Linux v6.12; see docs/LINUX_BOOT_MILESTONE.md.
# The init shell must have /dev/ttySAC0 as its controlling input/output tty.
set -eu

fail() {
    printf '\nG4-ERROR %s\n' "$1" >&2
    exit 1
}

restore_terminal() {
    if ! stty "$terminal_state"; then
        printf '\nG4-ERROR terminal restoration failed\n' >&2
        return 1
    fi
}

cleanup() {
    saved_status=$?
    trap - 0
    if ! restore_terminal; then saved_status=1; fi
    exit "$saved_status"
}

[ "$#" -eq 1 ] || fail 'expected one 32-character lowercase hexadecimal nonce'
nonce=$1
[ "${#nonce}" -eq 32 ] || fail 'invalid nonce length'
case "$nonce" in *[!0-9a-f]*) fail 'invalid nonce characters' ;; esac

terminal=$(tty) || fail 'standard input is not a tty'
[ "$terminal" = /dev/ttySAC0 ] || fail 'standard input is not Apple ttySAC0'
terminal_state=$(stty -g) || fail 'cannot read terminal settings'
trap cleanup 0
trap 'exit 1' HUP INT TERM
stty -echo

printf '\nG4-BEGIN %s\n' "$nonce"
printf 'G4-ARCH %s\n' "$(uname -m)"
printf 'G4-TTY %s\n' "$terminal"
driver=$(/bin/sh /g4-serial-binding.sh /sys) || fail 'serial binding verification failed'
printf 'G4-DRIVER %s\n' "$driver"
printf 'G4-COMPAT-BEGIN\n'
tr '\000' '\n' < /proc/device-tree/compatible
printf 'G4-COMPAT-END\n'
printf 'G4-CONSOLES-BEGIN\n'
cat /proc/consoles
printf 'G4-CONSOLES-END\n'
printf 'G4-IRQ-BEFORE-BEGIN\n'
cat /proc/interrupts
printf 'G4-IRQ-BEFORE-END\n'
printf 'G4-UPTIME-BEFORE %s\n' "$(cat /proc/uptime)"
printf 'G4-READY %s\n' "$nonce"

# -t is the BusyBox ash read builtin's timeout, not a POSIX sh extension.
# The host must also enforce the complete trial deadline and capture input.
IFS=' ' read -r -t 20 response_nonce left right extra || fail 'challenge missing or timed out'
[ "$response_nonce" = "$nonce" ] || fail 'challenge nonce mismatch'
[ -z "$extra" ] || fail 'extra challenge fields'
for operand in "$left" "$right"; do
    case "$operand" in ''|0*|*[!0-9]*) fail 'invalid decimal operand' ;; esac
    [ "${#operand}" -le 6 ] || fail 'operand exceeds 999999'
done

# A scheduled sleep, not a wall-clock delay on the host. Timer interrupt and
# uptime deltas are checked independently of the challenge result.
sleep 1
printf 'G4-IRQ-AFTER-BEGIN\n'
cat /proc/interrupts
printf 'G4-IRQ-AFTER-END\n'
printf 'G4-UPTIME-AFTER %s\n' "$(cat /proc/uptime)"
printf 'G4-RESULT %s %s\n' "$nonce" "$((left + right))"
restore_terminal || exit 1
trap - 0
printf 'G4-END %s\n' "$nonce"
