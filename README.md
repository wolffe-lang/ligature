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
target/ligature archive libexample.a first.o second.o
target/ligature script-plan tests/fixtures/pax-kernel.ld
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
and extraction paths; `--dependencies SYMBOL` shows section relocation causes and
`--discarded SECTION` shows selected-input discard reasons. Ambiguous locals require `--input MEMBER_ORDINAL`. Unknown options and unsupported formats
fail by name on stderr. AArch64 ELF headers can be read; AArch64 linking,
ELF32, big-endian ELF, REL relocations, BSD archives, thin archives and extended
ELF numbering are not supported. The reader uses bounded positional reads,
not memory mapping. `src/` is one Wolf package; Python and shell are test and
oracle automation, not the linker implementation.

`archive OUTPUT OBJECT...` creates a deterministic GNU/SysV archive, including
its big-endian symbol index. It preserves input order, duplicate basenames and
long names; defined global, weak and COMMON symbols are indexed, local and
undefined symbols are not. Inputs must be validated ELF64 relocatable objects
of one machine, with printable ASCII basenames. Object payloads are bounded to
64 MiB in total, and the encoded archive to 128 MiB. It is a create command, not
an `ar rcs` compatibility interface; thin and BSD formats remain refused.

`script-plan FILE` validates the exact token profile of `tests/fixtures/pax-kernel.ld`
(up to 64 KiB), allowing whitespace and comments. It rejects changes to directives,
entry, PHDR types/flags, patterns, order or expressions. Its JSON explicitly says
`"linking": false`: it does not enable `-T`, interpret a general script or link a
kernel. The high-half address model, script layout/provenance and kernel boot
qualification are unfinished.

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
real musl links with LLD 17 and GNU ld, script-profile refusals, independently
parsed archive indexes and three-linker archive execution, deterministic relinks, deliberate byte
and metadata corruptions, symbol resolution, ten three-linker writer cases, the cc frontend, independent
provenance hashes and resealed corruption witnesses, full byte coverage,
explanation queries, the high-half GOT range fixture and the public runtime
archive. The self-link gate compiles every linker module with the pinned compiler,
links the object set twice, executes that linker and demands a byte-identical
bootstrap relink and an executed hello. Its runtime preflight currently reports
**BLOCKED on [wolf-lang#962](https://github.com/wolffe-lang/wolf-lang/issues/962)**:
the pinned musl runtime loses command-line arguments under both reference
linkers too. CI records this as BLOCKED, neither a passing self-link nor a SKIP, only
for runtime SHA-256 `9d859b9e6b5319f5a6f609e73ba0d71981d2dfa489882648ac9f454cd9db739c`.
Any other runtime digest must pass the hard self-link assertions. `tools/check-core` runs the independent linker/provenance gates. Both a Wolf release carrying the new entry (0.2.36 at the earliest) and
its matching musl bundle are required before self-link execution can qualify;
a runtime-only update leaves 0.2.35-compiled objects without argv.
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
and `notes/ld02a/`; compact-format measurements and individual finding dispositions
are under `notes/ld03/`. The hosted CI gate does not boot the complete PAX corpus.

`tools/oracle` records `readelf`, `nm`, disassembly, extraction traces and runs.
`tools/differ` checks symbol metadata, relocation equations (including measured
TLS/GOT relaxations), segments, entry, initialization order, TLS and runs.
Address/file-offset differences are listed separately. Exact named differences
may be supplied with `--allow`; category-wide waivers are not supported. LLD
and GNU ld differ in four recorded structural categories for hello, so their
structural comparison is **not green** and no blanket equivalence is claimed.
A copied executable with an allocated byte changed must fail the differential.

## Current boundaries

The fourteen-case Linux corpus passes behavior, verification, deterministic
relinks and independent relocation-site validation against both binary oracles.
It still records **87 structural findings**: 28 symbol, 28 segment, 28 retained
relocation-record and three GNU TLS-order differences. Fourteen LLD entry-alias
findings and all three original LLD TLS-order findings are resolved. The three
GNU TLS findings are new comparisons, not unchanged copies of the old ones;
named initializer bytes and memory sizes agree, while binding differences
remain recorded separately. `notes/ld03/findings.json` retains each of the 87
findings by name, raw-record hash, deciding fact and specification reference.
No blanket structural equivalence is claimed.

Fresh native and release kernels from PAX `edbd385c91f2ff0eadb1ab4e52b276f1a1412b63`
ran the same three linker outputs under BIOS and UEFI: **56 live boots, all
halted, all three outputs equal within every guest**. Fifty-two boot rows also
match Linux. The four `pax-fork` rows remain red: PAX prints `fork: io` instead
of the child and status 7 ([pax#175](https://github.com/wolffe-lang/pax/issues/175)).
No expectation changed. These are the cc/glibc-built seed's musl program
outputs, not a linker running inside PAX. Kernel, image, program and transcript
hashes were read twice; `notes/ld02a/` indexes the full evidence. Hosted CI
replays a genuine transcript with corruption fixtures; live boots run on the
Linux test host through PAX's own QEMU harness.

Self-link execution and running ligature itself on PAX remain **BLOCKED on
[wolf-lang#962](https://github.com/wolffe-lang/wolf-lang/issues/962)** under the
exact-runtime-digest CI condition above. Two seed links produced byte-identical
linker binaries, but they lose argv just like the same objects linked by LLD
and GNU ld. A compiler release carrying the new entry and its matching runtime
bundle are both required; a runtime-only update is insufficient.

The compact-format outputs were also exercised in 56 new BIOS/UEFI boots
using those preserved native/release kernel binaries: 52 Linux-equal rows and
the same four named fork failures, with no unexpected failures. No new kernel
was built for this repeat; `notes/ld03/evidence/` records every new transcript.

Each of the fourteen cases has a fresh compact-format Linux qualification and
per-site relocation proof, indexed in `notes/ld03/`. Final byte-name regression
tests preserve legacy JSON name semantics for non-ASCII inputs as well.

The nonallocated 116-byte `.note.wolf.link` seals input hashes, disjoint file
ranges and relocation patches with SHA-256. It is integrity, not a signature
or proof of authorship. `explain` validates the manifest before answering.
Hello retains all 590,358 relocation records. Its interned binary patch table
reduces the embedded manifest from 147,136,512 to 12,414,976 bytes (11.85×),
including 17,765 newly explicit discard/consumed-metadata records. Legacy JSON
manifests remain readable by `verify` and `explain`; no debug sites are omitted. Unwind data has no generated unwind header, strings are not merged,
and AArch64 linking, linker scripts and Mach-O remain future work. The high-half
relocation fixture does not claim support for a kernel linker script. The
supplementary `tests/ld04-controls.py` requires clang/LLD 18: LLD 18.1.3 retains
the GOT load at the edge where LLD 17 refuses. It also measures actual AArch64
assembly-object relocations and an LLD-linked ELF, without executing it or
claiming a compiler/runtime census. Candidate AArch64 linking remains refused.

Licence: GPL-3.0-only with the wolf Training Data Permission (`LICENSE`, `LICENSE-TRAINING-DATA`), as pax, boreutils and den.
