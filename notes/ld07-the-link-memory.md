# ld07 — the link's memory: one static link in a bounded footprint (ligature#32)

## Prediction

Written before any change to `src/`, from reading every module and from a counter build of
trunk `c8ca1be4` (phase markers only, kept off this branch) run on macOS arm64 against the
same x86-64 inputs, killed by a resident-set watchdog at 2.5 GiB.

**The mechanism.** Wolf's native tier places every allocation in the current region, and per-object
frees do not exist. Outside a `region` block the current region is the process-root arena, which
frees nothing until exit. The link runs almost entirely in the root arena; only `elf.walk`'s
per-section and per-symbol blocks and the three hashing blocks free anything. So the link's peak is
close to the **cumulative** allocation of the whole link, not its live set. A list grown by `push`
also keeps every abandoned buffer charged, about 2x its final size (1x after `reserve`).

Unit costs, measured on the pinned compiler with `region_bytes` (macOS arm64):

| idiom | charge |
|---|---|
| `List[byte]` grown to n by `push` | 2n (n after `reserve(n)`) |
| `binary.read` of n bytes (64 KiB `fs_read_at` parts copied into a grown list) | about 3n |
| `copy` of a struct holding a list | the whole list again |
| `for x in xs`, `xs[i].f`, passing `xs` to a read parameter | 0 |
| a `"{a}:{b}"` key | 16 B |
| `Map[str, int]` entry, key included | about 65 B |
| `json.parse` | about 10.5x the text |
| emitting JSON through `emit` | about 5x the text |
| `sha2.update256` (a fresh 64-word schedule and a fresh buffer per 64-byte block) | about 17x the input |

The counter build, hello against the 46.7 MB runtime (363 selected objects, 22,566 symbols,
14,372 sections of 18.1 MB, 647,354 relocations, 614,648 retained patch rows, a 44.8 MB output):

| phase | resident growth |
|---|---|
| resolve | 74 MB |
| read (every selected section's bytes, before GC) | 223 MB |
| collect (10 passes) | 4 MB |
| place (zero-filled outputs, then copied bytes) | 74 MB |
| relocate | 112 MB |
| symbols | 8 MB |
| retained relocations | 248 MB |
| input hashing (`provenance.inputs`) | 1,010 MB |
| manifest, two fixed-point iterations | 660 MB |
| output image (zero-fill and copies) | 140 MB |
| **reached at the watchdog, before seal and the in-link verify** | **2.57 GB** |

**Predicted owners at the 7.2 GiB peak**, largest first:
1. **The in-link verification**, which runs after the output is written and in the same root arena:
   the whole-file and manifest digests through `sha2` (about 17x the 44.8 MB file), and
   `provenance.validate`, which decodes the whole manifest into a `json.Value` tree, one `Map` per
   patch row (614,648 rows), before checking it. Predicted: about the 4.8 GiB standalone
   `ligature verify` measures (ligature#32), so about two thirds of the link's peak.
2. **Hashing**: inputs and members (1.0 GB measured), the seal digests of the output (about 0.8 GB).
   Each runs in its own `copy region`, so its charge is freed, but a single digest's working set
   sits on top of everything the root holds at that moment.
3. **The manifest**, rebuilt on every fixed-point iteration (two here): JSON emitted byte by byte
   through grown lists, a hex string and a slice per patch, the pulls re-parsed as JSON. About
   330 MB per iteration.
4. **Per-relocation encoding**: retained relocations (`binary.encode` builds three lists per entry)
   and relocation application (a site string per relocation). About 360 MB together.
5. **Section bytes**: read with about 3x overhead for every selected section, live or not, then
   copied into zero-filled outputs (2x), then into a zero-filled file image (2x), with a `copy` of
   each output section on the way. About 0.4 GB in all.

**`--gc-sections` keeps dead bytes alive: yes.** `layout.read_for` reads every selected section's
bytes before `collect` decides liveness: 18.09 MB read, 16.96 MB live, and the 1.13 MB of dead
sections stay charged for the whole link, along with their relocation records.

**The levers, ranked by this model:**
1. Run each phase's work in a region so its temporaries are freed, carrying out only the result
   (`copy region`); put the in-link verification after the link's own state is gone.
2. Hash in bounded steps: each 64 KiB step in its own region, carrying out only the eight state
   words. The digest is the pinned `sha2`'s by construction.
3. Validate the provenance patch table by streaming it, without a `json.Value` per row (the same
   checks in the same order, with the same refusal messages).
4. Read section bytes once, at exact capacity, and only for live sections where liveness does not
   need them; zero-fill with `reserve`.
5. Write the output image once.

**Predicted rows after the change:** hello's link resident peak under 1 GiB (predicted
0.3–0.6 GiB), `str` the same, `ligature verify` under 1 GiB; every output byte-identical to
trunk's; the hello link no slower than trunk on the same host (predicted faster: most of the time
is allocation); the N/10N/100N synthetic-archive row linear.

