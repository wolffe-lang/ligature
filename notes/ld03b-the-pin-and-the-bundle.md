# ld03b — the pin, the self-link at it, and the 0.2.38 bundle (relaunch of ld03, 2026-11-09)

The first ld03 pass merged as ligature#22 (`b2615dd3`, 2026-10-25): the compact manifest, `explain`,
the determinism rows, the 87 named findings and the kernel subset's plan are in the tree and
summarised in `notes/ld03-the-explainable-link.md`. This pass moves the toolchain pin to wolf 0.2.38,
stages the matching link bundle (published since as `link-bundle-wolf-0.2.38`), keeps the self-link
live at that pin, retires the last admitted self-link outcome, holds hello's link identity per pin,
and measures the 87 findings and the manifest at the new pin. The prediction is
`notes/ld03/relaunch-prediction.md`, committed first at `2fd5b29`.

Footprint: cross-cutting

## Prediction

Twelve rows, written before the first change (`notes/ld03/relaunch-prediction.md`). Scored below:
rows 1, 7, 8, 9 (the pin, the findings gate, the manifest, determinism) from the classification
record in this directory; rows 2–6 and 10 (check-core, self-link, the bundle rows, link-cost,
link-memory, the retired admission) by the lane's green record at the final head, quoted in the
hand-back and the PR; row 11 by the plant records; row 12 by the README and SOURCES commits.
Two rows moved: hello's retained sites grew 6.4 % (predicted within ±5 %), and the pin needed two
test changes the prediction did not name (hello's census identity and link-cost's ratio, below).

## Forbidden

ligature's clean room (never any linker's source; GNU ld and lld black-box; the ELF gABI, the AMD64
psABI); no wolf-lang or pax change; no label, merge, tag, release or issue action by the lane (the
release that publishes the staged bundle was made from the staged bytes, outside this branch); no
attribution trailers; nothing in `/tmp`; no commit signed on the build host.

## Inputs verified

- wolf 0.2.38 (tag commit `95ae0827a8ad4d0bbed9302df7811caaa7009fa1`): `aarch64-apple-darwin`
  `66a2c31324e9e4c4cbb6f103e4014e36b400366c198598b67c71491a65cffba4`, `x86_64-unknown-linux-gnu`
  `8447a57944da67ba8e76f5b4e88c2f38a32f39466f44b65e5817dcc276394f39`, `aarch64-unknown-linux-gnu`
  `e0a6763095cf99cb60a18f260966c96dd62be826076aa0ea22e4ad4f141a60e6`; each hashed twice on the Mac
  and twice more by `tools/fetch-toolchain` in every Linux take; the darwin binary prints
  `wolf 0.2.38 (wolfgang, pin 95ae082)`.
- lupin 0.1.60 (tag commit `17bd522382373b361fe035a5cc61f9e136e1caba`): `f3cae16f…6bb8` darwin,
  `e7d4c4f1…637e` x86_64 Linux, `dc19e519…373c` aarch64 Linux, each read twice; no gate runs lupin.
- wolf-std `d4a4d4cab358e1e8c174f0206f9e13ad5cfe6c61`, the release's bundled std.
- wolf-rt 0.2.38 musl: archive `486f54735c18a352ae20eb7a7c2bbc3c7d245ca1be488841727d1e4ca6bfa125`,
  `libwolf_rt.a` `37252e1d0d97d917bc19e95f27d8304b8da3d31afd7a2120395e0c9a87bbc740` (47,350,818
  bytes), read twice, equal to the release page and to the archive's `SHA256SUMS`. Its `LICENSE` and
  `LICENSE-EXCEPTION` are byte-identical to the 0.2.36 archive's (`3972dc97…6986`, `a0eec20d…4fec4`).
- The 0.2.36 link bundle `8210ac22…3e37a` (MANIFEST `8bcea757…7886`), fetched and verified twice by
  `tools/fetch-bundle`; its seven control and sysroot binaries are the 0.2.38 bundle's, unchanged.
