# ligature

A linker written in [wolf](https://github.com/wolffe-lang/wolf-lang), targeting
static x86-64 ELF for Linux and [PAX](https://github.com/wolffe-lang/pax), with
a measured AArch64 static-link subset.
**It links a static x86-64 hello that runs on Linux and PAX, and PAX paging
kernels that boot under BIOS and UEFI.** It reads GNU
archives, resolves symbols, collects sections, applies the measured relocation
set and writes an executable with retained relocations and a verifiable
byte-and-patch provenance manifest.

## Build and use

On x86-64 Linux with a C toolchain and Python 3.12:

```sh
tools/fetch-toolchain       # digest-verified wolf 0.2.38, lupin 0.1.60 and the release's musl runtime
tools/fetch-bundle          # licensed, digest/MANIFEST-verified musl inputs and oracle controls
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
fail by name on stderr. ELF32, big-endian ELF, REL relocations, BSD archives, thin archives and extended
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
`"linking": false`: that command performs preflight only. To link the profile,
use `ligature -nostdlib -T tests/fixtures/pax-kernel.ld -o kernel.elf OBJECT...`.
The writer emits three page-separated LOADs (RX, R, RW), absolute script bounds,
ordered wildcard/COMMON layout and separate script-discard attribution. The
script itself is a hashed input. Virtual addresses remain unsigned 64-bit;
file positions are independently bounded. Unknown allocated orphans and every
script outside this exact profile are refused. General linker scripts are not
implemented.

The `cc` subset uses `/usr/lib/wolf-musl` unless `LIGATURE_SYSROOT` names another
directory. It supplies `crt1.o`, `crti.o`, `libc.a`, optional `libunwind.a`, and
`crtn.o`; musl provides the `-lpthread`, `-ldl` and `-lm` interfaces. The runtime
archive is supplied by the compiler, not silently replaced. `-fuse-ld=lld` is
accepted and ignored. Use `-nostdlib` for explicit CRT/archive order. Static
non-PIE is the only output mode; no external linker is executed. Archive entries
are discovered lazily, including backward references to earlier archives. Strong
demands extract immediately; weak references do not pull members. Hello's archive pulls and
defined names match LLD's at each measured runtime pin (`tests/fixtures/hello-identity.json`:
359 members and 401 names at the 0.2.35 runtime, 365 and 396 at 0.2.38); an unmeasured runtime is
refused by name, not compared with a stale census.

## Tests and reference tools

```sh
docker build -t ligature-oracle -f ci/oracle.Containerfile ci
docker run --rm -v "$PWD:/work" ligature-oracle bash -c 'tools/fetch-toolchain && tools/fetch-bundle && tools/check --require-licensed-bundle'
```

Unlabelled PRs run one cheap job. The `ci` or `full-matrix` label selects the
full set: planner checks and the Linux gate. Trunk pushes run that set only
on cross-cutting paths; the nightly still runs the full set. The
Linux gate checks formatting, Wolf unit tests, malformed-file/native integration,
real musl links with LLD 17 and GNU ld, script-profile refusals, independently
parsed archive indexes and three-linker archive execution, executable kernel
profile checks, 51 AArch64 relocation witnesses, ADDRSIG validation, deterministic relinks, deliberate byte
and metadata corruptions, symbol resolution, ten three-linker writer cases, the cc frontend, independent
provenance hashes and resealed corruption witnesses, full byte coverage,
explanation queries, the high-half GOT range fixture and the public runtime
archive. The self-link gate compiles every linker module with the pinned compiler,
links the object set twice, executes that linker and demands a byte-identical
bootstrap relink and an executed hello. It **passes** at the 0.2.38 pin, as it
has since 0.2.36: the compiler's entry hands argc, argv and envp to the runtime
([wolf-lang#962](https://github.com/wolffe-lang/wolf-lang/issues/962)), and the
objects link against the same release's published musl runtime
(`wolf-rt-0.2.38-x86_64-unknown-linux-musl`, `libwolf_rt.a` SHA-256
`37252e1d0d97d917bc19e95f27d8304b8da3d31afd7a2120395e0c9a87bbc740`, pinned as
`[wolf-rt]`), so the argv preflight sees all three arguments under both
reference linkers. The row has one outcome, PASS or a named failure: the
admission that once let the 0.2.35 bundle runtime report BLOCKED was retired
with the 0.2.38 pin, and no runtime digest is admitted.
The Linux gate also invokes the released compiler's `--linker` route on hello.
`tests/link-cost.py` builds a frozen pre-optimization relocation control against
the current sources and links hello and the linker's own objects with both. The
two outputs must be byte-identical; both link times are recorded, unbounded. The
row once demanded the candidate take at most half the control's time, and it did
at the 0.2.36 pin (hello: control 216.3 and 216.6 s against 7.61 and 7.69 s on
one Linux host). That ratio rested on the runtime's `Map`, which the control's
lookup leans on, scanning linearly; wolf 0.2.38's runtime finds Map keys through
a hashed index, so at this pin the control links as fast as the candidate (8.58,
8.68 and 8.70 s against 8.39, 8.42 and 8.65 s on the same host, every pair
byte-identical) and the ratio stopped measuring the linker. Time complexity is
guarded by `link-memory-scaling`'s seconds bound instead (below). No absolute
host-speed bound is used.
`tests/link-memory.py` bounds memory: it links hello and `str` against the
46.7 MB musl runtime and verifies hello, each as a direct child under a 512 MiB
address-space cap, and requires each resident peak (the child's own
`ru_maxrss`) to stay under 192 MiB; the linker's own objects, linked as a
program, stay under 256 MiB. With `--captured NAME:MIB:DIR` it also links a
captured cc-shaped command (a compiler's `link.json` and the files it names)
under the same cap and the bound given. Synthetic archives of N, 10N and 100N
members must grow at most linearly in peak and in time. Allocation is
region-scoped: the link runs in one region and its output is verified after
that region is freed; each object is parsed, and each relocation table decoded,
in its own region; each live section is read once and relocated in place, its
pristine bytes re-read only while that object's patch rows are attributed; the
patch table is built once and only the metadata is rebuilt per fixed-point
round; the file is sealed and written from its pieces, with no image of it in
memory; digests are taken in 1 MiB steps by an unrolled SHA-256 core that
allocates nothing per block; and verify reads the file a window at a time.
`tools/check-core` runs the independent linker/provenance gates.
The gate fetches binary inputs only; no external linker or libc implementation
source is read or built. Bundle licence texts are copied unchanged from upstream
release archives, separately from the binary inputs.

The strict PAX run additionally reads the **complete** PAX runtime, musl libc
and libunwind archives and all nine program input sets. Both pinned linkers
produce executables accepted by `verify`; each program's stdout, stderr and
status agree. `census/pax-link-set.json` contains input hashes, category counts,
example sites, extraction traces and output observations. See
[the link map](docs/MAP.md), [sources and binary pins](docs/SOURCES.md), and
[formats](docs/FORMATS.md).

The exact PAX LLD control, musl runtime and sysroot are available as the
[link-bundle-wolf-0.2.38 release](https://github.com/wolffe-lang/ligature/releases/tag/link-bundle-wolf-0.2.38).
The licensed archive is named `musl-link-bundle-sha256-4cff0af6a27d200def3651bf3caee77f9bd9452be715ce878e2f0197a0516a36.tar.gz`.
`tools/fetch-bundle` verifies that archive digest twice, pins MANIFEST SHA-256
`ef3261a0f7c05082c949945d259d7896ab9ce340c083ef76a0be834f40c69950`,
and checks every member twice before extraction and twice afterwards. Unknown,
missing, duplicate, non-file and unsafe-path members are refused by name.
With `LIGATURE_BUNDLE_ARCHIVE=/path/to/the/staged.tar.gz` it reads that file in
place of the release asset, under the same checks and without the network.
The bundle includes the matching 0.2.38 musl runtime; `tools/fetch-musl-runtime`
independently verifies the same runtime from the compiler release. The public
Wolf GNU/Linux runtime cannot substitute for this musl runtime.
CI additionally uses version-pinned distro LLD 17, binutils and musl binary
packages for independent C/assembly fixtures.

To stage a unified, licensed bundle locally after fetching those inputs:

```sh
python3 -I tools/stage-bundle --out target/licensed-bundle
python3 -I tests/bundle-smoke.py target/licensed-bundle
```

The destination must be new. The archive preserves the seven control/sysroot
binaries and uses the pinned 0.2.38 musl runtime; staging it twice gives the
same bytes, which is how the 0.2.38 bundle was made from the 0.2.36 one.
It includes unchanged musl, LLVM, Rust, PAX and wolf licence/notice texts,
`NOTICE` with each binary's version and source URL, `SOURCES.json` with the
licence provenance, and a SHA-256 `MANIFEST` covering every other member.
The external receipt hashes every member, including the manifest, twice.
The archive is deterministic and named by its digest. Staging does not publish
anything or change the live fetch pins. `tests/stage-bundle.py` checks the
licence roster, complete manifest, deterministic bytes and seven refusals;
`tests/bundle-smoke.py` unpacks, rechecks all hashes twice, and executes hello
through both the bundled cc/LLD and ligature. `tests/pc32.py` independently
checks the PC-relative equation under all three linkers.

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

Linux self-link execution passes with wolf 0.2.38 and its matching musl runtime,
as described above. The earlier argv failure belonged to the 0.2.35 bundle
runtime, which nothing here links any more. Running that newly self-linked linker inside PAX is
not established by the Linux gate; the historical PAX results below do not
claim a fresh on-PAX linker execution.

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
The recorded compact-format hello retained all 590,358 relocation records. Its interned binary patch table
reduces the embedded manifest from 147,136,512 to 12,414,976 bytes (11.85×),
including 17,765 newly explicit discard/consumed-metadata records. Legacy JSON
manifests remain readable by `verify` and `explain`; no debug sites are omitted. Unwind data has no generated unwind header, strings are not merged,
and general linker scripts and Mach-O remain future work.

The exact PAX profile is qualified against real native and release paging-kernel
inputs: 66,882 and 60,768 retained relocation sites independently validated,
matching script bounds against LLD17, LLD18 and GNU controls, deterministic
relinks, and four monitor-backed BIOS/UEFI boots. LLD17's default release link
hits the recorded GOT range failure; its `--no-relax` control succeeds, as does
LLD18 by default. GNU's kernel control uses `--no-relax`. The kernel builder's
default linker is unchanged; `tests/kernel-pax.py` coordinates explicit inputs
and PAX's existing boot suite, without modifying PAX. Kernel comparisons retain
24 separate named structural observations/refusals, including the oracles'
writable `.rodata` flag inside their R-only LOAD; whole-ELF equivalence is not
claimed and the strict verifier's refusals are not waived.

AArch64 `-nostdlib` links implement ABS64, PREL32, CALL26/JUMP26, ADRP plus
ADD/LDST64 low12, and GOT-page/GOT-low12 (257/261/275/277/282/283/286/311/312).
Instruction masks, alignment, ABI range endpoints and adjacent matching
ADRP/low12 pairs are checked; unsupported sequences, TLS families and other
relocations are refused by number and specification. No veneers or relaxation
are generated. Fifty-one independent fixture rows and 24 binary endpoint controls
per LLD17/LLD18 cover the subset. `tests/aarch64-live.py` links and executes an
assembled hello under explicit qemu AArch64 user-mode emulation, not native
AArch64, and independently proves all nine relocation kinds for both candidate
and reference outputs. The hosted core gate does not run that emulator.

The released AArch64 compiler ELF and all 440 runtime members have a separate
census (14,033 dynamic compiler relocations and 668,066 runtime relocations).
That runtime contains families beyond this linker subset. A **Wolf-generated
AArch64 object/hello remains blocked by [wolf-lang#614](https://github.com/wolffe-lang/wolf-lang/issues/614)**:
the verified 0.2.35 AArch64 compiler runs under emulation, but explicitly refuses
both native object emission and release IR emission on Linux AArch64. The
assembled hello is not represented as a Wolf compiler/runtime qualification.

Licence: GPL-3.0-only with the wolf Training Data Permission (`LICENSE`, `LICENSE-TRAINING-DATA`), as pax, boreutils and den.
