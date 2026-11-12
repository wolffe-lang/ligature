# ld08 — prediction: where a program-sized link's memory and time go (ligature#35)

Written before any change to `src/`, from reading every module and from a counter build of trunk
`32ec7f43` (phase markers only, kept off the branch) run on Linux x86-64 (Intel i7-12700KF, one
P-core, each link a direct child; resident numbers are the process's own `VmRSS`/`VmHWM`) and on
macOS arm64.

## The inputs, and the table reproduced

Objects from wolf 0.2.39 (`3fc86f77`) with std `2411d868`, the matching musl `libwolf_rt.a`
(47,693,716 bytes, SHA-256 `db50108f…`), musl 1.2.5's CRT, `libc.a` and `libunwind.a` as the link
bundle carries them, pelt at `b80d6570`. Each program was compiled by that compiler with a
cc-shaped `WOLF_LD` that kept its objects and argv; each link below is the kept argv, run by
trunk's ligature (built by its pinned wolf 0.2.38 with a static `cc` link) as a direct child on one
CPU. Three rounds, interleaved with the image's `cc` + `ld.lld` 18.1.8:

| program | ligature: wall, peak resident | ld.lld: wall, peak resident | output bytes, ligature / ld.lld |
|---|---|---|---|
| hello | 7.57–7.67 s, 640.9 MiB | 0.046–0.048 s, 103.7 MiB | 46,004,568 / 15,356,824 |
| `std.net` + `std.process` | 7.99–8.11 s, 670.6 MiB | 0.047–0.049 s, 105.0 MiB | 48,327,088 / 15,929,864 |
| pelt | 9.01–9.30 s, 750.6 MiB | 0.053–0.060 s, 123.6 MiB | 58,901,840 / 24,776,664 |
| ligature itself | 7.95–8.56 s, 670.5 MiB | 0.048–0.049 s, 107.0 MiB | 48,545,744 / 16,552,416 |

The issue's hello output (46,004,568 bytes) is reproduced exactly; the other three differ from the
issue's by 48–192 bytes in both linkers' outputs alike (the objects embed their source paths). Each
pair of outputs runs identically.

## What a link holds

Hello selects 371 objects (35 members of the runtime archive, 326 of `libc.a`, 9 of `libunwind.a`,
crt1/crti/crtn and one program object), 23,030 symbols and 668,446 relocation entries, of which
634,196 are in live sections. Pelt selects 383 objects, 26,385 symbols, 691,267 entries (667,387
live). The output's bytes by class:

| class | hello | pelt |
|---|---|---|
| allocated (the program) | 547,714 | 9,390,242 |
| `.debug_*` (kept, not merged) | 16,844,695 | 17,129,425 |
| retained relocations (`.rela.*`) | 15,220,704 | 16,017,288 |
| provenance manifest | 12,967,936 | 15,581,184 |
| `.symtab`, `.strtab`, `.shstrtab` | 391,192 | 728,588 |
| other | 17,810 | 17,810 |

The manifest's parts, hello / pelt: metadata JSON 4,875,900 / 6,368,894 bytes (of which the
`discarded` list is 2,899,647 / 2,570,567), a pooled-string table of 193,999 / 249,036 strings
(1,926,259 / 2,702,251 bytes), and 634,196 / 667,387 patch rows (6,163,285 / 6,509,494 bytes).

**How the 47.7 MB runtime is held.** Never whole. The link reads its 344 member headers, its
417,522-byte symbol index (4,286 names), the selected members' section headers, symbol and string
tables, their live sections' bytes and their relocation tables, each by positional reads. It is
also hashed twice over: once as an input (47.7 MB) and once member by member (the selected members
of all three archives come to 45,566,808 bytes).

## Where the memory goes (hello, Linux, resident after each phase)

| phase | resident after | growth | owner |
|---|---|---|---|
| resolve | 62.0 MB | 60.6 MB | the runtime's 35 members +41 MB, `libc.a`'s 326 +14 MB, the index +3 MB: per-symbol key building, every selected member's string tables, section-name reads; nearly all of it garbage left in the root arena |
| read | 124.2 MB | 62.2 MB | 668,446 `Reloc` records (26.7 MB, reserved) and the raw tables, read as 64 KiB parts gathered into a second list (about 32 MB) |
| collect | 125.3 MB | 1.2 MB | |
| load | 156.6 MB | 31.2 MB | live sections' bytes (17.4 MB) with the gathered parts |
| place | 176.1 MB | 19.5 MB | zero-filled output sections (17.4 MB), then the bytes copied in |
| relocate | 193.3 MB | 17.2 MB | the global relocation-site index (2,097,152 slots, 16.8 MB) |
| symbols | 199.8 MB | 6.5 MB | |
| retained | 237.2 MB | 37.4 MB | 15.2 MB of `.rela` entries, and per-relocation copies |
| inputs | 239.5 MB | 2.3 MB | hashing in freed regions |
| manifest, iteration 1 | 254.4 MB | 15 MB kept; the region peaks at 578.8 MB | patch attribution 156 MB (hex strings, interning), `ranges` 71 MB and `sections` 40 MB (each `copy` of an output or atom copies its bytes), `discarded` 28 MB, the patch-site index again 17 MB, the final concatenation 35 MB |
| manifest, iteration 2 | 629.3 MB | 374.9 MB | the second region's freed memory is not returned to the system by the allocator (the first one's was) |
| image, seal, write, verify | 665.1 MB | 35.8 MB | the 46 MB file image and the verify read-back, mostly reusing freed memory |

