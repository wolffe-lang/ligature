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

## Inputs verified

## Evidence index

## Done-when
