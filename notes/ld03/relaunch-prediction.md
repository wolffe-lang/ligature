# ld03, relaunched 2026-11-09: the prediction

Written before any change, from trunk `6cec81a741fed8c25ad7178a5c295b3eb338aa26` and a read-only
build probe of that commit on macOS arm64 (`~/lanes/ld03/mac-build-probe.log`).

## What the tree already holds (facts at trunk, not predictions)

The first ld03 pass merged as ligature#22 (`b2615dd3`, 2026-10-25) and ld04 to ld07 merged after it.
At trunk, M3's items stand as follows:

- The provenance manifest: measured at 147,136,512 bytes of JSON for hello's 590,358 retained sites
  (249.2 bytes per site), then the interned binary table `WLPATCH2` inside `.wolf.link.manifest`,
  sealed by the unchanged 116-byte `.note.wolf.link`: 12,414,976 bytes, 21.0 bytes per site, 11.85x,
  every patch record equal field by field, 17,765 discard records made explicit, an independent
  encoder reproducing the bytes (`notes/ld03/measurement-before.json`, `measurement-after.json`).
  R-ld03-1 was recommended as option A on those sizes and is still unruled in the campaign index.
- `explain --symbol | --address | --why | --dependencies | --discarded` (`src/explain/explain.lu`),
  reading both manifest forms; the gate's "explanation queries" row.
- Determinism as a test: byte-identical relinks in the self-link row (first = second = bootstrap
  third), deterministic relinks across the fourteen Linux cases, and the writer's
  `strong-weak ligature nondeterministic` row.
- The 87 findings (28 symbols, 28 segments, 28 relocations, 3 GNU TLS): each retained by name with
  the deciding specification clause and a decision, 0 resolved, 0 waivers (`notes/ld03/findings.json`);
  `tools/check-findings` holds every one to ld02a's baseline record identity.
- The kernel subset's plan: `notes/ld03/ld04-draft.json`, since implemented by ld05 (PAX paging
  kernels boot under BIOS and UEFI from ligature's output).
- The self-link: live since the 0.2.36 pin (r41p) and the republished bundle (ld06); CI requires it
  to pass (`LIGATURE_REQUIRE_SELF_LINK=1`). The old BLOCKED admission for the 0.2.35 runtime digest
  `9d859b9e…` is still in `tests/self-link.py`, now vestigial.

So the relaunch's work is the pin, the self-link at that pin, the findings and the manifest measured
at that pin, the plants, and the note. The ld02a inputs this contract names are all in the tree.

## The pin, read twice

Every digest below was read twice on the Mac (`~/lanes/ld03/rel-0.2.38/sums.twice.txt`) and equals
the release page where the page states it.

