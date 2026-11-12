# notes/ld08b/rig/lib.sh: the take's container runner, sourced by step.sh through GAUNTLET_RIG_DIR
# (the recorder runs a stored copy of step.sh). The rig runs from a clean checkout of the commit
# under test, which need not hold the rig. The host's facts are shell assignments in the file
# LD08_HOST names, kept beside the lane and never in the tree:
#   L        the lane's directory (everything the rig writes outside the tree; TMPDIR is under it)
#   CPUS     the CPUs the take may use, and ONE, one of them, for the single-thread time rows
#   P        the container engine (rootless podman)
#   IMG      the image built from ci/oracle.Containerfile
#   CAPTURE  the captured links, one directory per program (link.json and the files it names)
#   SYSROOT  the sysroot those links name (the runtime and CRT the compiler that made them ships)
#   TRUNK    the trunk commit the rows compare against
: "${LD08_HOST:?LD08_HOST names the host file}"
# shellcheck disable=SC1090
. "$LD08_HOST"
: "${L:?}" "${CPUS:?}" "${ONE:?}" "${P:?}" "${IMG:?}" "${CAPTURE:?}" "${SYSROOT:?}" "${TRUNK:?}"
export TMPDIR=$L/tmp
mkdir -p "$TMPDIR"
CO=$(git rev-parse --show-toplevel)
# ctr CMD...: CMD in the image, in the checkout, on the take's CPUs.
ctr() {
    "$P" run --rm --memory 12g --pids-limit 16384 --ulimit core=0:0 --security-opt label=disable \
        -v "$L:$L" -w "$CO" -e TMPDIR="$CO/target/tmp" -e HOME="$CO/target/tmp" \
        -e WOLF_STD="$CO/.wolf-bin/std" -e LIGATURE_REQUIRE_SELF_LINK=1 \
        "$IMG" taskset -c "$CPUS" "$@" < /dev/null
}