**Owners at hello's 640.9 MiB peak:** the root arena's live state and garbage before the manifest
(about 254 MB), one manifest iteration's working set (about 324 MB, freed, but standing on top of
the root at its own peak), and allocator slack: the second iteration's freed region held resident
(about 50 MB more than the first iteration reached). The output image itself costs little at the
peak because it reuses the freed manifest region; it would cost 46 MB on its own.

**Pelt's extra 110 MiB** (774.8 MB against 665.1 MB at the end): load and place +29 MB (9.4 MB
more allocated bytes, held twice), relocate and symbols +5 MB, resolve, read and retained +5 MB
together (3,355 more symbols; sh.o is a 9.2 MB object), the manifest's kept bytes +3 MB, and the
retained second manifest region +67 MB (1.5 MB more metadata, 55,000 more pooled strings and
33,000 more patch rows).

**Standalone `ligature verify`** peaks at 262 MiB for hello and 306 MiB for pelt: the manifest read
as 64 KiB parts and gathered (26 MB), the metadata decoded as a JSON tree with the pooled strings
interned (89 MB), and both streaming passes over the patch rows allocating a four-element list
literal per row (about 70 MB each).

## Where the time goes (hello, Linux, 7.97 s with the markers)

| phase | seconds | why |
|---|---|---|
| hashing: inputs | 2.32 | 104 MB (every input file and every selected member) at about 45 MB/s: the pinned SHA-256 allocates a fresh schedule and buffer for each 64-byte block |
| hashing: seal | 1.25 | the 46 MB image and the 13 MB manifest |
| hashing: in-link verify | 1.30 | the same 59 MB, read back |
| manifest, two iterations | 1.35 | each rebuilds all 634,196 patch rows (0.53 s: two hex strings and four interned strings per row) and the metadata |
| verify walk | 0.24 | one positional read per symbol and per retained relocation |
| patch checks in verify | 0.32 | one positional read and one region per patch row |
| place | 0.23 | zero-fill and copy, a byte at a time |
| patch-table decode in verify | 0.27 | |
| everything else | 0.67 | resolve 0.09, visibility 0.01, read 0.08, collect 0.10, load 0.04, relocate 0.10, symbols and retained 0.08, image 0.12, write 0.03, manifest read 0.02 |

So 4.87 s of hello's 7.97 s is SHA-256 over 222 MB, and most of the rest is building the manifest
twice and verifying it a row at a time.

## The changes, with the predicted rows after each (hello / pelt on the Linux host)

Each change keeps every output byte-identical; the predictions are cumulative.

1. **A whole-block SHA-256 core** (FIPS 180-4 §6.2, unrolled, no allocation per block; measured
   in a probe at 320 MiB/s on the Linux host against the pinned module's 44 MiB/s, digests equal at
   every block edge). Hashing 4.9 s → 0.7 s. Wall 7.6 / 9.0 s → 3.4 / 4.6 s. Memory unchanged.
2. **Verify in bounded memory, after the link's own state is gone**: the manifest read without
   gathered parts, no per-row list literal, patch bytes checked against windows read in bulk, the
   walk reading each table once. Standalone verify 262 / 306 MiB → about 80 / 100 MiB, and 0.6 s
   faster. The link's peak is unchanged until 3.
3. **The manifest built once**: the patch table (pooled strings and rows) is the same in every
   fixed-point iteration, so it is computed once, interned from raw bytes without hex strings; each
   iteration builds only the metadata, in a region, reading outputs and atoms by index (no copies);
   the manifest is never concatenated into one list. Peak 641 / 751 → about 270 / 320 MiB; wall
   −1.2 s.
4. **No file image**: the output is written in file order from its pieces, and the seal hashes the
   same pieces. Peak −10 to −46 MiB; wall −0.15 s.
5. **Section bytes read once**: each live section is read into its own buffer and relocated in
   place, with its pristine bytes re-read per object only while that object's relocations and patch
   rows are computed; no zero-filled output copies. Peak −50 / −70 MiB.
6. **Relocation tables in regions, compact records, a per-object site index**: read 62 → about 20
   MB; the 16.8 MB global index goes. Peak −55 MiB.
7. **Resolution's temporaries in regions**: each object's parse in its own region, carrying out
   only its sections, names and symbols. Resolve 60 → about 15 MB.
8. **Retained relocations encoded at exact size**, without per-relocation copies: 37 → 15 MB.

**Predicted after all eight:** hello about 90–110 MiB and 1.0–1.2 s; pelt about 120–140 MiB and
1.3–1.6 s; standalone verify under 100 MiB for both. The N/10N/100N scaling row stays linear (no
change adds a per-item search). The bounds the contract names (hello under 192 MiB, pelt under 256
MiB, both measured on the child under an address-space cap below today's peak) look reachable with
margin. Hello's 1 s is at the edge: the manifest's design hashes 163 MB per link (every input,
every selected member, the output and the manifest) and the in-link verify hashes the output and
manifest again (222 MB in all, about 0.69 s at the measured core speed), so the rest of the link
must fit in about 0.3 s. If it does not, the number reached and that floor are the answer.

**The output-size question** is measured above: the retained relocations (15.2 / 16.0 MB) and the
manifest (13.0 / 15.6 MB) make up 28.2 / 31.6 MB of 46.0 / 58.9 MB. Most of the rest of the
difference from lld is a third, separate cost: `.debug_str` is kept unmerged (hello 6,138,902
bytes against lld's merged 4,130,291). It goes to a decision with options; the default does not
change in this lane.