| pin | value |
|---|---|
| wolf 0.2.38 | tag commit `95ae0827a8ad4d0bbed9302df7811caaa7009fa1`; version line `wolf 0.2.38 (wolfgang, pin 95ae082)` |
| `aarch64-apple-darwin` | `66a2c31324e9e4c4cbb6f103e4014e36b400366c198598b67c71491a65cffba4` |
| `x86_64-unknown-linux-gnu` | `8447a57944da67ba8e76f5b4e88c2f38a32f39466f44b65e5817dcc276394f39` |
| `aarch64-unknown-linux-gnu` | `e0a6763095cf99cb60a18f260966c96dd62be826076aa0ea22e4ad4f141a60e6` |
| lupin 0.1.60 | tag commit `17bd522382373b361fe035a5cc61f9e136e1caba`; `lupin 0.1.60 (wolf-interp, reference interpreter at pin 5f1f1c9)` |
| `aarch64-apple-darwin` | `f3cae16fdb88a94702c0fd816d5eb90cdc8e8636c028dcf40f03868c5dc36bb8` |
| `x86_64-unknown-linux-gnu` | `e7d4c4f1534736c9262f4ccd01a631f03ff70e3b8122eefe6e9ec1e15c02637e` |
| `aarch64-unknown-linux-gnu` | `dc19e519c77e3b830965ba1516cecf3ef0097d658bc8dfd12ae96f2693d3373c` |
| wolf-std | `d4a4d4cab358e1e8c174f0206f9e13ad5cfe6c61` (the release's bundled std) |
| wolf-rt 0.2.38 musl archive | `486f54735c18a352ae20eb7a7c2bbc3c7d245ca1be488841727d1e4ca6bfa125` |
| its `libwolf_rt.a` | `37252e1d0d97d917bc19e95f27d8304b8da3d31afd7a2120395e0c9a87bbc740`, 47,350,818 bytes (0.2.36's was 46,700,882) |

No `link-bundle-wolf-0.2.38` release exists on ligature (2026-11-09 18:00Z: `link-bundle-wolf-0.2.36`
and `link-bundle-2026-10-25` only). The bundle is coupled to the runtime pin: `tests/bundle-smoke.py`
requires the bundle's `libwolf_rt.a` to equal `[wolf-rt].libwolf_rt`, and `link-cost`, `link-memory`,
`real-ligature`, `static-pax`, `tools/oracle` and `tools/census` link the pinned compiler's objects
against the bundle's copy of the runtime, while `self-link` and `musl-argv` link against the
`[wolf-rt]` copy. Moving `[wolf]` and `[wolf-rt]` to 0.2.38 under the 0.2.36 bundle therefore puts
0.2.38 objects against a 0.2.36 runtime in six rows, the mismatch #962/#963 taught (one release for
objects and runtime), and `bundle-smoke` goes red by digest. That is R-ld03-2 below.

## The probe (read-only, trunk, macOS arm64)

| compiler | `fmt --check src` | `test --deny-warnings --json src` | `build --deny-warnings src/ligature.lu` | binary sha256 |
|---|---|---|---|---|
| 0.2.36 (`5adf3d9`) | exit 0 | 7 passed, 0 failed, 2 native | exit 0, 1 s | `74f82165…6a08a` |
| 0.2.38 (`95ae082`) | exit 0 | 7 passed, 0 failed, 2 native | exit 0, 1 s | `bb60367c…2759f` |

0.2.38's new W0801 (a binder spelling a variant) and E0806 do not fire on ligature's sources, so the
pin move needs no source change for the compiler.

## Predicted rows

1. **The pin commit** (`wolf-toolchain.toml`, `tools/fetch-musl-runtime`'s docstring, the two tests
   that spell the asset names: `tests/fetch-musl-runtime.py`, `tests/licensed-bundle.py`):
   `tools/fetch-toolchain` prints each 0.2.38 archive digest twice, `.wolf-bin/wolf --version` is
   `wolf 0.2.38 (wolfgang, pin 95ae082)`, and `tools/fetch-musl-runtime` prints `486f5473…` and
   `37252e1d…` twice. Footprint: cross-cutting (a pin).
2. **`check-core` at 0.2.38:** every row green as at 0.2.36, the Linux build of `target/ligature` a
   new sha256 (the compiler changed), `roundtrip` of the public 0.2.38 glibc runtime green.
3. **`self-link` at 0.2.38 against the 0.2.38 musl runtime:** `musl-argv` prints `argc=3` under both
   lld and GNU ld (exit 0, not the BLOCKED 2); the object set is the same 24 modules; first = second
   = third byte for byte; the self-linked linker prints `ligature 0.0.2 …` and links a hello that
   prints `hello, wolf`. The one named risk: the 0.2.38 runtime's archive (hashed Map, the descriptor
   walk, `.debug_frame` on `-g`) brings a relocation type or section flag outside the measured set,
   which ligature refuses by name. Predicted: no; the runtime is built by the same rust 1.97.1 with
   the same flags, so the 13 encodings and the section classes of `docs/MAP.md` hold. A refusal
   here is a finding to name, not a guess to patch.