## Forbidden

No linker, binutils, libc or kernel source was read: not lld, mold, gold, GNU ld, ld64, zig's linker,
binutils, musl or glibc. The references are ligature's own source, the wolf language specification
(the memory model's regions, `copy region`, the list storage clauses) and the pinned standard
library's `sha2` module. The oracles ran as binaries only. No publication, tag, label, merge or issue
closure; no pin changed.

## Inputs verified

- Base: trunk `c8ca1be4b3ccb7f8c425638e2d1145d21a62ee5a`.
- wolf 0.2.36 (pin `5adf3d9`): the Linux x86-64 release by its pinned digest
  (`tools/fetch-toolchain`) and the macOS arm64 release by its pinned digest
  `b79d55845f349d56789d9d1cb057ee88b5a7128d3b6dd77ca070707cfa4aa632`, read twice.
- The licensed musl link bundle `8210ac22…3e37a`, MANIFEST `8bcea757…86`, every member verified
  twice by `tools/fetch-bundle`; its `libwolf_rt.a` is the 0.2.36 musl runtime, SHA-256
  `6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad`, 46,700,882 bytes.
- The x86-64 objects (hello, `str`, the linker's own 24 modules) were compiled by the pinned compiler
  on Linux. The same object files were linked on both hosts, so every comparison below is of one set
  of inputs. ligature's output depends on its inputs' bytes and base names only: the macOS build of
  the head and the Linux build of trunk wrote byte-identical hello and `str` executables.
- Oracle and gate image: the repository's own `ci/oracle.Containerfile` (lld 17.0.6, binutils 2.42).

## Evidence index

### The measured model, trunk, Linux x86-64

Resident set (VmHWM) at each phase marker of a counter build of trunk (markers only), hello against
the 46.7 MB runtime:

| phase | resident after | growth |
|---|---|---|
| resolve | 73.8 MB | 71.5 MB |
| read (every selected section, before GC) | 298.3 MB | 224.4 MB |
| collect, place | 348.3 MB | 50.0 MB |
| relocate | 509.1 MB | 160.8 MB |
| symbols, retained relocations | 761.8 MB | 252.6 MB |
| input hashing (`copy region`, freed) | 764.0 MB | high-water 1,767.6 MB |
| manifest, two iterations | 2,419.3 MB | 1,655.3 MB (627.9 MB of each is patch attribution) |
| output image | 2,576.1 MB | 156.8 MB |
| seal and whole-file digests (freed) | 2,576.6 MB | high-water 3,538.1 MB |
| in-link verify: the manifest decoded as JSON | 5,279.9 MB | 2,703.3 MB |
| in-link verify: patch checks over that JSON | 7,829.5 MB | 2,538.0 MB |

The prediction held. The in-link verification owned two thirds of the peak (5.24 GB of 7.83 GB);
standalone `ligature verify` is the same two owners (2.18 GB and 2.54 GB, peak 5.26 GB). Hashing
charged about 17x its input in freed regions, and each manifest iteration about 830 MB.

Trunk's rows on Linux x86-64, the issue's command, as a direct child under a 10 GiB address-space cap:

| row | resident peak (VmHWM) | address-space peak | seconds |
|---|---|---|---|
| hello link | 7.291 GiB | 7.322 GiB | 23.8 |
| hello link, again | 7.291 GiB | 7.329 GiB | 24.9 |
| `str` link | 7.317 GiB | 7.409 GiB | 23.9 |
| `ligature verify` of hello | 4.901 GiB | 4.865 GiB | 4.4 |

### The change, by owner

| owner | change | commits |
|---|---|---|
| in-link and standalone verify | the patch table validated in two streaming passes through a cursor, no `json.Value` per row; each row's file read freed in its own region | `e96331a`, `a2f783b`, `e813bc0` |
| hashing | 64 KiB steps, each in its own region, carrying out the eight state words of the pinned `sha2` | `b239455`, `7786486` |
| manifest | each fixed-point iteration in a `copy region`; patch attribution without per-row lists, slices or quadratic hex strings | `2dde4b8`, `c70824f` |
| relocations | sites built only for refusals; skipped TLS calls by list, not by string key | `9bf133e` |
| retained relocations, symbols | encoded straight into reserved tables; output indices by list | `dc85f0f`, `8c85ea8` |
| section bytes | read at exact capacity, and only for the sections `--gc-sections` keeps | `3f18d8e`, `7a3b723` |
| outputs and image | zero-filled at capacity; written without per-section copies | `21b1d7b`, `18b39f8` |
| lookups | sections, symbol tables and global names by integer or by ligature's own name index | `e4e8524`, `43975ec`, `708db6f`, `b90a452` |

The pinned native `Map` costs time in proportion to its size on every operation, whatever the key's
shape (2,000 to 8,000 entries: about 20x the time). Lookups once per symbol or per relocation made
trunk's links superlinear in their inputs; the name index and the integer indexes remove that cost.

### After, macOS arm64 (the same object files)

| row | resident peak | seconds |
|---|---|---|
| hello link | 0.703 GiB | 5.7 |
| `str` link | 0.710 GiB | 5.5 |
| `ligature verify` of hello | 0.246 GiB | 1.6 |
| synthetic 1/40/400/4000 members | 6.2 / 8.6 / 36.3 / 331.5 MB | 0.005 / 0.015 / 0.111 / 1.148 |

The largest owners at the new peak: the root's live state and garbage before the manifest
(about 266 MB), one manifest iteration's region (about 355 MB, freed), and the output image with its
seal (about 80 MB). Trunk's hello link does not fit under the macOS rows' 2 GiB watchdog.
The prediction was 0.3–0.6 GiB; the measured 0.70 GiB is above it because a manifest iteration's
working set, though freed, still stands on top of the root's at its own peak.

### Rows

- `tests/link-memory.py` (in `tools/check`): `link-memory-hello`, `link-memory-str`,
  `link-memory-verify` (each resident peak under 1 GiB, the child under a 2 GiB address-space cap) and
  `link-memory-scaling` (N/10N/100N synthetic archives; each 10x step within 15x in peak and time).
  Seen red at trunk on Linux: hello, `str` and verify each aborted under the cap (status -6,
  `memory allocation of … failed`, 1.93–1.99 GiB), and the scaling row grew 45.68x in time from 400
  to 4,000 members.
- Identity: hello and `str` byte-identical to trunk (`75f2c22a…df75`, `6b2c7c72…a0df`); the synthetic
  archives' links at 1, 10, 40, 100, 400, 1,000 and 4,000 members byte-identical to trunk's; the
  link-cost row's baseline/candidate pairs; and, in the lane's green record, every ELF executable the
  linking tests write (the self-link, the kernel-profile links, the three-linker writer and oracle
  rows) under trunk's binary and the head's.
- `src/digest_test.lu`: stepped digests equal the one-shot digest at every block and step edge.
- `src/nameidx_test.lu`: the name index across growths, replacement and absence.
- The lane's green record at the final head holds every `END` line, the Linux after-rows and the
  alternating trunk/head timing; its plant record holds the plant's red rows.

### Rulings

- **R-ld07-1, the bound.** (A) 1 GiB resident under a 2 GiB address-space cap, as the brief set it:
  the head measures 0.70 GiB, so about 30% headroom. (B) 768 MiB, which catches smaller regressions
  with less headroom. (C) 1.5 GiB. **Recommend A; implemented.**
- **R-ld07-2, the footprint.** (A) The rows run in `tools/check`, so CI keeps them: cross-cutting,
  with the labelled full run before the merge. (B) The rows run only in lane gauntlets: module.
  **Recommend A; implemented.**
- **R-ld07-3, fenrir's link budget.** Each link's address space can come down from 10 GiB to 2 GiB,
  the memory rows' own cap (about 2.8x the measured peak), with the 16 MiB starved control unchanged.
  A fenrir follow-up; **recommend 2 GiB.**
- **R-ld07-4, the runtime `Map`.** Its per-operation cost grows with its size. ligature no longer
  depends on it for anything that grows with the input. **Recommend a wolf-lang issue with the
  measurement above.**
- **R-ld07-5, the identity suite.** Comparing every linking test's executables against trunk's binary
  needs trunk's binary, so it stays lane evidence, as the link-cost row's frozen control is the
  in-repository form. **Recommend keeping it lane-side.**

## Done-when

- hello's and `str`'s links and `ligature verify` under 1 GiB resident on Linux x86-64, each red at
  trunk and green at the head, measured on the child;
- every output byte-identical to trunk's; determinism unchanged;
- hello's link no slower than trunk's on the same host; the scaling row linear;
- one plant on the green head, red by name at the memory rows;
- the PR open with the five sections, the green record's `END` lines and the plant record.
