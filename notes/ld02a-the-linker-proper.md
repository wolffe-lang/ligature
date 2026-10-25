# ld02a — the linker proper (ligature#14, merged at c0b56c3d)

The lane's report, materialised from the PR body at the merge by the orchestrator (the Codex wrapper writes no Markdown). Evidence under `notes/ld02a/`.

Footprint: cross-cutting

## Prediction

Committed before implementation in `15b6ecc`:
- Extraction cost below one second; all 349 sequence positions resolved. **Observed:** 0.143 → 0.171 s (+0.028 s), 349/349 resolved, identical 359-member multiset.
- Two of three TLS reorderings resolved. **Observed:** all three original **LLD** findings resolve; three new **GNU** findings for the same cases are retained. An unchanged count did not mean unchanged records.
- Byte-identical self-links. **Observed:** two seed links are identical, hashes read twice; executing the resulting linker and the bootstrap relink remain **BLOCKED on wolf-lang#962**.
- Note 116 bytes, hello manifest 2–8 MiB. **Observed:** note 116 bytes, hello manifest **147,136,512 bytes**; the manifest prediction missed substantially.

## What was done

- `66744d3`: retain RELA sites and targets; independent unused-data/debug patch witnesses; local/entry positive and negative normalization fixtures.
- `ece7414`: measured LLD-compatible lazy discovery, backward references, weak-demand behavior and extraction causes.
- `e54eb5e`: complete disjoint file ranges, patch/definition/alias attribution, NOBITS/TLS and validated `explain --symbol/--address/--why`.
- `64af563`, `c86cf51`: digest-pinned public bundle and genuine self-link harness over all compiler-emitted modules.
- `54f8a24`, `73b0d68`: reduced independent argv reproducer; exact-digest BLOCKED allowance under R-ld02-5 A; hard assertions for every other digest.
- `56c775a`, `0f5a89b`: tested compressed staging, separate TLS binding/content classification, full Linux records and exact old/new finding identities.
- `fedcd23`, `c0b56c3`: refreshed README, 56 fresh-kernel PAX boots, final structured closeout and ld03 draft.

Closes #3. Closes #13. The underlying argv fix remains wolf-lang#962/#963; no workaround was added to ligature.

### Forbidden

No other linker, libc or third-party kernel implementation source read. No Mac build/test, merge to trunk, tag, release, package publication, issue filing/closure, PR label or attribution trailer by this lane. Planning and `~/.claude` remained read-only. The PAX checkout was built with stock tools; its kernel source was neither read nor modified. ld01 remains read-only.

### Inputs, verified

Complete release archives read twice: Wolf 0.2.35 `4cc4045bbbb605c07835bc4f32685953c784eeef4cd3139a48b457dfc90dad1a`; Lupin 0.1.56 `ad703550ac4787e8e4bb26989d591a731410274d7332f2b4e8b9a64c878822cc`. Wolf's bundled std retained.

Published link bundle `6f99a2794da54b2dd85f06713d736b27862a7cd0da9e28bd940d975a4603a1d1` (36,594,483 bytes), downloaded and verified twice; every extracted input checked twice. Runtime `9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c` (45,363,160 bytes).

Fresh full PAX checkout **edbd385c91f2ff0eadb1ab4e52b276f1a1412b63**; `localhost/px79-ubuntu`, `PAX_WOLF=$(tools/fetch-wolf)`, no explicit `WOLF_STD`, stock `tools/build-kernel`. Kernel SHA256 read twice:
- native: `2ef1e4cfc0c9ed9a0dcd8f41d238f040a56b58ca8af5763c0c560902b3c97198`
- release: `265b2f3deb8f3dc3d76de0f34e346e7cd6872753f399e9c063e15a3abee46df2`

Host QEMU through PAX's `qemu-halt`/`qemu-run`, CPUs 12–15 by the shared lock, BIOS and UEFI/TCG, 4096 MiB. No stale ISO kernel or shared playground disk was used.

## Evidence

### Evidence index

`notes/ld02a/closeout.json`, `extraction.json`, `decisions.json`, `ld03-draft.json`; `evidence/linux-closeout.json`, `structural-classes-v2.json`, `pax-matrix-results.json`, `pax-inputs-verified.json`, `compressed-evidence-index.json`, `self-link-blocked-evidence.json`, `argv-probe/`, and gate logs.

`evidence/pax-evidence.tar.gz` contains every transcript, halt/row/boot record and build log. SHA256 read twice: **d1ba3d8f44def38928eb9c14f7a0875c20138633903dd44a4ea0a3e309bbae72**. Large ISO/CPIO evidence remains verified-compressed on kasumi. Every program, kernel, image and transcript hash was read twice.