- The 0.2.38 bundle: `musl-link-bundle-sha256-4cff0af6a27d200def3651bf3caee77f9bd9452be715ce878e2f0197a0516a36.tar.gz`,
  36,613,546 bytes, MANIFEST `ef3261a0f7c05082c949945d259d7896ab9ce340c083ef76a0be834f40c69950`, 38
  members; staged twice by `tools/stage-bundle` to the same bytes; hashed twice on macOS arm64 and on
  the Linux build host; published as release `link-bundle-wolf-0.2.38` (2026-11-09 19:04Z) with the same digests; the
  green record fetches it from the release and from the staged copy, both through the same checks.
- Baseline findings: `notes/ld02a/evidence/structural-classes-v2.json` (87 names), unchanged.
- Trunk `6cec81a7` builds under 0.2.36 and 0.2.38 alike on macOS arm64 (`fmt --check` 0; `test
  --deny-warnings` 7 passed, 0 failed; `build --deny-warnings` 0), so the pin needed no source change.

## Evidence index

### The classification at the pin (the Linux build host, `classification-0d34aaef.log`)

One take of the fourteen Linux cases at head `0d34aaef`, inside `ci/oracle.Containerfile`'s image, the
0.2.38 compiler and runtime, the 0.2.38 bundle's sysroot and lld 17.0.6 and GNU ld 2.42 as oracles:
every step `exit=0` (fetch-toolchain 8 s, fetch-bundle 2 s, build 3 s, make-corpus 0 s, static-pax
1570 s, classify-static 118 s, compare-findings 0 s, manifest-measure 8 s). `static-pax-results-0.2.38.json`:
14 rows, 0 functional failures, every case behaviour-equal under ligature, lld and GNU ld,
deterministic across two links and verified; 84 structural records.

