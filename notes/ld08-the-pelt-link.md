# ld08 — the pelt link: memory, time and size for a program-sized link (ligature#35)

## Prediction

`notes/ld08-prediction.md`, committed before any change to `src/`, attributes trunk `32ec7f43`'s
floor from a counter build's phase markers (kept off this branch) on Linux x86-64 and macOS arm64,
and predicts each change's effect. In short: hello's 640.9 MiB was the root arena's live state and
garbage before the manifest (about 254 MB), one manifest iteration's working set standing on top of
it (about 324 MB) and allocator slack; its 7.6 s was 4.87 s of SHA-256 over 222 MB at about
45 MB/s (a schedule and a buffer allocated per 64-byte block), the manifest built twice, and verify
a row at a time. Predicted after all eight changes: hello about 90–110 MiB and 1.0–1.2 s, pelt
about 120–140 MiB and 1.3–1.6 s, standalone verify under 100 MiB.

What the measurement showed against it:

- **Memory** came in above the prediction (hello 139.6 MiB, pelt 175.0 MiB against 90–110 and
  120–140) but well inside the bounds. The peak is now the link's own live state when the metadata
  is built, everything the write still needs (pelt, in MB): resolution 21, the relocation records
  and ranges 36 (the prediction expected about 20), the live sections' relocated bytes and their
  places 35, the patch table 32 (pooled strings, their index and the encoded rows, which the
  prediction did not count: it has to live from the first object's attribution to the write), the
  output's symbols and retained relocations 24, and one metadata round's working set on top.
- **Time** came in above it too (hello 1.40 s, pelt 1.67 s against 1.0–1.2 and 1.3–1.6). The
  hashing was predicted right: 0.67 s of hello's link and 0.79 s of pelt's, at the measured
  320 MB/s. The rest was not 0.3 s but 0.75 s for hello and 0.89 s for pelt: attributing every
  patch row (pooling its before and after bytes and encoding it; 0.17 s for pelt's 667,387 rows),
  the in-link verify's two passes over those rows (0.14 s), its metadata and pooled strings
  (0.06 s), relocating (0.06 s), and the metadata's two fixed-point rounds (0.07 s).

## Forbidden

No linker, binutils, libc or kernel source was read: not lld, mold, gold, GNU ld, ld64, zig's
linker, musl, glibc or any kernel. The sources used were the ELF gABI, the x86-64 and AArch64
psABIs, FIPS 180-4 (for SHA-256, sections 4.2.2, 5.1.1, 5.3.3 and 6.2) and black-box runs of
ld.lld 18.1.8, `cc` and `objdump`. ligature's own std pin was read where its behaviour had to be
matched exactly (`std.json`'s parser, so the metadata fast path builds the tree `json.parse`
builds). No output's bytes changed: every link below is byte-identical to trunk's.

## Inputs verified

- ligature trunk `32ec7f43` (base); pinned wolf 0.2.38 and its std for the build.
- The measured programs, compiled by wolf 0.2.39 (`3fc86f77`) with std `2411d868` through a
  cc-shaped linker that kept each link's argv and objects (`link.json` and the files it names):

| program | objects | `link.json` SHA-256 |
|---|---|---|
| hello | 2 | `44a27824d2f2f4258df137a70c8caf19e32119dd753030db482286b3de4e592b` |
| `std.net` + `std.process` | 8 | `63b6ed73c52b35f169921eee70f37b85f6f82736f74ba3a4d5220e4af9392fb3` |
| pelt at `b80d6570` | 14 | `4177d8502035fa198d55213eca175530cce7a507bad4ec06b148d8b3bca18cfb` |
| ligature itself | 27 | `eb985dd40ae566932c0edba0536d61b2e3de3d5bc4d5f6a69925ab3f177951b3` |

- The musl `libwolf_rt.a` in each: 47,693,716 bytes, SHA-256
  `db50108f80eae4423c44e708c739f17f09ceaa3314196b3a31fd563b2b36748d`; pelt's `sh.o` 9,242,328 bytes,
  `0160f2c3293e7c0eefaf802725a1ded642c9cc3f32b56c521dea2537501ce133`.
- The sysroot those links name (musl 1.2.5's CRT and libraries as the 0.2.39 release ships them):
  `crt1.o` 5,560 bytes, `51dba24287eb9b1e74f3c7cb8ea5464491d3a4ba54c016722f149179d08f90f6`;
  `crti.o` 2,816 bytes, `5cbc84c78a23cdddda0db8cdcd5ec3b5a15b6b555510bd97e4c5a0334aca7b49`;
  `crtn.o` 2,760 bytes, `d884ee5f9120490b98bb43496f88983ee379a0d2ebf027574fcca7eae9aaa1e7`;
  `libc.a` 10,961,970 bytes, `8e69a73c464a86fd8b278f3aa08ab2640b720157e92b45a2d34441c22248ddd4`;
  `libunwind.a` 201,794 bytes, `264296d61db52859cc7a8cd6a7a09fc62bde189aa3ea8867fb62ef5129b694bc`.
- Trunk's hello output reproduced ligature#35's exactly (46,004,568 bytes); the three others differ
  from the issue's by 48–192 bytes in both linkers' outputs alike, because the objects embed their
  source paths.

## Evidence index

### Before and after, Linux x86-64

The same host, one P-core, each link a direct child; the resident peak is the child's own
`ru_maxrss`. Trunk is `32ec7f43`, built by its pinned wolf 0.2.38 with a static `cc` link.

Three rounds each; trunk's rows are the prediction's (interleaved with ld.lld 18.1.8 there):

| program | trunk: wall, peak | head: wall (CPU), peak | ld.lld: wall, peak | output, identical to trunk's |
|---|---|---|---|---|
| hello | 7.57–7.67 s, 640.9 MiB | 1.40–1.49 s (1.40–1.41), 139.6 MiB | 0.046–0.048 s, 103.7 MiB | 46,004,568 bytes, `2ccd873c…` |
| `std.net` + `std.process` | 7.99–8.11 s, 670.6 MiB | 1.50–1.51 s (1.50), 151.0 MiB | 0.047–0.049 s, 105.0 MiB | 48,327,088 bytes, `41a08717…` |
| pelt | 9.01–9.30 s, 750.6 MiB | 1.67–1.68 s (1.66–1.67), 175.0 MiB | 0.053–0.060 s, 123.6 MiB | 58,901,840 bytes, `dbe08396…` |
| ligature itself | 7.95–8.56 s, 670.5 MiB | 1.48 s (1.47–1.48), 147.9 MiB | 0.048–0.049 s, 107.0 MiB | 48,545,744 bytes, `2878d17d…` |

Standalone `ligature verify` of hello's and pelt's outputs: 262 and 306 MiB at trunk, 62 and 85 MiB
at the head (0.41 s and 0.50 s). The green record's `time-rows` and `link-memory` rows measure the
same links again beside trunk's, interleaved.

### Where the time goes now (Linux, seconds, from a counter build's phase markers)

| phase | hello | pelt |
|---|---|---|
| resolve | 0.053 | 0.054 |
| read relocation tables and section records | 0.056 | 0.056 |
| collect (`--gc-sections`) | 0.018 | 0.019 |
| load and place the live sections | 0.024 | 0.059 |
| relocate and attribute, object by object (relocating 0.057 / 0.063, attributing every patch row 0.148 / 0.173) | 0.226 | 0.264 |
| output symbols and retained relocations | 0.061 | 0.069 |
| **hash inputs and selected members** | **0.324** | **0.349** |
| metadata, two fixed-point rounds | 0.049 | 0.066 |
| **seal (hash the file and the manifest)** | **0.171** | **0.218** |
| write | 0.024 | 0.024 |
| free the link's region | 0.007 | 0.009 |
| verify: walk the tables | 0.030 | 0.033 |
| **verify: hash the file and the manifest** | **0.178** | **0.225** |
| verify: read the manifest, its metadata and pooled strings; check the metadata | 0.068 | 0.095 |
| verify: the patch rows, two passes | 0.127 | 0.137 |
| total, with the markers | 1.424 | 1.683 |

Hashing (bold) is 0.67 s of hello's link and 0.79 s of pelt's.

### macOS arm64 (the same objects)

Three rounds each, wall time with CPU where it differs; macOS's allocator keeps more resident, so
the peaks run 30–45 MiB above Linux's:

| program | trunk | head | `verify` at the head |
|---|---|---|---|
| hello | 8.22–8.47 s, 781 MiB | 1.53–1.78 s (1.52–1.55), 185–188 MiB | 0.44 s, 63 MiB |
| `std.net` + `std.process` | 8.63–8.68 s, 821–822 MiB | 1.63–1.65 s, 185 MiB | 0.47 s, 80 MiB |
| pelt | 9.78–9.87 s, 933 MiB | 1.81–1.83 s, 207 MiB | 0.53 s, 86 MiB |
| ligature itself | 8.55–8.60 s, 815 MiB | 1.61–1.62 s, 187 MiB | 0.46 s, 72 MiB |

Every output byte-identical to trunk's Linux outputs.

### The changes, by owner

| change | commits | effect |
|---|---|---|
| the SHA-256 core: unrolled from FIPS 180-4, no allocation per block, 1 MiB steps | `efc7a03`, `0ac2694`, `a450931` | 44 → 320 MB/s; hashing 4.87 → 0.67 s for hello |
| reads: one positional read up to 1 MiB, longer ranges gathered part by part | `6707b3c` | no gathered second copy |
| verify: windows of the file, rows decoded in place, after the link's region is freed | `f039e73`, `a5be890`, `d001d44`, `c51d0ca`, `b9daedf`, `bb55184`, `a0a3e07`, `4d5ec50`, `4dd3f9d` | standalone verify 262 / 306 → 62 / 85 MiB |
| relocation tables, atoms and sites as per-object ranges, decoded in regions | `66930fc`, `1e00823`, `8183290`, `dddd937` | read 62 → about 35 MB |
| the patch table built once, rows from fields | `b00e926`, `b9faf71`, `805ee24`, `803fac3`, `fa32242`, `b169b69` | the manifest's 324 MB working set gone |
| sections relocated in place from pristine copies; the file sealed and written from its pieces | `e42d211` | no zero-filled output copies, no 46–59 MB image |
| resolution's temporaries in regions; winners settled once | `558b8b5`, `5a7b316`, `f2656b7` | resolve 60 → 19 MB |
| the output's symbols and retained relocations encoded in place | `9560db7`, `462e516` | retained 37 → 17 MB |
| the metadata: one list, reserved; the stable round's kept | `88e03f9`, `9241803` | one metadata build fewer |
| collection by worklist | `eac3c56`, `2c3652d` | |

### Rows

`tests/link-memory.py` (in `tools/check`, so CI runs it), each link a direct child under a
512 MiB address-space cap, its resident peak the child's own `ru_maxrss`:

- `link-memory-hello`, `link-memory-str`: under 192 MiB; `link-memory-self` (ligature's own objects
  linked as a program): under 256 MiB; `link-memory-verify` (`ligature verify` of hello's output):
  under 192 MiB.
- `link-memory-captured-NAME` with `--captured NAME:MIB:DIR`: a captured link under its bound. The
  lane's gauntlet passes hello, the net/process program and ligature itself at 192 MiB and pelt at
  256 MiB.
- `link-memory-scaling`: N/10N/100N synthetic archives (N = 40), each 10x step within 15x in peak
  and in time.
- `link-identity-CASE` with `--baseline`: every row's output byte-identical to the baseline
  linker's.

The lane's rig (`notes/ld08/rig/`, run by the recorder in steps mode from a clean checkout) adds:

- `time-NAME` for the four captured programs: the fastest of three CPU times, trunk and the
  candidate interleaved on one CPU, under 2 s; hello's 1 s reported against its number.
- `time-identity`: every output of a program, by either linker in any round, one file.
- `identity-suite`: every ELF executable the linking tests write, under trunk's binary and the
  head's, byte-identical.

Seen red first: the red-first record runs the memory and time rows at `b61fed6`, the commit that
adds the bounds, before any change to the linker; every bounded row fails there by name.

### Decisions

Each decision is the owner's; the options are measured, and none of them is implemented here.

- **Decision 1, what an output carries by default.** Measured at trunk and unchanged here (the
  outputs are byte-identical), hello / pelt in bytes:

  | class | hello | pelt |
  |---|---|---|
  | allocated (the program) | 547,714 | 9,390,242 |
  | `.debug_*`, kept and not merged | 16,844,695 | 17,129,425 |
  | retained relocations (`.rela.*`) | 15,220,704 | 16,017,288 |
  | provenance manifest | 12,967,936 | 15,581,184 |
  | `.symtab`, `.strtab`, `.shstrtab` | 391,192 | 728,588 |
  | other | 17,810 | 17,810 |
  | the output | 46,004,568 | 58,901,840 |
  | ld.lld 18's output, same inputs | 15,356,824 | 24,776,664 |

  The retained relocations and the manifest are 28.2 / 31.6 MB of 46.0 / 58.9 MB; most of the rest
  of the gap to lld is `.debug_str` kept unmerged (hello 6,138,902 bytes against lld's merged
  4,130,291). Options: (A) keep today's default, everything embedded. (B) Write the manifest as a
  sidecar file by default, bound to the output by the digest the 116-byte note already holds, and
  embed it on request: 33.0 / 43.3 MB. (C) As B, with the retained relocations in the sidecar too
  (each manifest row already names its patch's site, kind, symbol and addend, so verify can check
  the bytes from the sidecar alone): 17.8 / 27.3 MB, 16% / 10% over lld. (D) Separately, merge
  `.debug_str` (SHF_MERGE and SHF_STRINGS): about 2 MB more off each. **Recommend C, with an
  option that embeds both as today, and D as its own change**: on a live image every output lands in
  RAM, and C keeps every byte of the evidence one flag away. Each moves output bytes, so each needs
  the ruling first.
- **Decision 2, hello's 1 s.** Not reachable without changing what a link hashes or verifies. The
  manifest's design hashes every input file and every selected archive member (104 MB for hello,
  the runtime archive twice over: whole, and member by member), seals the output and the manifest
  (59 MB), and the in-link verify reads both back and hashes them again (59 MB): 222 MB at the
  measured 320 MB/s is 0.69 s, and the rest of the link (resolving, reading, relocating, attributing
  and encoding 634,196 patch rows, the metadata's two rounds, writing, and verify's two passes over
  the rows) is about 0.8 s more. Options: (A) accept hello at 1.40 s and pelt under 2 s.
  (B) Let the in-link verify skip re-hashing the file it has just sealed from the same pieces, still
  checking every structure and patch row; a standalone `ligature verify` hashes everything as
  today: about 0.19 s off hello, 0.24 s off pelt. (C) Hash in more than one thread: the brief asks
  for one. **Recommend A**, with B as a follow-up if a live image's link time matters more than
  re-reading its own write.
- **Decision 3, the bounds.** (A) Keep hello's 192 MiB and pelt's 256 MiB under the 512 MiB cap, as
  the brief set them: the head measures 139.6 and 175.0 MiB on Linux x86-64. (B) Tighten
  to 160 and 208 MiB, catching smaller regressions with less headroom (macOS arm64 already sits at
  185–188 MiB for hello, its allocator holding more resident). **Recommend A.**
- **Decision 4, the PAX row.** The pelt link's resident peak on Linux x86-64 is 175.0 MiB, its
  address space under the rows' 512 MiB cap; the 2 GiB guest's 1.48 GB is about 8 times that. The
  commit to pin is this branch's head once merged. **Recommend** that the image's linker choice be
  retaken on that pin with the guest's own row.
- **Decision 5, fenrir's link budget.** Every measured link now fits a 512 MiB address-space cap with
  a resident peak under 176 MiB. **Recommend** fenrir's budget drop to 512 MiB in its own
  follow-up.

## Done-when

- [x] The floor attributed before any change, with predictions per change:
  `notes/ld08-prediction.md` (`74a0f18`), the first commit.
- [x] The bound, red first: the memory rows (`b61fed6`) fail at the commit that adds them, before
  any change to the linker, and pass at the head: hello 139.6 MiB (under 192), pelt
  175.0 MiB (under 256), each under a 512 MiB address-space cap, on Linux x86-64.
- [x] Time: pelt 1.67 s, under 2 s on one thread. Hello 1.40 s: 1 s is not reached,
  and decision 2 gives the measured reason. The N/10N/100N scaling row stays linear.
- [x] Size: measured by class and put as decision 1; the default is unchanged.
- [x] Every output byte-identical to trunk's: the four captured programs (in the memory rows, the
  time rows and every round), and every ELF executable the linking tests write, the self-link and
  the kernel-profile links among them (the identity suite). Every program linked twice or more gave
  one file.
- [x] The PAX row's facts for its own lane: decision 4.
- [x] fenrir's budget: decision 5.
- [x] One plant on the green head, red by name at the memory rows.
- [x] The green record at the head with every `END` line, the red-first record, the plant record.