- [x] Core gate: two checked tests, 43 process rows, ten three-linker writer cases, four TLS models, lazy-order oracle, per-site equations, full attribution/delta locality, explain and resealed corruption fixtures; zero SKIP.
- [x] Fourteen Linux cases: behavior against both oracles, own-reader verification, identical relinks, no candidate or oracle relocation-validation findings. Hello retains **590,358 RELA records**.
- [x] Exact before/after input identities/order/hashes match. Baseline times: 417.703 s warm-up, 335.921/337.213 s measured. Post-change: 255.397 s warm-up, 266.776/259.380 s measured. Medians 336.567 → 263.078 s include metadata and host-load changes; no extraction-only whole-link speedup is claimed.
- [x] **56 live PAX boots / 168 program runs**: native/release × BIOS/UEFI × 14 cases; all halt; all three linker outputs agree within every guest. **52 boot rows match Linux.**
- [x] **Four named RED rows, pax#175:** `pax-fork` prints `fork: io` in each combination instead of Linux's child and status 7. Matrix exit is **1**, not disguised as green; unexpected failures are zero. No expectation changed.
- [x] Two seed-linked linker outputs are identical: **c07f2300982e528f7556c398e91f45586ff671cad431fd1e1d4b08dbacf49600**, 182,631,512 bytes each, hashes read twice. Their manifest is 150,601,728 bytes. This is not an executed bootstrap success.
- [x] **BLOCKED self-link and executing ligature on PAX: wolf-lang#962.** The same 23 objects linked by both oracles lose argv too. Tiny Wolf fixture: cc/glibc preserves three arguments; LLD/musl and GNU/musl print argc=0; the pinned C/musl control preserves them. The orchestrator filed the issue.

### Structural records: 87, no blanket waivers

28 symbol, 28 segment, 28 retained-relocation-record differences, and three GNU TLS-order findings remain. Fourteen original LLD entry findings and three original LLD TLS findings resolve. The three new GNU TLS records are `compiler-procs`, `pax-host`, `pax-spawn`: named initializer bytes and memory sizes agree; binding differences stay separate. Every exact report is retained and indexed, not replaced by category acceptance. Structural equivalence is not claimed.

### CI plants

- #15, seen red at refined head `49f472d`, run [40184536391](https://github.com/wolffe-lang/ligature/actions/runs/40184536391): independent `target` relocation witness. The original 40184317162 checked-kernel red is not substituted for this evidence.
- #18, seen red at `b3ab537`, run [40184381385](https://github.com/wolffe-lang/ligature/actions/runs/40184381385): required `choice` archive extraction.
- #16, seen red at `db616de`, run [40184318477](https://github.com/wolffe-lang/ligature/actions/runs/40184318477): executed `local-exec`, actual `writer 35 3` versus expected `writer 42 3`.
- #17, seen red at `1559f93`, run [40184320850](https://github.com/wolffe-lang/ligature/actions/runs/40184320850): `self-link-execute` rc **-4**, after changing the actual generated entry to UD2 following integrity verification.

## Departures

**R-ld02-5 A:** the reproduced BLOCKED row is non-failing only while the fetched runtime digest is exactly `9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c`. CI loudly prints the issue, digest and diagnostic paths. Every other digest faces hard argv/self-link assertions; positive and other-digest/status negative tests cover the predicate. A green CI verdict does not claim either blocked capability works. Unblocking requires **both** a Wolf release carrying the new entry (0.2.36 at earliest) **and** the matching republished runtime bundle; runtime alone is insufficient. This is ld03's first item.

The cc/glibc seed drives the Linux corpus; its unchanged musl outputs run on fresh PAX. These are separate claims from a self-linked linker or a linker executing on PAX. No M milestone is claimed over the blocker.

R-ld02-1 A is the implemented measured recommendation; R-ld02-4 recommends the canonical reserved alignment string that fixes the demonstrated manifest-layout oscillation. The lane decided neither ruling. Digests mean integrity, never authentication. The large manifest, string merging, unwind header and richer discarded/dependency explanations remain explicit follow-on work. ligature#12 remains open.

Reporting is this PR and structured evidence, not a standalone Markdown report; no wrapper-refusal claim. README is refreshed. Initial classification conflated TLS binding with initializer equality; the new independent positive/negative fixtures separate them without removing any raw TLS finding.

## Hand-off

### Done-when

Local independent qualification is complete, with the exact-digest BLOCKED capabilities and four named PAX fork reds preserved under the agreed conditions. Final merge still requires green head CI, the orchestrator-added full-matrix label and a clean final audit. The lane does not label or merge.

Close ligature#3 and #13 at qualified merge. Keep wolf-lang#962/#963, pax#175/#176 and ligature#12 explicit. The ld03 draft is `notes/ld02a/ld03-draft.json`, first item compiler **and** bundle pins.

No jobs remain. Verified compression reclaimed about 6.2 GiB before PAX; the completed lane is 7.6 GiB, below its 10 GiB ceiling. Preserve pins, compressed evidence and indexes until review. Afterwards prune only exact ld02a generated target/build/cache paths and its four named plant worktrees; never enumerate and remove another lane's worktrees. Final run id and audit line follow at this head.

