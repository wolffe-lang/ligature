#!/usr/bin/env bash
# Lane-only long job; the orchestrator resumes ld02a after its durable exit marker.
set -euo pipefail
base=$HOME/lanes/ld02a
attempt=${LD02A_ATTEMPT:-long}
printf '%s\n' "$$" > "$base/$attempt.pid"
trap 'rc=$?; printf "%s\n" "$rc" > "$base/$attempt.exit"; printf "LD02A LONG EXIT %s %s\n" "$rc" "$(date -Iseconds)"' EXIT
ulimit -c 0
printf 'LD02A LONG START %s pid=%s head=%s\n' "$(date -Iseconds)" "$$" "$(git -C "$base/ligature" rev-parse HEAD)"
podman run --rm --name ld02a-long --network=none --cpuset-cpus=12-15 --memory=8g --pids-limit=16384 --ulimit nproc=32768:32768 \
  -v "$base:/lane:rw" -v "$HOME/lanes/ld01:/baseline:ro" -v "$HOME/lanes/kasumi-cores-12-15.lock:/lane-cores.lock:rw" -w /lane/ligature localhost/ld00-oracle:latest bash -c '
set -euo pipefail
ulimit -c 0
export WOLF=/baseline/toolchain/wolf/wolf-0.2.35-x86_64-unknown-linux-gnu/wolf
export WOLF_STD=${WOLF%/wolf}/std WOLF_RT_FOR_TEST=${WOLF%/wolf}/libwolf_rt.a
export LIGATURE_LINK_INPUTS=/lane/ligature/.link-inputs
printf "SOURCE GATE %s\n" "$(date -Iseconds)"
flock /lane-cores.lock tools/check
printf "POST-CHANGE TOTAL COST %s\n" "$(date -Iseconds)"
TIMEFORMAT="elapsed=%R user=%U sys=%S"
base=/lane/ligature/.link-inputs
args=(-static -nostdlib --gc-sections --undefined=__wolf_rt_trap_at --defsym=wolf_trap=__wolf_rt_trap_at -o /lane/lazy-hello "$base/sysroot/crt1.o" "$base/sysroot/crti.o" --start-group target/corpus/hello-hello/main.o "$base/libwolf_rt.a" "$base/sysroot/libc.a" "$base/sysroot/libunwind.a" --end-group "$base/sysroot/crtn.o")
for i in 1 2 3; do
 printf "POST-CHANGE LINK %s %s\n" "$i" "$(date -Iseconds)"
 flock /lane-cores.lock bash -c "TIMEFORMAT=\"elapsed=%R user=%U sys=%S\"; { time target/ligature \"\$@\"; } 2> /lane/lazy-link-$i.time" bash "${args[@]}"
 cat /lane/lazy-link-$i.time
 sha256sum /lane/lazy-hello
done
printf "SEED-LINKED CORPUS %s\n" "$(date -Iseconds)"
flock /lane-cores.lock tools/make-corpus
mkdir -p /usr/share/lupin
cp tests/corpus/pax/*.lu /usr/share/lupin/
export LIGATURE_LINKER=/lane/ligature/target/ligature
export LIGATURE_COMPRESS_EVIDENCE=1 LIGATURE_COMMAND_LOCK=/lane-cores.lock
python3 -I -u tests/static-pax.py "$LIGATURE_LINK_INPUTS"
flock /lane-cores.lock python3 -I tools/classify-static target/static-pax /lane/structural-classes.json
printf "LINUX COMPLETE %s\n" "$(date -Iseconds)"
'
du -sh "$base"
