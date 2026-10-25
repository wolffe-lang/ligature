#!/usr/bin/env bash
# Fresh kernels, unchanged seed-linked corpus bytes, host QEMU, isolated lane images.
set -euo pipefail
base=$HOME/lanes/ld02a
printf '%s\n' "$$" > "$base/pax-matrix.pid"
trap 'rc=$?; printf "%s\n" "$rc" > "$base/pax-matrix.exit"; printf "PAX MATRIX EXIT %s %s\n" "$rc" "$(date -Iseconds)"' EXIT
ulimit -c 0
export TMPDIR="$base/tmp" PAX_BUILD="$base/pax-results"
exec 9>"$HOME/lanes/kasumi-cores-12-15.lock"
printf 'PAX MATRIX START %s kernel_source=%s\n' "$(date -Iseconds)" "$(git -C "$base/pax" rev-parse HEAD)"
for tier in native release; do
    out="$base/pax-results/kernel-$tier"; test ! -e "$out"; mkdir -p "$out"
    flock 9
    podman run --rm --network=none --cpuset-cpus=12-15 --memory=8g -v "$base:$base:rw" -w "$base/pax" localhost/px79-ubuntu:latest bash -c '
        set -euo pipefail
        ulimit -c 0
        export PAX_CACHE=$1/pax-cache
        unset WOLF_STD
        export PAX_WOLF=$(tools/fetch-wolf)
        if [ "$2" = release ]; then flag=--release; else flag=; fi
        tools/build-kernel ${flag:+$flag} --src "$1/pax/kernel/kmain_console.lu" "$1/pax-results/kernel-$2/build"
    ' bash "$base" "$tier" > "$out/build.log" 2>&1
    flock -u 9
    for read in first second; do sha256sum "$out/build/kmain_console.elf" > "$out/kernel-$read.sha256"; done
    cmp "$out/kernel-first.sha256" "$out/kernel-second.sha256"
    cat "$out/kernel-first.sha256"
done
failed=0
for case in "$base"/pax-cases/*; do
    name=${case##*/}; root="$base/pax-results/$name"; test ! -e "$root"; mkdir -p "$root"
    [ "$(du -sm "$base" | cut -f1)" -lt 9500 ] || { echo 'lane disk ceiling reached'; exit 2; }
    flock 9
    taskset -c 12-15 python3 -I "$base/ligature/tools/pax-stage" "$HOME/lanes/ld01/iso-extract/initramfs.cpio" "$case" "$root/initramfs.cpio" > "$root/stage.json"
    cp "$root/initramfs.cpio" "$base/pax-image-root/boot/initramfs.cpio"
    flock -u 9
    for tier in native release; do
        image="$root/$tier.iso"; elf="$base/pax-results/kernel-$tier/build/kmain_console.elf"
        flock 9
        cp "$elf" "$base/pax-image-root/boot/pax"
        # The current PAX tools/mkimage dual-CD recipe, with the baseline dev initramfs.
        podman run --rm --network=none --cpuset-cpus=12-15 -v "$base:$base:rw" localhost/px79-ubuntu:latest xorriso -as mkisofs -R -r -J \
            -b boot/limine/limine-bios-cd.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
            -hfsplus -apm-block-size 2048 --efi-boot boot/limine/limine-uefi-cd.bin -efi-boot-part --efi-boot-image \
            --protective-msdos-label "$base/pax-image-root" -o "$image" > "$root/$tier-image.log" 2>&1
        flock -u 9
        for read in first second; do sha256sum "$image" > "$root/$tier-image-$read.sha256"; done
        cmp "$root/$tier-image-first.sha256" "$root/$tier-image-second.sha256"
        for firmware in bios uefi; do
            out="$root/$tier-$firmware"; mkdir -p "$out"
            printf 'BOOT %s %s %s %s\n' "$name" "$tier" "$firmware" "$(date -Iseconds)"
            flock 9
            hrc=0
            taskset -c 12-15 "$base/pax/tools/qemu-halt" --accel auto --firmware "$firmware" --serial "$out/serial.log" --timeout 240 --qemu -m --qemu 4096M --elf "$elf" --marker 'halt|PANIC .*' "$image" > "$out/halt.log" 2>&1 || hrc=$?
            flock -u 9
            cat "$out/halt.log"
            [ "$hrc" = 0 ] || { printf '{"halt_status":%s,"row_status":null}\n' "$hrc" > "$out/status.json"; exit 1; }
            rrc=0
            taskset -c 12-15 python3 -I "$base/ligature/tests/pax-row.py" "$out/serial.log" "$case" "$out/result.json" > "$out/row.log" 2>&1 || rrc=$?
            printf '{"halt_status":%s,"row_status":%s}\n' "$hrc" "$rrc" > "$out/status.json"
            cat "$out/row.log"
            if [ "$rrc" != 0 ]; then failed=1; fi
            printf 'END %s %s %s halt=%s row=%s\n' "$name" "$tier" "$firmware" "$hrc" "$rrc"
        done
        # qemu-halt joined both QEMU instances; no live image is renamed or removed.
        flock 9
        taskset -c 12-15 gzip -1 "$image"
        taskset -c 12-15 gzip -t "$image.gz"
        flock -u 9
    done
    rm "$base/pax-image-root/boot/initramfs.cpio" # scratch copy; original preserved below
    flock 9
    taskset -c 12-15 gzip -1 "$root/initramfs.cpio"
    taskset -c 12-15 gzip -t "$root/initramfs.cpio.gz"
    flock -u 9
done
printf 'PAX MATRIX completed; raw row failure status=%s (fork remains red unless served)\n' "$failed"
exit "$failed"
