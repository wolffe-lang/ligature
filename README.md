# ligature

A linker written in [wolf](https://github.com/wolffe-lang/wolf-lang), targeting
static x86-64 ELF for Linux and [PAX](https://github.com/wolffe-lang/pax).
**It links a static x86-64 hello that runs on Linux and PAX.** It reads GNU
archives, resolves symbols, collects sections, applies the measured relocation
set and writes an executable with retained relocations and a verifiable
byte-and-patch provenance manifest.

## Build and use

On x86-64 Linux with a C toolchain and Python 3.12:

```sh
tools/fetch-toolchain       # digest-verified wolf 0.2.35 and lupin 0.1.56
tools/fetch-bundle          # digest-verified musl runtime, CRTs and oracle controls
tools/build
target/ligature --version
# Use a matching musl runtime and sysroot; the public GNU/Linux runtime is not musl.
CC="$PWD/target/ligature" LIGATURE_SYSROOT=/path/to/wolf-musl \
  WOLF_RT_LIB=/path/to/musl/libwolf_rt.a wolf build hello.lu -o hello
target/ligature inspect hello.o
target/ligature roundtrip libwolf_rt.a
target/ligature verify hello
target/ligature explain hello --symbol main
target/ligature explain hello --why main
target/ligature --print-plan -o hello hello.o libwolf_rt.a -lpthread -ldl -lm -Wl,--gc-sections
```

`inspect` writes byte-preserving JSON Lines. `roundtrip` checks parsed table
fields by re-serialization, without rewriting the input. `verify` checks ELF
header consistency, section indices, segment coverage and overlap, alignment,
entry placement, the TLS template, provenance digests, complete file coverage
and patch-byte claims when present. `explain` queries symbols, virtual addresses
and extraction paths; ambiguous locals require `--input MEMBER_ORDINAL`. Unknown options and unsupported formats
fail by name on stderr. AArch64 ELF headers can be read; AArch64 linking,
ELF32, big-endian ELF, REL relocations, BSD archives, thin archives and extended
ELF numbering are not supported. The reader uses bounded positional reads,
not memory mapping. `src/` is one Wolf package; Python and shell are test and
oracle automation, not the linker implementation.

The `cc` subset uses `/usr/lib/wolf-musl` unless `LIGATURE_SYSROOT` names another
directory. It supplies `crt1.o`, `crti.o`, `libc.a`, optional `libunwind.a`, and
`crtn.o`; musl provides the `-lpthread`, `-ldl` and `-lm` interfaces. The runtime
archive is supplied by the compiler, not silently replaced. `-fuse-ld=lld` is
accepted and ignored. Use `-nostdlib` for explicit CRT/archive order. Static
non-PIE is the only output mode; no external linker is executed. Archive entries
are discovered lazily, including backward references to earlier archives. Strong
demands extract immediately; weak references do not pull members. The measured
hello sequence now matches all 359 LLD-selected members in order.

## Tests and reference tools

```sh
docker build -t ligature-oracle -f ci/oracle.Containerfile ci
docker run --rm -v "$PWD:/work" ligature-oracle bash -c 'tools/fetch-toolchain && tools/fetch-bundle && tools/check'
```

The PR tier and full tier currently run the same two jobs: planner checks and
the Linux gate. The `full-matrix` label selects the full-tier verdict. The
Linux gate checks formatting, Wolf unit tests, malformed-file/native integration,
real musl links with LLD 17 and GNU ld, deterministic relinks, deliberate byte
and metadata corruptions, symbol resolution, ten three-linker writer cases, the cc frontend, independent
provenance hashes and resealed corruption witnesses, full byte coverage,
explanation queries, the high-half GOT range fixture and the public runtime
archive. The self-link gate compiles every linker module with the pinned compiler,
links the object set twice, executes that linker and demands a byte-identical
bootstrap relink and an executed hello.
No linker, binutils or libc source is fetched or built.

The strict PAX run additionally reads the **complete** PAX runtime, musl libc
and libunwind archives and all nine program input sets. Both pinned linkers
produce executables accepted by `verify`; each program's stdout, stderr and
status agree. `census/pax-link-set.json` contains input hashes, category counts,
example sites, extraction traces and output observations. See
[the link map](docs/MAP.md), [sources and binary pins](docs/SOURCES.md), and
[formats](docs/FORMATS.md).

The exact PAX LLD control, musl runtime and sysroot are available as the
[link-bundle-2026-10-25 release](https://github.com/wolffe-lang/ligature/releases/tag/link-bundle-2026-10-25).
`tools/fetch-bundle` verifies its digest twice and checks every extracted binary.
The public Wolf GNU/Linux runtime cannot substitute for this musl runtime.
CI additionally uses version-pinned distro LLD 17, binutils and musl binary
packages for independent C/assembly fixtures.

The static-writer corpus adds five runnable compiler smoke programs to the nine
initial sets: fourteen cases, linked twice, verified and run against both
oracles on Linux. `tests/static-pax.py LINK-INPUTS` drives it;
`LIGATURE_LINKER` selects a self-linked linker and
`LIGATURE_COMPRESS_EVIDENCE=1` retains verified compressed per-case reports.
The corpus requires every candidate's retained relocation site to validate
independently. Evidence is retained under `notes/ld00-evidence/`, `notes/ld01/`
and `notes/ld02a/`. The hosted CI gate does not boot the complete PAX corpus.

`tools/oracle` records `readelf`, `nm`, disassembly, extraction traces and runs.
`tools/differ` checks symbol metadata, relocation equations (including measured
TLS/GOT relaxations), segments, entry, initialization order, TLS and runs.
Address/file-offset differences are listed separately. Exact named differences
may be supplied with `--allow`; category-wide waivers are not supported. LLD
and GNU ld differ in four recorded structural categories for hello, so their
structural comparison is **not green** and no blanket equivalence is claimed.
A copied executable with an allocated byte changed must fail the differential.

## Current boundaries

Fourteen live PAX BIOS legs compare the same three linker outputs: all three
agree in every guest, and thirteen cases also match Linux. `pax-fork` remains a
named cross-host red: PAX returns `fork: io`, while Linux prints the child and
status 7. Fresh native and release kernels from PAX trunk reproduce syscall 57
returning `-ENOSYS` for all three binaries ([pax#175](https://github.com/wolffe-lang/pax/issues/175)).
No expectation was changed. CI replays a genuine captured transcript and its
corruption cases; it does not boot the private-to-the-run ISO bundle.

The ld01 baseline fourteen-case comparison records 101 structural findings: 28 symbol,
28 segment, 14 entry-alias, 28 retained-relocation and three TLS-order findings.
Five controls with LLD 18.1.3 reproduce all five classes; these are not explained
by the LLD 17/18 high-half kernel bug. The three TLS cases have equal named
initializers and memory size but different variable ordering. Differences remain
recorded, not waived. The output retains unwind data without an unwind header;
string merging still differs from the oracles. Relocation records are now
retained and local/entry normalization has independent positive and negative
fixtures. Baseline findings are not retired without a new per-case comparison.

The nonallocated 116-byte `.note.wolf.link` seals input hashes, disjoint file
ranges and relocation patches with SHA-256. It is an integrity digest, not a
signature or proof of authorship. `explain` validates that manifest before
answering. Self-linking on PAX still requires live qualification; AArch64,
linker scripts and Mach-O remain future work. The high-half relocation fixture tests a post-layout boundary; it does not
claim the frontend accepts a kernel linker script.

Licence: GPL-3.0-only with the wolf Training Data Permission (`LICENSE`, `LICENSE-TRAINING-DATA`), as pax, boreutils and den.