**The 87 findings at the pin** (`findings-0.2.38.json`, from `structural-classes-0.2.38.json` against
the baseline's 87 names; no waiver): **84 retained, 3 resolved, 0 new, 0 not measured.**
- Retained: 28 symbols, 28 segments, 28 relocations, each by name with the baseline's facts beside
  the fresh ones. The 28 segment findings have facts equal to the baseline's; the symbol and
  relocation findings keep their kind with changed counts (the 0.2.38 runtime's objects), as predicted.
- Resolved: `compiler-procs/gnu/tls`, `pax-host/gnu/tls`, `pax-spawn/gnu/tls`. At 0.2.35 each recorded a
  TLS variable ordering different from GNU ld's with equal normalised initialisers; at 0.2.38 no TLS
  difference is recorded for those cases against GNU ld. The resolution is the runtime's TLS layout
  meeting GNU ld's, not a linker change: `src/` is unchanged since the 0.2.36 pin for this row.
- The baseline gate (`tools/check-findings`, `tests/findings.py`) is unchanged and green: the 87 stay
  held to ld02a's record identities; this table is evidence beside it, not a second gate, as decided.

**The manifest at the pin** (`manifest-0.2.38.json`, hello linked against the 0.2.38 runtime): 628,047
retained sites (590,358 at 0.2.35: +6.4 %, outside the predicted ±5 %), 18,171 discard records; the
`WLPATCH2` table is 12,984,320 bytes (20.67 bytes per site; predicted 21.0 ± 0.5), reproduced by the
independent encoder; the legacy JSON form, derived from the decoded model under `docs/FORMATS.md`'s
rules since the writer no longer emits it, would be 159,268,864 bytes (253.6 per site): a ratio of
12.27 (predicted 11–12.5; 11.85 at 0.2.35). Two reads of the file and of the table agree.

### Hello's identity: the red, the fix, the open question

- The first take at `be8bd052` (`classification-red-hello-identity-be8bd052.log`) ran hello behaviour-equal,
  deterministic and verified, then failed `tests/static-pax.py`'s census constant: ligature pulled
  `libc.a` 328 / `libwolf_rt.a` 32 / `libunwind.a` 5 members where the 0.2.35 census said 322; the
  defined-globals constant (401) would have failed next. LLD's own `--trace` at 0.2.38 extracts exactly
  the same member set (empty set difference both ways), and its `nm -g --defined-only` defines exactly
  the same 396 names as ligature's hello. The six libc members new since 0.2.35 are `getpriority`,
  `mkdirat`, `rewinddir`, `setpriority`, `statvfs` and `symlinkat`, demanded by the 0.2.38 runtime's
  members; gone from the globals are `__wolf_rt_stack_start`, the `pthread_attr_*`/`pthread_self`/
  `thrd_current` set and three crate-hash-renamed names, new are `__wolf_rt_main_start`,
  `term::restore_now` and the renamed three. So the row was the pin's census, not ligature's behaviour.
- Red first (`120e3b3`): `tests/fixtures/hello-identity.json` holds the identity per runtime pin, keyed
  by the `libwolf_rt.a` digest, the 0.2.35 entry copied from the M0 census and the 0.2.38 entry taken
  from LLD's trace and nm, with `tests/hello-identity.py` in check-core failing by name against the old
  runner; then (`57ae338`) `static-pax.py` reads the entry for the runtime it linked and refuses an
  unmeasured runtime by name. At `0d34aaef` hello's row records `hello_identity`: 32/328/5, 396 names,
  equal, runtime `37252e1d…`.
- **The merge condition and a reproducibility question.** Between the red take and the fix head,
  `git diff --stat be8bd052..0d34aaef -- src/` is empty. The ligature binary built at `0d34aaef`
  nonetheless hashed differently from the red take's: `f5cab72ccc6c74da586699d76ffa6485b126763389fb960a53be46f1c1377c6b`
  (worktree `classify-be8bd052`), `a97ff9e0f5191f98298b1fe2c12176c7f428b3d6224c2c275913980774d63187`
  (worktree `hello-0d34aaef`), `17589dca4f2e20439c09cb792df7566813f544894d7b554bfeb8fec63280a7cf`
  (worktree `classify-0d34aaef`): the same compiler, the same sources, three directories, three
  binaries. Hello's output also differed between the two takes at `0d34aaef` (`4161ecf2…` and
  `4ece818c…`) with an identical site count and table size and a 383-byte difference in the table's
  used bytes, which points at strings whose length follows the directory path, in the compiled
  objects and so in the link's inputs, not at the linker (ligature's own determinism rows, two links
  of the same inputs, passed in every take). This is named here as open, not explained: a minimal
  witness (one source compiled in two directories with the pinned compiler, the objects compared) is
  the next step, and belongs to the compiler's repository as an issue to file, listed below. Because
  of it, a record merged from two takes was voided (kept beside the lane's records with a `VOID.txt`),
  and the classification above is one take at one head.

### The rest

- Mac probe of trunk under both compilers: `notes/ld03/relaunch-prediction.md`, "The probe".
- The lane's green record at the final head, on the Linux build host's CPU block with its three locks,
  holds every `END … exit=` line for fetch-toolchain, fetch-bundle from the release and from the staged
  archive, the pins, check-core, real-ligature, self-link, link-cost, link-memory and bundle-smoke; its
  path and lines are in the hand-back and the PR. The plant records hold the three named reds.

### link-cost at the pin: the ratio's premise went with the runtime

- The first green take at `a5909ac0` (`green-red-link-cost-a5909ac0.log`) was green through self-link and
  red at `link-cost`: `FAIL link-cost-hello: ratio=0.976342 bound=0.50`, the frozen control linking hello
  in 8.83 s against the candidate's 8.62 s, byte-identical. ld07's record at trunk `6cec81a7` (wolf
  0.2.36, the same block, 2026-11-04) had 269.05 s against 7.86 s, ratio 0.029.
- Five measurements on one host and block, the same frozen control file (`950485ee…`), block, slot and
  light locks held, differing only in the pin (`diagnose-link-cost/`): at wolf 0.2.38 with its runtime
  and bundle, control 8.575 / 8.676 / 8.701 s, candidate 8.386 / 8.418 / 8.646 s, ratios 0.978 /
  0.970 / 0.994; at trunk `6cec81a7` with wolf 0.2.36 and its runtime and bundle, control 216.337 /
  216.583 s, candidate 7.612 / 7.693 s, ratios 0.0352 / 0.0355; every pair byte-identical. The
  candidate's time is the same at both pins; the control's fell 25×.
- Why: the frozen control is ligature's original relocation lookup, which leaned on the runtime's `Map`,
  and `docs/SOURCES.md` recorded that its slowness was the pinned runtime's Map scanning linearly. wolf
  0.2.38's runtime (s280) finds Map keys through a hashed index behind the same entry points, so at this
  pin the control no longer scans and the ratio tends to 1 by construction. The row was not measuring
  a loaded host (both linkers would slow alike) and ligature's index did not slow down.
- The decision: the row keeps byte identity as its assertion (the original lookup and the current index
  must write the same executable, for hello and for the linker's own objects) and records both times
  without a bound; no straw-man control, no loosened bound. Red first is the record above at the
  unchanged row.
- **What guards time complexity now, by reading:** `link-memory-scaling` (`tests/link-memory.py`) bounds
  `seconds` as well as `resident_peak` at each 10× step of N/10N/100N synthetic archive members (≤ 15×,
  best of two runs). Each synthetic member carries relocations that grow with N (`lea d{i}(%rip)`,
  `.quad f{i}`, a `call f{i}`, plus one `call` per member in the entry object), and
  `src/provenance/attribution.lu` performs one `layout.site_lookup` per live relocation, so a lookup
  regressed to a linear scan makes the link quadratic in its relocations and the 400 → 4000 step costs
  about 100× against the 15× bound: `link-memory-scaling` is the row that fails. The unit test
  `src/relocation_index_test.lu` guards the index's answers and capacity, not its time.

## Done-when

- [x] Prediction committed before the change (`2fd5b29`).
- [x] The pin moved to 0.2.38 by digest (`f055af0`); the bundle staged and pinned (`3afd866`), published.
- [x] The admitted BLOCKED digest retired, red first (`3120760`, then `3afd866`).
- [x] Hello's identity held per pin, red first (`120e3b3`, then `57ae338`).
- [x] The 87 findings measured at the pin, each by name (84 retained, 3 resolved), as evidence.
- [x] The manifest measured at the pin (12.27x derived; 20.67 bytes per site).
- [x] README read and refreshed (`7693910`, `0d34aae`); SOURCES (`be8bd05`) and MAP (`0d34aae`).
- [ ] The self-link PASS at 0.2.38 and every other row in the green record at the final head.
- [ ] Three plants red by name in the plant records.
- [ ] The PR open, cross-cutting; `full-matrix` is the orchestrator's.

## Follow-ons and issues

- To file (wolf-lang, not filed by the lane): the compiled output depends on the source directory's
  path (three binaries from one source and compiler in three worktrees; details above); first a
  minimal witness, then the issue.
- The 0.2.36 runtime has no hello identity entry: `static-pax.py` refuses it by name until someone
  measures it from LLD's trace and nm; nothing in the gate links it any more.
- The three resolved GNU TLS findings stay in the baseline gate by identity; a later lane may move the
  baseline forward to the 0.2.38 table when it re-measures the whole corpus with PAX boots.

## Decisions

- The manifest's form: the interned table in the note envelope, as ligature#22 built it.
- The 0.2.38 bundle: staged, pinned and recorded on this branch; published separately from the staged bytes.
- The admitted BLOCKED digest: retired.
- The findings at the pin: one fresh classification as evidence; the baseline gate unchanged.
- The branch: `ld03b`, plants `ld03b-plant-*`.
- The records' host: the Linux build host, once its disk read above the floor.
- link-cost: byte identity kept, both times recorded unbounded; time complexity is
  `link-memory-scaling`'s seconds bound.

## The committed logs

The raw logs under `notes/ld03b/` are redacted by one rule and otherwise byte for byte: the lane's
directory on the build host reads `LANE`, and the host's name reads `HOST` (in the recorder's
`host=` field too). `diagnose-link-cost/diagnose-linux.log` is the diagnosis take's log.
