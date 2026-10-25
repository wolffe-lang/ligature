# ld01 — hello static (ligature#11, merged at `3f206413`)

This note is the PR body of ligature#11, materialised at the merge by the orchestrator (the lane's wrapper could not write Markdown). The lane's evidence files are under `notes/ld01/` where it kept them.

Footprint: cross-cutting

## Prediction

Committed before implementation in `f01a0a3`: TLSGD would fail first, hello would miss 359 pulls initially, GD/LD relaxations would be needed, writer ~2100 lines, first PAX run would fail. Observed: first valid-path hello linked and ran; exact 359-member multiset immediately; GD/LD confirmed in hello; 1599 implementation lines; first guest hello ran. Extraction order differs at 349 positions and is recorded, not hidden.

## What was done

- `bbabe78`, `daaddeb`: ordered indexed archive groups, strong/weak/common, COMDAT, forced roots, aliases and visibility.
- `bf09269`, `15bc2c4`, `bf02104`: GC, static ELF layout, the census's 13 relocations, TLS transitions, symbols and executable verification.
- `600342a`: post-layout GOT relaxation range check, including the high-half -2147483652 witness (ligature#4).
- `f8a3060`: cc-shaped musl frontend; unchanged `CC=ligature wolf build` with matching runtime/sysroot. `-fuse-ld=lld` is accepted and ignored.
- `172df6c`: section-level provenance, fixed note format and independent digest checks.
- `7e22de0`: byte-sensitive executed hello and genuine PAX transcript replay gates.
- `8d8f247`, `3f20641`: live PAX evidence, classified differences, ld02 draft and final source gate. README refreshed.

### Forbidden

No linker, binutils, libc or third-party kernel implementation source was read. No merge, tag, release, package installation, issue closure, PR label or Mac build/test. The late PAX control compiled this organization's own kernel through stock tools after the coordinator requested it; it was not a reference for the linker implementation.

### Inputs, verified

Complete Wolf 0.2.35 (`cf0c13d`) and Lupin 0.1.56 (`28547b4`) release archives were hashed twice: Wolf `4cc4045bbbb605c07835bc4f32685953c784eeef4cd3139a48b457dfc90dad1a`, Lupin `ad703550ac4787e8e4bb26989d591a731410274d7332f2b4e8b9a64c878822cc`. Wolf's bundled std was retained. The copied PAX ISO is `02f979bedf5520661f8a5e5623f1f9a7f5cb18b2b1d8c936b3d51f8c0336d4d9`; exact LLD `1217ca75f9df70439294844b2aba14895adc557e2514c6cdc76c4c6676a3757b` and musl runtime `9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c`. Input sizes/hashes were checked twice against `tests/pax-link.sums`. Distro oracle identities are in `docs/SOURCES.md` and the LLD 18 control record.

## Evidence

Evidence index: `notes/ld01/closeout.json`, `notes/ld01/evidence/`, `notes/ld01/ld02-draft.json`.

- [x] Final local `tools/check`: 2 checked tests, 43 integration process rows, indexed-resolution fixtures, 10 three-linker writer cases, deterministic relinks, cc/provenance/replay/range gates and public-runtime roundtrip; zero SKIP.
- [x] Hello: exact 359 member identities/multiplicities (32 runtime, 322 libc, 5 unwind), exact 401 public-definition names; TLS 80 initialized / 272 memory / alignment 8.
- [x] Fourteen Linux cases: both oracles' stdout/stderr/status, own-reader verification, byte-identical relinks. Full batch head `bb00a28`; log SHA read twice: `b6a6c59f4331d825fe02df371110431874b33b2c095233cf329fa7b995cb7a02`.
- [x] Final provenance-bearing hello built by unchanged wolf, executed on Linux and PAX. Same-input explicit-link control: all 156 allocated sections and program headers unchanged by provenance emission.
- [x] Fourteen live PAX BIOS/TCG legs: all three linker outputs agree within each guest; all kernels halt cleanly. Thirteen cases also match Linux.
- [ ] **Named cross-host red, pax#175:** `pax-fork` prints `fork: io` on PAX, versus child + status 7 on Linux. Fresh full-checkout PAX trunk `105d0d1` native AND release kernels reproduce syscall 57 `-ENOSYS` under all three linkers. No expectation changed. Kernel/serial hashes and unquieted diagnostics are committed. Missing commit banner tracked by pax#176.

### Structural records: 101, none waived

| Class | Count |
|---|---:|
| Symbol metadata/local retention | 28 |
| Segment shape/flags/alignment | 28 |
| Entry aliases | 14 |
| Retained relocation records | 28 |
| Raw TLS variable ordering | 3 |

The TLS cases have equal named-symbol initializers and memory size. Five LLD 18.1.3 controls (hello, pax-loop, pax-hello, pax-std, compiler-procs) have **zero** structural differences against LLD 17 and retain all five classes against ligature. These classes are ligature's, not the 17/18 high-half kernel artifact (pax#172). Exact reports remain in verified compressed evidence archives; committed indexes give per-record hashes and classifications.

### Plants seen red in CI

All six drafts were closed unmerged by the coordinator:

- #5, seen red in run [40177155125](https://github.com/wolffe-lang/ligature/actions/runs/40177155125), head `227cadc`: executed hello `(b'', b'', -4)`.
- #6, run [40176469421](https://github.com/wolffe-lang/ligature/actions/runs/40176469421): required `weak.o` pull assertion.
- #7, run [40176472807](https://github.com/wolffe-lang/ligature/actions/runs/40176472807): local-exec TLS writer verification.
- #8, run [40177416224](https://github.com/wolffe-lang/ligature/actions/runs/40177416224), head `c819142`: high-half relocation overflow witness.
- #9, run [40177417831](https://github.com/wolffe-lang/ligature/actions/runs/40177417831): `PAX validator accepted mutation` (captured-transcript replay, not a boot).
- #10, run [40177422430](https://github.com/wolffe-lang/ligature/actions/runs/40177422430): provenance corruption `('manifest', 0, b'')`.

The initial #5 plant was harmless: +1 into `puts`' ENDBR64 leaves a NOP. The gate already executed and compared the binary; a RET/UD2 assembly marker made the mutation sensitive. The initial #8 event was an unchanged baseline after a patch-site mismatch; only its corrected head is counted.

Canonical `bash wolf/tools/lane-audit.sh ligature ld01 11`: exit 1; last line **`AUDIT FAIL (footprint: cross-cutting)`**. PR CI run **40180058218** was first observed in progress at `3f20641`; no CI wait. Required PR/full-tier green and the coordinator-added label remain pending.

## Departures

- M1 is presented on 13 matching cross-host rows plus the identically reproduced, named PAX fork red, as accepted by the coordinator. It is not an all-green cross-host claim.
- Archive identity/multiplicity matches; lazy discovery order does not. Unwind records are retained with dead-target tombstones, no unwind header; merge strings are concatenated. Retained relocation sections and per-site output differential proof remain incomplete. Structural equivalence is not claimed.
- Provenance explicitly says `coverage: sections`; full disjoint byte ranges, patch attribution and `explain` remain ld03. The note is an integrity digest, not a signature.
- The full Linux batch predates note emission; the final source gate and same-input allocated-section control cover that addition. The cc compiler's optional trap-root plan is not confused with the forced-root census plan.
- Live PAX boots are local, on kasumi's host through unchanged `qemu-halt`/`qemu-run`, pinned to CPUs 12–15; builds run in Ubuntu containers. BIOS/TCG, 2048 MiB, no UEFI claim. The exact ISO link bundle is not provisioned in CI (pax#167); CI has generated distro fixtures and a genuine transcript replay.
- Narrative sections live in this PR and durable JSON evidence under `notes/ld01/`, rather than a standalone Markdown note. No wrapper refusal is claimed.

## Hand-off

### Done-when

Implementation and local evidence are presented with the explicitly accepted fork red and unwaived structural findings. Merge waits for the required green CI tiers and the coordinator-added full-matrix label; no green head is claimed here.

R-ld01-1 A (range-checked direct relaxation), R-ld01-2 A (0x200000), R-ld01-3 A (live locals retained, differences named), R-ld01-4 (weak definition under strong demand) implemented; the last was concurred.

`notes/ld01/ld02-draft.json` covers relocation proof/normalization, archive/TLS ordering, wolf-lang's `--linker`/`WOLF_LD`, removing the image's lld/cc, and self-linking. Existing issues remain explicit: ligature#3, pax#167, pax#172, pax#175, pax#176. The range fix for ligature#4 is implemented; closure is the coordinator's. Consider a separate performance issue for the roughly three-minute hello link.

Kasumi lane use is below 10 GB. Retain verified compressed corpus archives, binary pins and transcripts until review. Afterwards prune only exact ld01 generated trees and its plant worktrees; no other lane paths. No jobs remain running.

