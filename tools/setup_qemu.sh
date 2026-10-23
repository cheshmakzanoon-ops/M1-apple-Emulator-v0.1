#!/bin/sh
set -eu

project_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
qemu_ref=${QEMU_REF:-v11.1.2}
checkout="$project_root/vendor/qemu"
build_dir="$checkout/build-m1"

if [ ! -d "$checkout/.git" ]; then
    mkdir -p "$project_root/vendor"
    git clone --depth 1 --branch "$qemu_ref" https://github.com/qemu/qemu.git "$checkout"
else
    current_ref=$(git -C "$checkout" describe --exact-match --tags HEAD 2>/dev/null || true)
    if [ "$current_ref" != "$qemu_ref" ]; then
        echo "Existing QEMU checkout is not at $qemu_ref; refusing to overwrite" >&2
        exit 2
    fi
fi

mkdir -p "$build_dir"
cd "$build_dir"
../configure --target-list=aarch64-softmmu --enable-debug --disable-werror
echo "Configured QEMU $qemu_ref at $build_dir"
echo "Build with: ninja -C '$build_dir'"
echo "NOTE: no Apple T8103 board is implemented yet"
