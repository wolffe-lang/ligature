# ld04 — archives, AArch64 and the paging kernels

_Materialised from ligature#23's PR body at the merge (730a43e2); the lane's wrapper could not write Markdown notes._

Final head: `730a43e260bdaaa0d8b78214dc56c925bfd9c517`. CI run **40394787679**: green `tier pr`, observed by the required audit without waiting. Audit last line: **`AUDIT CLEAN (footprint: module)`**.

All seven kernel rows now have executable-link evidence and real boots. The nine requested AArch64 relocation kinds, including GOT 311/312, are implemented and an assembled hello executes under emulation. **Wolf-generated AArch64 inputs/hello remain BLOCKED on existing wolf-lang#614.** Keep this PR draft pending the detached full-corpus regression and review; no M4 sign-off is implied.

This wrapper prohibits Markdown lane-report files. This body is the five-section note; `notes/ld04/closeout.json` supersedes the earlier `checkpoint.json`.

## Prediction

`17995f7`, committed first: at least 20 profile/refusal witnesses, deterministic indexed archives, and no kernel/AArch64 execution claim without actual execution. Observed: **31 profile rows, 35 archive process rows**, deterministic archive bytes, **four kernel boots**, and an **assembled AArch64 hello**. A Wolf-generated ARM hello is explicitly blocked, not substituted by that assembly witness.

- `9746024`, `82f10fe`, `db3c9c9`: profile, GNU archive writer, commands/gates.
- `66098a2`: executable kernel profile and full-width address/provenance model.
- `8122683`: validated excluded LLVM ADDRSIG metadata for real release inputs.
- `80108cc`, `365a516`, `b41ca53`: AArch64 relocations, indexed pair proofs, independent oracle veneers, XZR/SP refusal.
- `5eb481f`, `0ec8c77`: exact script input attribution and declarative plans.
- `d7bee69`: guarded, explicitly nonexecuting kernel snapshots and retained oracle refusals.
- `e3b88b3`, `04b5f7b`: named range/TLS/query-size refusals before unsigned conversion.
- `730a43e`: final evidence and continuation draft. No implementation/test bytes changed after the committed-head gate.

## Forbidden

No other linker's source read; only this project's implementation, published specifications and binary oracles. No PAX/kernel implementation source read or modified; unchanged kernel inputs were built by PAX's tools. No compiler/pin/self-link-predicate changes, package installation by this lane, Mac builds, labels, merges, tags, releases, issue filing/closure or attribution trailers. Planning and `~/.claude` stayed read-only.

**Correction disclosed:** early kernel site witnesses accidentally inherited `tools/differ.snapshot()`'s `execute=True` default, attempting native execution of high-half ELFs inside the lane container. Those attempts were not functional-pass evidence; their return statuses were not retained. The final callers explicitly disable execution and have an independent guard against launching the kernel path. A regression plant was rejected **before process launch**, the complete guarded gate was rerun, and all four QEMU boot legs were rerun with the corrected harness. The separate real boot proofs are not native-process execution claims. See `evidence-resumed/kernel-nonexecuting.json` and `kernel-guard-plant.log`.

## Inputs verified

- Ligature base `db2bf27`; adopted ld03 draft/note, ld02a note, PAX as02b note, campaign, RULES 1–10, all 87 finding decisions and fourteen inherited corpus qualification records read.
- Complete pinned Wolf 0.2.35, Lupin 0.1.56 and musl/oracle bundle verified twice by the existing fetchers. No pin moved. Actual AArch64 release archive SHA256: `30ccded432264b7ddd4ebf738d4f895d12091ca604e2da4c2f831da807886f3e`, verified twice.
- PAX source `4831abe70e08811be4a7adbd6cfb3b0cbad21699`; permitted script byte-identical to the fixture. Native/release input and output hashes read twice; `kernel-results.json` records them.
- Observed images `localhost/ligature-oracle` and `localhost/as02b-rust`; LLD17, LLD18.1.3 and GNU ld 2.42 binary controls. QEMU user 11.1.2 and ARM glibc 2.44 sysroot were provisioned by the coordinator, not installed by this lane. Cross GCC/binutils were not used as expected-answer oracles.
- Builds/tests on kasumi CPUs 8–11 under the shared lock. `final-input-output-hashes.json` matches the committed source/test bytes to tested inputs/outputs.