4. **The bundle rows** (`stage-bundle`, `licensed-bundle`, `bundle-smoke`, `real-ligature`,
   `link-cost`, `link-memory`): under the recommended R-ld03-2 A, a 0.2.38 bundle staged by
   `tools/stage-bundle` from the 0.2.36 bundle's seven unchanged binaries plus the 0.2.38 runtime and
   the notices with the runtime's source row updated, pinned by its digest and MANIFEST digest in
   `tools/fetch-bundle` and `tests/pax-link.sums`: all green, `bundle-smoke` executing hello under
   both the bundle's `cc`+lld and ligature. Before the release exists, `tools/fetch-bundle` refuses
   (404 or digest), so CI's `linux` job is red until the orchestrator publishes the staged archive;
   the local record runs on the staged archive through a local-path override added to
   `tools/fetch-bundle` (the same verification, no network; `tests/fetch-bundle.py` still proves the
   digest refusal). Without that ruling, the rows go red by digest at `bundle-smoke` (the pin and
   the bundle's runtime differ), which is the coupling made visible, not a pass.
5. **`link-cost`:** the frozen relocation control compiles under 0.2.38 as `src` does; candidate at
   most half the same run's baseline; hello and self-link outputs byte-identical between control
   and candidate.
6. **`link-memory`:** hello and `str` against the 47.35 MB runtime (1.4 % larger than 0.2.36's) stay
   under 1 GiB resident (ld07 measured 0.615 and 0.618 GiB at 0.2.36; predicted within +3 %), and
   the N/10N/100N archives stay linear.
7. **The findings gate:** `tools/check-findings` and `tests/findings.py` unchanged and green: the
   87 are held to ld02a's baseline identities, which the pin does not touch. A fresh classification
   of the 0.2.38 corpus is R-ld03-4; predicted, if run: the same four kinds with different counts,
   every name present in the baseline's 87 (the same fourteen cases against the same two oracles),
   none resolved, since ligature's layout freedom and retained-relocation policy did not change.
8. **The manifest at 0.2.38:** hello's retained sites move with the runtime, predicted within ±5 %
   of 590,358; the table's bytes per site stay 21.0 ± 0.5; the legacy JSON form is read-only now, so
   its size at 0.2.38 is derived from the decoded model under `docs/FORMATS.md`'s legacy rules and
   labelled derived; the ratio stays between 11 and 12.5.
9. **Determinism:** two links of the self-link objects and of hello byte-identical; the change of
   one input (the runtime 0.2.36 → 0.2.38 at the same objects) moves bytes only in ranges the
   manifest attributes to runtime members; the blast-radius row is read from the manifest, not asserted
   by hand.
10. **The vestigial BLOCKED admission** (R-ld03-3): retiring it leaves `tests/self-link.py` with one
    outcome, PASS or a named failure; `tests/self-link-blocker.py` becomes the witness that no digest
    is admitted; CI unchanged (it already demanded PASS).
11. **Plants, three, red by name in a plant record on hasu, off the line:** a provenance record
    dropped (`lazy-order: provenance retained patch count mismatch`), a finding's record reclassified
    (`check-findings: … retained finding silently reclassified`), a nondeterministic relink
    (`writer: strong-weak ligature nondeterministic`).
12. **README:** the 0.2.36 sentences (lines 17, 94–98, 132–152, 207 at trunk) refreshed in a
    README-only commit; `docs/SOURCES.md`'s bundle and runtime rows likewise.

## Rulings asked (recommendations, implemented as recommended unless ruled otherwise)

- **R-ld03-1, the manifest's form** (unchanged from the first pass, with the sizes above): (A) the
  interned binary table inside the existing note envelope, recommended, 11.85x measured; (B)
  compressed JSON; (C) a sidecar file.
- **R-ld03-2, the 0.2.38 bundle:** (A) stage `link-bundle-wolf-0.2.38` with `tools/stage-bundle`
  (the seven 0.2.36 binaries unchanged, the 0.2.38 runtime, the notices' runtime row updated), hand
  the archive and its digest to the orchestrator for publication, pin by digest; recommended, the
  path ld06 took for 0.2.36. (B) decouple the six rows from the bundle's runtime copy and keep the
  0.2.36 bundle; no public step, but the bundle stops being the whole PAX link set. (C) the
  contract's fallback: everything stays at 0.2.36 and this lane reports the missing bundle.
- **R-ld03-3, the BLOCKED admission:** (A) retire it now that the self-link is live, recommended;
  (B) keep it.
- **R-ld03-4, the findings at the new pin:** (A) a fresh classification run on hasu, recorded as
  evidence with each name resolved or retained against the baseline's 87, the baseline gate
  unchanged, recommended; (B) the baseline only; (C) replace the baseline with the 0.2.38 table.
- **R-ld03-5, the branch:** `ld03` and `ld03-plant-*` already exist on origin from ligature#22,
  all in trunk. (A) branch `ld03b` and `ld03b-plant-*`, recommended; (B) force-push `ld03`.
