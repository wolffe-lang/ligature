# ld03 — the explainable link

Materialised from ligature#22 (head b2615dd3, merged 2026-10-25) at the merge; the structured closeout is `notes/ld03/closeout.json`, the findings `notes/ld03/findings.json`, evidence under `notes/ld03/evidence/`.

Footprint: cross-cutting

## Prediction

Committed first at `f616c8d`: a compact provenance manifest at least 10× smaller than the JSON one with every patch record retained. Scored: 147,136,512 → 12,414,976 bytes, 11.85×; 590,358 hello patches identical; 17,765 explicit discard/consumed-metadata records added. The first row stays as predicted: self-link BLOCKED unchanged: the self-link goes live when ld03b (or the pin lane) bumps both compiler and bundle (runtime digest `9d859b9e6b5319f5…`, predicate unchanged).

## Forbidden

ligature's clean room (never any linker's source); no self-link predicate, pin or test change (the first row flips only when ld03b or the pin lane bumps both compiler and bundle); no kernel rebuild (ld02a's immutable native/release ELFs reused, hash-checked twice); no attribution trailers; no ruling decided — R-ld03-1 is recommended: option A with the existing two-section envelope retained. Interned binary table in .wolf.link.manifest, sealed by unchanged 116-byte .note.wolf.link; no sidecar and no ruling decided

## Inputs verified

- Corpus source head `f76ae9cb4dd8092ef823e4a654a1c4da91316797` (fourteen cases, all string pools ASCII); the final byte-name correction `6864e5b` disclosed with its own witness, not hidden behind a pre-edit green.
- PAX kernels from `edbd385c91f2ff0eadb1ab4e52b276f1a1412b63`: Reused immutable ld02a native/release ELF binaries, verified twice; no kernel rebuild or claim of current PAX trunk
- Every inherited self-link output, kernel, structural record, PAX archive and all 56 archived transcripts read by SHA twice; `/home/mfwolffe/lanes/ld02a` untouched.
- Recovery: Kasumi reboot at 13:32 EDT preceded qualification launch. Mac reboot at 16:21 EDT followed PAX completion at 16:20:33 EDT. All completed markers were reconciled; no completed Linux corpus or PAX boot was relaunched. A dead job is not a red row.

## Evidence index

- Findings: 0 resolved / 87 retained / 0 waivers, by name with baseline and current raw hashes in `notes/ld03/findings.json` (relocations 28, segments 28, symbols 28, tls 3); fresh facts equal the ld02a baseline exactly.
- Linux: 14 qualified cases, 14 deterministic relinks, 28 oracle comparisons, 0 functional failures, 8,282,548 candidate relocation sites independently validated; hello link 190.4/185.1 s, final witness 171.4/207.4 s (no speedup claim).
- PAX: 56 boots, 168 program runs, 56 proven halts, 52 Linux-equal rows, 4 named pax-fork reds (pax#175), 0 unexpected; raw exit 1. Archive `notes/ld03/evidence/pax-evidence.tar.gz` (sha 0be46176…, read twice), summary `pax-results.json`.
- Tracked evidence under `notes/ld03/evidence/`: evidence/compress-views.log, evidence/compressed-views.json, evidence/final-byte-name-witness.json, evidence/final-core.log, evidence/final-witness.exit, evidence/final-witness.log, evidence/inherited-hashes.json, evidence/inherited-transcripts.json, evidence/linux-qualified.json, evidence/linux-results.json, evidence/marker-tests.log, evidence/pax-evidence-index.json, evidence/pax-evidence.tar.gz, evidence/pax-inputs.json, evidence/pax-results.json, evidence/pax.exit, evidence/pax.log, evidence/plant-40217336712.log, evidence/plant-40217341895.log, evidence/plant-40217347952.log, evidence/qualification.exit, evidence/qualification.log
- Structured closeout: `notes/ld03/closeout.json`; ld04 draft `notes/ld03/ld04-draft.json`.

## Done-when

- [x] Prediction committed before the change; scored above.
- [x] Compact manifest with every finding retained by name; an independent encoder reproduces the bytes; legacy JSON verify/explain still supported.
- [x] Fourteen Linux cases and fifty-six PAX boots qualified; every transcript read twice.
- [x] Three plants red by name (below), left open for the orchestrator.
- [x] README read and refreshed; the note is this body (the wrapper refuses .md), materialised at the merge.
- [ ] Full-matrix label and a green tier full at this head (the orchestrator's).

## Follow-ons

- ld04 (draft in `notes/ld03/ld04-draft.json`): the exact subset/refusal rows and the separate AArch64 work.
- Retained blockers: wolf-lang#962/#963 compiler and bundle pins; pax#175 fork behavior; ligature#12 total-link cost; ligature#13 genuine self-link qualification.
- No issue to file or close from this pass.
- Prune after review (7.8 GiB (the prior 5.9 GiB Linux checkpoint grew with PAX images; verified text compression reclaimed 3415952094 bytes)): /home/mfwolffe/lanes/ld03/pax-results (5.1 GiB); /home/mfwolffe/lanes/ld03/ligature/target (2.3 GiB); /home/mfwolffe/lanes/ld03/ligature/.wolf-bin (363 MiB); /home/mfwolffe/lanes/ld03/ligature/.link-inputs (118 MiB); /home/mfwolffe/lanes/ld03/pax-image-root (?); /home/mfwolffe/lanes/ld03/pax-cases (?); /home/mfwolffe/lanes/ld03/pax-tools (?); /home/mfwolffe/lanes/ld03/marker-tests (?).

## Note

ld03 makes the link explainable at a size that ships: the provenance manifest drops from 147 MB of JSON to 12.4 MB of an interned binary table inside `.wolf.link.manifest`, sealed by the unchanged 116-byte `.note.wolf.link`, with every one of the 590,358 hello patch records intact and 17,765 discard/consumed-metadata records made explicit. All 87 findings of ld02a are retained by name (symbols, segments and relocations against both lld and GNU ld; three tls identities kept independently), none resolved and none waived. Fourteen Linux cases relink deterministically and agree with both oracles; fifty-six PAX boots run the three linkers' outputs equal in every guest, with the four known pax-fork reds. The self-link row stays BLOCKED by the compiler and bundle pins until ld03b or the pin lane bumps both.

### Plants

- ligature#19 `ld03-plant-drop-provenance` at d7fbfae: expected red `provenance retained patch count mismatch`

- ligature#20 `ld03-plant-reclassify-finding` at 2e5d005: expected red `retained finding silently reclassified`

- ligature#21 `ld03-plant-nondeterministic-relink` at b790963: expected red `nondeterministic relink`