## Evidence index

All paths below are under `notes/ld04/evidence-resumed/`; `resumed-evidence-index.json` contains twice-read hashes.

- **`committed-head-check.log`**: complete `tools/check`, exit 0 at committed code head `04b5f7b`. Four checked suites, all native/core/provenance gates, 31 profile, 35 archive and 51 AArch64 rows; 0 SKIP. The final evidence commit changes no implementation/test bytes.
- **`kernel-script.json`**: actual three-linker high-half outputs; entry, three LOAD permissions/page separation, absolute bounds, ordered `.data.limine`, COMMON/NOBITS, script discards, full-width explain/provenance, deterministic bytes, orphan/format/type/range refusals. The script is a hashed original input.
- **`kernel-results.json`, `kernel-boot-evidence.tar.gz`, `final-guarded-kernel.log`**: native/release paging kernels; **66,882 + 60,768 = 127,650** candidate relocation sites independently validated; deterministic relinks; bound values equal all three oracle controls; **four BIOS/UEFI boots** with monitor-backed paging, W^X, HHDM/map/unmap and proven halt. The archive contains the actual serial/monitor/verdict artifacts.
- **`final-kernel-identity.json`**: final relinks byte-identical to the boot-qualified ELFs. **`kernel-nonexecuting.json`**: explicitly guarded, nonexecuting site proofs.
- **`kernel-structural/index.json`** and eight compressed raw views: **24 named observations/refusals**, separate from the inherited 87. Oracle `.rodata` retains SHF_WRITE inside R-only LOADs, so the strict verifier refuses those reference outputs; program headers and script-symbol metadata differ too. No category waiver or whole-ELF equivalence claim.
- LLD17 default reproduces the real release-kernel GOT range failure at `__pax_image_start`; its `--no-relax` control succeeds. LLD18 default succeeds; GNU kernel controls explicitly use `--no-relax`.
- **`aarch64-rows.json`**: 51 independent ELF/range/alignment/instruction-mask/pair/GOT/refusal rows. ABS64 low-bit wrapping and byte alignment; PREL32's specified signed-or-unsigned interval; CALL26/JUMP26, ADRP, ADD/LDST64 and GOT 311/312. Unknown/TLS variants, duplicate sites and unsupported pairs are named refusals.
- **`aarch64-endpoints17.json`, `aarch64-endpoints18.json`**: 24 binary endpoint controls each. Oracle branch veneers are independently decoded through their exact target literals, not waived.
- **`aarch64-live-evidence.tar.gz`, `final-aarch64-17.log`, `final-aarch64-18.log`**: actual clang AArch64 objects, archive, candidate/reference ELFs and records. All nine types appear in ten independently proved sites. Candidate and both LLD outputs print `hello, AArch64` plus LF and exit 0 under **explicit emulated user mode, not native ARM hardware**.
- **`aarch64-census.json.gz`**: actual compiler ELF's 14,033 dynamic relocations and all **440 runtime members / 668,066 relocations**. Additional runtime families remain explicitly outside the nine-type implementation; no full-runtime link is claimed.
- **`compiler-blocker/results.json`**: verified AArch64 Wolf 0.2.35 runs, but native `--emit=obj` and release `--emit=llvm-ir` each refuse the host with status **2**. The probe reports BLOCKED and exits 2, not PASS or SKIP. This reproduces existing **wolf-lang#614**; no guard workaround.
- **`resumed-plants.log`, `kernel-guard-plant.log`**: local plants seen red at the intended assertions for writable rodata LOAD, corrupted AArch64 GOT target, invalid ADDRSIG index and attempted kernel execution; restored green. Initial archive/profile plants remain in `notes/ld04/evidence/plants.log`.

