#!/usr/bin/env bash
# Own images and logs; immutable inherited kernels. Completed boot markers resume safely.
set -euo pipefail
base=$HOME/lanes/ld03
previous=$HOME/lanes/ld02a
printf '%s\n' "$$" > "$base/pax.pid"
trap 'rc=$?; printf "%s\n" "$rc" > "$base/pax.exit"; printf "LD03 PAX EXIT %s %s\n" "$rc" "$(date -Iseconds)"' EXIT
ulimit -c 0
export TMPDIR="$base/tmp" PAX_BUILD="$base/pax-results"
mkdir -p "$TMPDIR" "$PAX_BUILD" "$base/pax-image-root/boot/limine" "$base/pax-tools/tools"
cp "$previous/pax/tools/"{qemu-halt,qemu-run,lib.sh} "$base/pax-tools/tools/"
cp "$previous/pax-image-root/boot/limine/"* "$base/pax-image-root/boot/limine/"
exec 9>"$HOME/lanes/kasumi-cores-12-15.lock"
failed=0
printf 'LD03 PAX START %s reused kernels from edbd385c91f2ff0eadb1ab4e52b276f1a1412b63\n' "$(date -Iseconds)"
for case in "$base"/pax-cases/*; do
    name=${case##*/}; root="$PAX_BUILD/$name"; mkdir -p "$root"
    # A case with four durable markers is never booted again on a restart.
    if [ -f "$root/native-bios/complete.json" ] && [ -f "$root/native-uefi/complete.json" ] && [ -f "$root/release-bios/complete.json" ] && [ -f "$root/release-uefi/complete.json" ]; then
        for tier in native release; do
            for firmware in bios uefi; do
                flock 9
                taskset -c 12-15 python3 -I "$base/ligature/notes/ld03/pax-checkpoint.py" --verify "$root/$tier-$firmware" "$case" "$previous/pax-results/kernel-$tier/build/kmain_console.elf" "$root/$tier.iso"
                flock -u 9
            done
        done
        printf 'RESUME completed %s\n' "$name"; continue
    fi
    flock 9
    if [ ! -f "$root/initramfs.cpio" ]; then
        if [ -f "$root/initramfs.cpio.gz" ]; then
            gzip -dc "$root/initramfs.cpio.gz" > "$root/initramfs.cpio"
        else
            taskset -c 12-15 python3 -I "$base/ligature/tools/pax-stage" "$HOME/lanes/ld01/iso-extract/initramfs.cpio" "$case" "$root/initramfs.cpio" > "$root/stage.json"
        fi
    fi
    taskset -c 12-15 python3 -I -c 'import hashlib,json,pathlib,sys; r=pathlib.Path(sys.argv[1]); assert hashlib.sha256((r/"initramfs.cpio").read_bytes()).hexdigest()==json.loads((r/"stage.json").read_text())["cpio_sha256"]' "$root"
    cp "$root/initramfs.cpio" "$base/pax-image-root/boot/initramfs.cpio"
    flock -u 9
    for tier in native release; do
        image="$root/$tier.iso"; elf="$previous/pax-results/kernel-$tier/build/kmain_console.elf"
        flock 9
        if [ ! -f "$image" ] && [ -f "$image.gz" ]; then gzip -dc "$image.gz" > "$image"; fi
        if [ ! -f "$image" ]; then
        cp "$elf" "$base/pax-image-root/boot/pax"
        podman run --rm --network=none --cpuset-cpus=12-15 -v "$base:$base:rw" localhost/px79-ubuntu:latest xorriso -as mkisofs -R -r -J \
            -b boot/limine/limine-bios-cd.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
            -hfsplus -apm-block-size 2048 --efi-boot boot/limine/limine-uefi-cd.bin -efi-boot-part --efi-boot-image \
            --protective-msdos-label "$base/pax-image-root" -o "$image" > "$root/$tier-image.log" 2>&1
        fi
        flock -u 9
        sha256sum "$image" > "$root/$tier-image-first.sha256"
        sha256sum "$image" > "$root/$tier-image-second.sha256"
        cmp "$root/$tier-image-first.sha256" "$root/$tier-image-second.sha256"
        for firmware in bios uefi; do
            out="$root/$tier-$firmware"; mkdir -p "$out"
            if [ -f "$out/complete.json" ]; then
                flock 9
                taskset -c 12-15 python3 -I "$base/ligature/notes/ld03/pax-checkpoint.py" --verify "$out" "$case" "$elf" "$image"
                flock -u 9
                continue
            fi
            printf 'BOOT %s %s %s %s\n' "$name" "$tier" "$firmware" "$(date -Iseconds)"
            flock 9
            hrc=0
            taskset -c 12-15 "$base/pax-tools/tools/qemu-halt" --accel auto --firmware "$firmware" --serial "$out/serial.log" --timeout 240 --qemu -m --qemu 4096M --elf "$elf" --marker 'halt|PANIC .*' "$image" > "$out/halt.log" 2>&1 || hrc=$?
            flock -u 9
            cat "$out/halt.log"
            [ "$hrc" = 0 ] || { printf '{"halt_status":%s,"row_status":null}\n' "$hrc" > "$out/status.json"; exit 2; }
            rrc=0
            taskset -c 12-15 python3 -I "$base/ligature/tests/pax-row.py" "$out/serial.log" "$case" "$out/result.json" > "$out/row.log" 2>&1 || rrc=$?
            printf '{"halt_status":%s,"row_status":%s}\n' "$hrc" "$rrc" > "$out/status.json"
            cat "$out/row.log"
            taskset -c 12-15 python3 -I "$base/ligature/notes/ld03/pax-checkpoint.py" "$out" "$case" "$elf" "$image"
            if [ "$rrc" != 0 ]; then failed=1; fi
            printf 'END %s %s %s halt=%s row=%s\n' "$name" "$tier" "$firmware" "$hrc" "$rrc"
        done
        flock 9
        taskset -c 12-15 gzip -1 -f "$image"
        taskset -c 12-15 gzip -t "$image.gz"
        flock -u 9
    done
    rm "$base/pax-image-root/boot/initramfs.cpio"
    flock 9
    taskset -c 12-15 gzip -1 -f "$root/initramfs.cpio"
    taskset -c 12-15 gzip -t "$root/initramfs.cpio.gz"
    flock -u 9
    printf 'CASE COMPLETE %s\n' "$name"
done
# Read the durable statuses, including skipped cases, rather than forgetting prior fork reds.
if grep -q '"row_status":1' "$PAX_BUILD"/*/*/status.json; then failed=1; fi
printf 'LD03 PAX MATRIX COMPLETE raw-status=%s (named fork reds remain red)\n' "$failed"
exit "$failed"
