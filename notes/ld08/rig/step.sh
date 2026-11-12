#!/usr/bin/env bash
# notes/ld08/rig/step.sh NAME: one step of the lane's gauntlet (gauntlet.manifest), run by the
# recorder from the checkout under test. Every step but the trunk source's export runs in the
# repository's own oracle image.
set -uo pipefail
# shellcheck disable=SC1091
. "$GAUNTLET_RIG_DIR/lib.sh"
mkdir -p target/tmp
captured=(--sysroot "$SYSROOT")
for row in hello:192 netproc:192 pelt:256 ligself:192; do
    captured+=(--captured "$row:$CAPTURE/${row%%:*}")
done
case $1 in
    fetch-toolchain) ctr tools/fetch-toolchain ;;
    fetch-bundle) ctr python3 -I tools/fetch-bundle ;;
    trunk-build)
        # Trunk's source from this repository's own history, built by the pinned compiler.
        rm -rf target/trunk-src && mkdir -p target/trunk-src || exit 1
        git -c commit.gpgsign=false archive "$TRUNK" src | tar -x -C target/trunk-src || exit 1
        echo "trunk $TRUNK tree $(git rev-parse "$TRUNK^{tree}")"
        ctr bash -c '.wolf-bin/wolf build --no-cache --deny-warnings target/trunk-src/src/ligature.lu \
            -o target/trunk-ligature && sha256sum target/trunk-ligature'
        ;;
    build) ctr bash -c 'tools/build && sha256sum target/ligature' ;;
    core) ctr tools/check-core ;;
    real-ligature) ctr python3 -I tests/real-ligature.py ;;
    self-link) ctr python3 -I tests/self-link.py ;;
    link-cost) ctr python3 -I tests/link-cost.py ;;
    link-memory) ctr python3 -I tests/link-memory.py --baseline target/trunk-ligature "${captured[@]}" ;;
    time-rows)
        ctr taskset -c "$ONE" python3 -I "$GAUNTLET_RIG_DIR/time-rows.py" --capture "$CAPTURE" \
            --sysroot "$SYSROOT" --rounds 3 target/trunk-ligature target/ligature
        ;;
    identity-suite) ctr python3 -I "$GAUNTLET_RIG_DIR/identity-suite.py" target/trunk-ligature ;;
    *)
        echo "step.sh: no step $1"
        exit 64
        ;;
esac
