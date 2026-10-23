#!/bin/sh
# Read-only Linux v6.12 sysfs serial-binding check. The guest probe passes /sys;
# an explicit alternate root also supports inspection of a captured sysfs tree.
set -eu

fail() {
    printf '\nG4-ERROR serial binding: %s\n' "$1" >&2
    exit 1
}

[ "$#" -eq 1 ] || fail 'expected one sysfs root'
root=$(readlink -f "$1") || fail 'cannot resolve sysfs root'
[ -d "$root/devices" ] || fail 'missing devices directory'
platform_link="$root/bus/platform/devices/235200000.serial"
tty_link="$root/class/tty/ttySAC0/device"
[ -L "$platform_link" ] || fail 'missing physical UART symlink'
[ -L "$tty_link" ] || fail 'missing tty device symlink'
physical=$(readlink -f "$platform_link") || fail 'cannot resolve physical UART'
terminal=$(readlink -f "$tty_link") || fail 'cannot resolve tty device'
[ -d "$physical" ] && [ -d "$terminal" ] || fail 'missing canonical device directory'
case "$physical" in "$root/devices/"*) ;; *) fail 'UART is outside sysfs devices' ;; esac
case "$terminal" in
    "$physical"|"$physical/"*) ;;
    *) fail 'tty device is unrelated to the physical UART' ;;
esac

# Serial-core may insert controller/port children whose own driver is `port`.
# Follow the identified platform device, never a guessed number of ../ hops.
[ -L "$physical/driver" ] || fail 'missing platform driver symlink'
driver=$(readlink -f "$physical/driver") || fail 'cannot resolve platform driver'
[ "$driver" = "$root/bus/platform/drivers/samsung-uart" ] && [ -d "$driver" ] \
    || fail 'physical UART is not bound to samsung-uart'
[ -f "$physical/of_node/compatible" ] || fail 'missing physical UART OF compatible'
compatible=$(tr '\000' '\n' < "$physical/of_node/compatible") || fail 'cannot read UART compatible'
case "
$compatible
" in
    *"
apple,s5l-uart
"*) ;;
    *) fail 'physical UART lacks apple,s5l-uart compatible' ;;
esac
printf '%s\n' "${driver##*/}"
