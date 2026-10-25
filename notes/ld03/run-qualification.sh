#!/usr/bin/env bash
# Detached lane qualification; the orchestrator resumes ld03 at the durable marker.
set -euo pipefail
base=$HOME/lanes/ld03
printf '%s\n' "$$" > "$base/qualification.pid"
trap 'rc=$?; printf "%s\n" "$rc" > "$base/qualification.exit"; printf "LD03 EXIT %s %s\n" "$rc" "$(date -Iseconds)"' EXIT
ulimit -c 0
printf 'LD03 START %s pid=%s\n' "$(date -Iseconds)" "$$"
podman run --rm --name ld03-qualification --cpuset-cpus=12-15 --memory=8g --pids-limit=16384 --ulimit nproc=32768:32768 \
  -v "$base:/lane:rw" -v "$HOME/lanes/ld02a:/previous:ro" \
  -v "$HOME/lanes/kasumi-cores-12-15.lock:/lane-cores.lock:rw" -w /lane/ligature ligature-oracle bash -c '
set -euo pipefail
export CARGO_INCREMENTAL=0 WOLF=$PWD/.wolf-bin/wolf WOLF_STD=$PWD/.wolf-bin/std
export WOLF_RT_FOR_TEST=$PWD/.wolf-bin/libwolf_rt.a LIGATURE_LINK_INPUTS=$PWD/.link-inputs
printf "FULL GATE %s\n" "$(date -Iseconds)"
flock /lane-cores.lock tools/check
printf "FULL GATE PASSED %s\n" "$(date -Iseconds)"
flock /lane-cores.lock tools/make-corpus
mkdir -p /usr/share/lupin
cp tests/corpus/pax/*.lu /usr/share/lupin/
export LIGATURE_COMPRESS_EVIDENCE=1 LIGATURE_COMMAND_LOCK=/lane-cores.lock
printf "LINUX CORPUS START %s\n" "$(date -Iseconds)"
python3 -I -u tests/static-pax.py "$LIGATURE_LINK_INPUTS"
flock /lane-cores.lock python3 -I tools/classify-static target/static-pax notes/ld03/current-structural-classes.json
flock /lane-cores.lock python3 -I notes/ld03/measure-manifest.py /previous/ligature/target/static-pax/hello-hello/program.gz target/static-pax/hello-hello/program
printf "LINUX CORPUS COMPLETE %s\n" "$(date -Iseconds)"
'
du -sh "$base"
