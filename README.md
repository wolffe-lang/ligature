# ligature

A linker written in [wolf](https://github.com/wolffe-lang/wolf-lang), targeting
static x86-64 ELF for Linux and [PAX](https://github.com/wolffe-lang/pax).
**It does not link programs yet.** This first version reads objects and GNU
archives, verifies executables, inventories link inputs and prints the link
plan requested by a `cc`-style command line.

## Build and use

On x86-64 Linux with a C toolchain and Python 3.12:

```sh
tools/fetch-toolchain       # digest-verified wolf 0.2.35 and lupin 0.1.56
tools/build
target/ligature --version
target/ligature inspect hello.o
target/ligature roundtrip libwolf_rt.a
target/ligature verify hello
target/ligature --print-plan -o hello hello.o libwolf_rt.a -lpthread -ldl -lm -Wl,--gc-sections
```

`inspect` writes byte-preserving JSON Lines. `roundtrip` checks parsed table
fields by re-serialization, without rewriting the input. `verify` checks ELF
header consistency, section indices, segment coverage and overlap, alignment,
entry placement and the TLS template. Unknown options and unsupported formats
fail by name on stderr. AArch64 ELF headers can be read; AArch64 linking,
ELF32, big-endian ELF, REL relocations, BSD archives, thin archives and extended
ELF numbering are not supported. The reader uses bounded positional reads,
not memory mapping. `src/` is one Wolf package; Python and shell are test and
oracle automation, not the implementation of the ELF or archive readers.

## Tests and reference tools

```sh
docker build -t ligature-oracle -f ci/oracle.Containerfile ci
docker run --rm -v "$PWD:/work" ligature-oracle bash -c 'tools/fetch-toolchain && tools/check'
```

The PR tier and full tier currently run the same two jobs: planner checks and
the Linux gate. The `full-matrix` label selects the full-tier verdict. The
Linux gate checks formatting, Wolf unit tests, malformed-file/native integration,
real musl links with LLD 17 and GNU ld, deterministic relinks, deliberate byte
and metadata corruptions, symbol resolution and the public runtime archive.
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
substituted for PAX's musl-targeted runtime. Evidence is retained under
`notes/ld00-evidence/`; this is not a claim that CI runs the complete PAX corpus.

`tools/oracle` records `readelf`, `nm`, disassembly, extraction traces and runs.
`tools/differ` checks symbol metadata, relocation equations (including measured
TLS/GOT relaxations), segments, entry, initialization order, TLS and runs.
Address/file-offset differences are listed separately. Exact named differences
may be supplied with `--allow`; category-wide waivers are not supported. LLD
and GNU ld differ in four recorded structural categories for hello, so their
structural comparison is **not green** and no blanket equivalence is claimed.
A copied executable with an allocated byte changed must fail the differential.

## Next

The census is the input contract for static linking: symbol and archive
resolution, 13 observed relocation types, section collection, CRT startup,
TLS and retained unwind data. Provenance notes and `explain` have a documented
format but no writer yet. ELF output, AArch64 linking, linker scripts and
Mach-O are future work.

Licence: GPL-3.0-only with the wolf Training Data Permission (`LICENSE`, `LICENSE-TRAINING-DATA`), as pax, boreutils and den.