Self-link remains the reproduced **exact-runtime-digest BLOCKED** row for wolf-lang#962; neither compiler nor bundle/predicate changed. All 87 inherited findings remain named, with zero waivers. A fresh fourteen-case Linux regression is a separate detached final-head job; its result is not preclaimed.

## Done-when

- [x] Prediction before implementation; README read and refreshed in README-only commits.
- [x] GNU/SysV archive writing, index identity, determinism and executed three-linker controls. Thin/BSD remain named refusals under the adopted draft.
- [x] Kernel OUTPUT_FORMAT/ENTRY, PHDRS/flags, high-half arithmetic, bound symbols/ALIGN, ordered sections/COMMON/NOBITS, script discard attribution, full-width GOT behavior.
- [x] Actual native/release kernel links and four firmware boot legs.
- [x] All nine AArch64 fixture relocation kinds, including GOT 311/312; endpoint/pair proofs, actual binary census, emulated assembled hello.
- [x] Full local gate at committed code; independent evidence and local plants.
- [ ] Actual **Wolf-emitted** AArch64 object census/hello: **BLOCKED wolf-lang#614**, not narrowed away.
- [ ] Detached fresh fourteen-case regression and exact 87-finding comparison: PID/log/marker supplied at handback; no green claim before completion.
- [x] Final-head CI run 40394787679 is green (`tier pr`, 2/2 jobs); audit once: `AUDIT CLEAN (footprint: module)`. No CI wait, no labels; PR stays draft.

### Recommendations, implemented, not decided

R-ld04-1: execute only the exact explicit kernel profile. R-ld04-2: bounded create-only GNU/SysV archives. R-ld04-3: distinguish assembly/runtime census from compiler-generated ARM qualification. R-ld04-4: exact decimal strings above INT64_MAX, preserving low integer fields. R-ld04-5: retain strict verification and all 24 kernel observations rather than waive oracle differences.

### ld05 draft

`notes/ld04/ld05-draft.json`:
1. Read the final-head full-corpus result and all 87 exact deciding facts; resume ld04 on red.
2. Coordinate the explicit PAX kernel-linker seam in a PAX lane; no default flip here. Preserve four-leg boots, per-site equations and named LLD17/no-relax/LLD18 controls.
3. Resolve wolf-lang#614 in the compiler lane before claiming actual Wolf ARM objects/hello. Scope the remaining census families (258/260/278/284/285/299 and TLS descriptors 562/563/564/569), richer pairs and runtime/libc integration separately.
4. Compiler `--emit=lib` integration and thin/BSD formats remain follow-ons.
5. Preserve identity-based findings, provenance before merging strings/unwind records, and authentication as a separate signed envelope.

No new issue filing recommended; update existing wolf-lang#614 with the 0.2.35 reproduction. No issue filed or closed.

### Long job and pruning

Full regression is running on kasumi at this final head, PID **1096855**; initial log confirms CPUs 8–11. No exit marker existed at launch verification. Files: `/home/mfwolffe/lanes/ld04/full-corpus.pid`, `/home/mfwolffe/lanes/ld04/full-corpus.log`, `/home/mfwolffe/lanes/ld04/full-corpus.exit`; result `/home/mfwolffe/lanes/ld04/ligature/target/static-pax/ld04-comparison.json`. It leases each expensive command through the shared lock, not the whole run. Do not prune active results.

After completion/review, exact prune candidates: `/home/mfwolffe/lanes/ld04/ligature/target`, `.wolf-bin` and `.link-inputs` beneath that clone; `/home/mfwolffe/lanes/ld04/kernel-qualified`, `/home/mfwolffe/lanes/ld04/kernel`, `/home/mfwolffe/lanes/ld04/boot`, `/home/mfwolffe/lanes/ld04/pax`, `/home/mfwolffe/lanes/ld04/aarch64-release`. Container-written files may require `podman unshare rm`. No shared image or coordinator-installed package is on the prune list. The clean Mac worktree was removed before the audit. The temporary `/home/mfwolffe/lanes/ld04/committed.bundle` was pruned after verified synchronization; other evidence stays for review.

