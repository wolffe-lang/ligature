# ligature

A linker written in [wolf](https://github.com/wolffe-lang/wolf-lang), targeting
static x86-64 ELF for Linux and [PAX](https://github.com/wolffe-lang/pax).
**It links a static x86-64 hello that runs on Linux and PAX.** It reads GNU
archives, resolves symbols, collects sections, applies the measured relocation
set and writes an executable with a verifiable provenance note.

## Build and use

On x86-64 Linux with a C toolchain and Python 3.12:

```sh
tools/fetch-toolchain       # digest-verified wolf 0.2.35 and lupin 0.1.56
tools/build
target/ligature --version
# Use a matching musl runtime and sysroot; the public GNU/Linux runtime is not musl.
CC="$PWD/target/ligature" LIGATURE_SYSROOT=/path/to/wolf-musl \
  WOLF_RT_LIB=/path/to/musl/libwolf_rt.a wolf build hello.lu -o hello
target/ligature inspect hello.o
target/ligature roundtrip libwolf_rt.a
target/ligature verify hello
target/ligature --print-plan -o hello hello.o libwolf_rt.a -lpthread -ldl -lm -Wl,--gc-sections
```

`inspect` writes byte-preserving JSON Lines. `roundtrip` checks parsed table
fields by re-serialization, without rewriting the input. `verify` checks ELF
header consistency, section indices, segment coverage and overlap, alignment,
entry placement, the TLS template and provenance digests when present. Unknown options and unsupported formats
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
non-PIE is the only output mode; no external linker is executed.

## Tests and reference tools

```sh
docker build -t ligature-oracle -f ci/oracle.Containerfile ci
docker run --rm -v "$PWD:/work" ligature-oracle bash -c 'tools/fetch-toolchain && tools/check'
```

The PR tier and full tier currently run the same two jobs: planner checks and
the Linux gate. The `full-matrix` label selects the full-tier verdict. The
Linux gate checks formatting, Wolf unit tests, malformed-file/native integration,
real musl links with LLD 17 and GNU ld, deterministic relinks, deliberate byte
and metadata corruptions, symbol resolution, ten three-linker writer cases, the cc frontend, independent
provenance hashes and corruption witnesses, the high-half GOT range fixture,
and the public runtime archive.
No linker, binutils or libc source is fetched or built.

The strict PAX run additionally reads the **complete** PAX runtime, musl libc
and libunwind archives and all nine program input sets. Both pinned linkers
produce executables accepted by `verify`; each program's stdout, stderr and
status agree. `census/pax-link-set.json` contains input hashes, category counts,
example sites, extraction traces and output observations. See
[the link map](docs/MAP.md), [sources and binary pins](docs/SOURCES.md), and
[formats](docs/FORMATS.md).

There is a documented CI gap: the exact PAX LLD build, musl runtime and sysroot
are currently available only in the PAX dev ISO. They are tested locally with
`tools/strict-pax LINK-INPUTS` inside the pinned Linux container; CI instead
uses version-pinned distro LLD 17, binutils and musl binary packages with
generated C/assembly fixtures. The public Wolf GNU/Linux runtime cannot be
substituted for PAX's musl-targeted runtime. The new static-writer run adds the five other runnable top-level compiler smoke
programs to those nine sets: fourteen unique cases, linked twice, verified and
run against both oracles on Linux. `tests/static-pax.py LINK-INPUTS` drives it.
Evidence is retained under `notes/ld00-evidence/` and `notes/ld01/evidence/`;
this is not a claim that CI runs the complete PAX corpus.

`tools/oracle` records `readelf`, `nm`, disassembly, extraction traces and runs.
`tools/differ` checks symbol metadata, relocation equations (including measured
TLS/GOT relaxations), segments, entry, initialization order, TLS and runs.
Address/file-offset differences are listed separately. Exact named differences
may be supplied with `--allow`; category-wide waivers are not supported. LLD
and GNU ld differ in four recorded structural categories for hello, so their
structural comparison is **not green** and no blanket equivalence is claimed.
A copied executable with an allocated byte changed must fail the differential.

## Current boundaries

The fourteen-case comparison records 101 structural findings: 28 symbol,
28 segment, 14 entry-alias, 28 retained-relocation and three TLS-order findings.
Five controls with LLD 18.1.3 reproduce all five classes; these are not explained
by the LLD 17/18 high-half kernel bug. The three TLS cases have equal named
initializers and memory size but different variable ordering. Differences remain
recorded, not waived. The output retains unwind data without an unwind header;
retained relocation records and string merging still differ from the oracles.

The nonallocated `.note.wolf.link` seals input hashes and section ranges with
SHA-256. It is an integrity digest, not a signature. Byte-level patch provenance
and `explain`, self-linking on PAX, AArch64, linker scripts and Mach-O are future
work. The high-half relocation fixture tests a post-layout boundary; it does not
claim the frontend accepts a kernel linker script.

Licence: GPL-3.0-only with the wolf Training Data Permission (`LICENSE`, `LICENSE-TRAINING-DATA`), as pax, boreutils and den.
