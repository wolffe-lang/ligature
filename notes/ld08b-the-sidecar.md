# ld08b — the provenance sidecar

The owner chose option C of decision 1 in `notes/ld08-the-pelt-link.md`: by default a link writes
the provenance manifest and the retained relocations to a sidecar file beside the output, bound to
it by the digest its 116-byte note already holds, and embeds both on request. This branch builds
that. The embedded form is byte-identical to trunk's output; the default output's bytes change.

## Prediction

The ld08 note measured option C at 17.8 MB for hello and 27.3 MB for pelt, 16% and 10% over
ld.lld 18's output from the same inputs, with no change to what a link reads, hashes or verifies:
the same bytes are written and hashed, only to two files instead of one. Memory and time should
stay where #36 left them, a little lower for the one fixed-point round a sidecar's manifest needs
(it takes no room in the output, so its size cannot move the layout).

Measured: exactly as predicted for size (17,814,712 and 27,302,152 bytes; 1.160 and 1.102 times
lld's). Memory and time are a little lower than trunk's, as expected (below).

## Forbidden

No linker, binutils, libc or kernel source was read, and no PAX kernel source. The sources used
were the ELF gABI, the x86-64 psABI, ligature's own source, and black-box runs of ld.lld 18.1.8
and `cc`. To answer what the PAX image needs, PAX's notes and its distribution test's shell
session were read, nothing under its kernel.

## Inputs verified

Base trunk `8594073c`, built by its pinned wolf 0.2.38. The measured programs are ld08's four
captured links, unchanged: hello, a `std.net` + `std.process` program, pelt at `b80d6570`, and
ligature itself, compiled by wolf 0.2.39 (`3fc86f77`, std `2411d868`) and linked against
`libwolf_rt.a` (47,693,716 bytes, `db50108f…748d`) and musl 1.2.5's CRT, `libc.a` and
`libunwind.a`. Trunk's outputs are ld08's (`2ccd873c…`, `41a08717…`, `dbe08396…`, `2878d17d…`).

## What a link writes

The note is always in the output, and its flags word (note offset 24, the first word after the
version) says where the rest is:

- **flags 0, the embedded form** (`--provenance=embed`, or `-Wl,--provenance=embed` through the cc
  front end): the manifest is the output's `.wolf.link.manifest` section and the retained
  relocations are its `SHT_RELA` sections, exactly as trunk writes them. The note's size and
  offset name the manifest section and its first digest is the manifest's. A stale
  `OUTPUT.provenance` from an earlier link is removed.
- **flags 1, the default**: the output has no manifest section and no `SHT_RELA` section. The
  note's size field is the sidecar's size, its offset field is 0, and its first digest is the
  SHA-256 of the whole sidecar. The sidecar is written first, so its digest is known when the note
  is sealed.

Either way the second digest is the output's, with both digest slots zero. An output names its one
sidecar by that sidecar's digest, and the sidecar's head holds the output's size.

`OUTPUT.provenance`, every integer a little-endian u64:

| bytes | what |
|---|---|
| 0–40 | `WLPROV01`, the output's size, the number of retained tables T, the manifest's offset, the manifest's size |
| 40–40+32T | per table: its target section (`sh_info`), its symbol table (`sh_link`), its entries' offset, its entry count |
| then | each table's `Elf64_Rela` entries, in the records' order, the bytes the embedded form's sections hold |
| then | the manifest, encoded as the embedded section would be, padded with zeros to its size |

The manifest's patch rows are the same rows in both forms. Its metadata differs only where it
describes the output file itself: `output` (size), `ranges` (the output's byte ranges, which have
no `.rela.*` or manifest range in the default form) and `sections`. `sidecar-embedded` checks
exactly that.

`verify` and `explain` read the sidecar named `OUTPUT.provenance` beside the path they are given.
`verify` refuses by name a sidecar that is missing, altered (its digest), another output's (the
digests or the size in its head), laid out wrongly (a table's entries not where its record says),
or whose tables or manifest fail the same checks the embedded form's do: each retained table is
checked against the output's section and symbol tables a window at a time, as `walk` checks an
embedded one, and the manifest's retained patch count must equal the sidecar's entries. `inspect`
lists the sidecar's retained relocations after the output's own sections, numbered from the
output's section count, each row naming its symbol table. The output runs without its sidecar;
only its provenance is lost.

## Sizes, memory and time

Linux x86-64, one CPU, in the repository's oracle image, three rounds interleaved with trunk's
linker (the lane's `time-rows`, a development run at the head's source; the green record in the
pull request repeats it). Bytes:

| program | trunk = embedded | default output | sidecar | ld.lld 18 | default / lld |
|---|---|---|---|---|---|
| hello | 46,004,568 | 17,814,712 | 28,185,032 | 15,356,824 | 1.160 |
| `std.net` + `std.process` | 48,327,088 | 18,451,384 | 29,870,880 | 15,929,864 | 1.158 |
| pelt | 58,901,840 | 27,302,152 | 31,594,864 | 24,776,664 | 1.102 |
| ligature itself | 48,545,744 | 19,039,544 | 29,501,384 | 16,552,416 | 1.150 |

The rest of the gap to lld is `.debug_str` kept unmerged (option D of the same decision, its own
change). Resident peak and the fastest CPU time of three, default form against trunk:

| program | head | trunk `8594073c` | #36's bound |
|---|---|---|---|
| hello | 138.3 MiB, 1.327 s | 140.4 MiB, 1.417 s | 192 MiB, 2 s |
| `std.net` + `std.process` | 149.3 MiB, 1.403 s | 151.7 MiB, 1.498 s | 192 MiB, 2 s |
| pelt | 168.3 MiB, 1.552 s | 175.8 MiB, 1.664 s | 256 MiB, 2 s |
| ligature itself | 147.0 MiB, 1.370 s | 148.8 MiB, 1.469 s | 192 MiB, 2 s |

Every link stays under the memory rows' 512 MiB address-space cap. macOS arm64 (the same captured
links, the head's source built by wolf 0.2.38, `/usr/bin/time -l`): default form 178.2 / 178.4 /
206.1 / 175.3 MiB, embedded 185.5 / 185.7 / 207.1 / 187.0 MiB, every output verified. The Mac
writes the same bytes as Linux in both forms: outputs `54b35705…`, `f508dfe6…`, `a7e422b0…`,
`a6ebfce4…` and sidecars `ce9e2d7a…`, `a0f34c77…`, `b4814d2f…`, `697690bb…` in the default form,
and trunk's four outputs embedded.

## Rows

### Byte-identity rows that move, and why

The default output is a different file from trunk's, so every row that compared the head's default
output with trunk's now compares the head's embedded form with trunk's output, which must still be
the same file. No output digest is pinned in the tree, so nothing else is refrozen.

- `link-identity-CASE` (`tests/link-memory.py --baseline`): against a baseline that embeds
  (trunk's binary), the candidate links each case again with `-Wl,--provenance=embed` and that
  output must be the baseline's; against a baseline that writes a sidecar, both files must match.
- The lane rig's `time-identity`: the candidate's embedded form of each captured program must be
  trunk's file in every round, and must leave no sidecar.
- The lane rig's `identity-suite`: the linking tests run under the candidate with
  `--provenance=embed` added to every link (by a shim in place of `target/ligature`; never to
  `verify`, `inspect`, `roundtrip`, `explain`, `script-plan`, `archive` or `--version`), then under
  trunk's binary, and every ELF executable they write must be the same.
- `self-link`'s bootstrap identity: the seed link (by `target/ligature`) and the bootstrap link (by
  the seed) must be the same files. When the seed comes from a linker whose default is the other
  form (trunk's binary in the identity suite), the bootstrap link writes the seed's form with
  `--provenance=embed`.

### Rows that read the manifest find it in the sidecar

`tests/provenance-files.py` reads an output's provenance from wherever its note says it is, and
writes a mutated output with its sidecar, resealing both digests when a row asks. Every row that
read the manifest or the retained tables from the output reads them through it, in either form:
`provenance` (the note's fields per form, and a missing sidecar refused), `attribution` (delta
locality: a sidecar delta is confined to the manifest), `compact`, `kernel-script`,
`relocation-witness` and `aarch64-sites`. `tools/differ` takes a retained table's symbol table from
its inspect row, since a sidecar's table is not a section of the output. Every row that demands one
file from repeated links compares the sidecars too: `writer`, `self-link`, `link-cost`, the rig's
`time-determinism`.

### New rows

`tests/sidecar.py`, in `tools/check-core`:

- `sidecar-default`: a default link writes OUTPUT and OUTPUT.provenance; the note, the head, every
  record and both digests check independently; the program runs and `verify` passes.
- `sidecar-embedded`: `--provenance=embed` and `-Wl,--provenance=embed` write the same embedded
  form and remove a stale sidecar; its tables and patch rows are the sidecar's, byte for byte, and
  its metadata differs only in `output`, `ranges` and `sections`.
- `sidecar-determinism`: two links of each form are the same files.
- `sidecar-option`: an unknown `--provenance` value is refused by name; the plan names the mode.
- `sidecar-inspect`: `inspect` lists the sidecar's retained relocations as the embedded form's.
- `sidecar-explain`: `explain` answers from the sidecar, and refuses without it.
- `sidecar-refusals`: `verify` refuses, by name, a missing sidecar, an altered sidecar, another
  output's sidecar, an altered output, and (with both digests resealed, so only the check past the
  digests can refuse) a sidecar naming another output, a misplaced table, an entry's symbol outside
  the symbol table, and a manifest one patch row short.

Seen red first: the red-first record runs `tests/sidecar.py` and the link-memory rows at
`b94db00`, the commit that adds them, before any change to the linker. Every sidecar row and every
`link-identity` row fails there by name (trunk's linker refuses `--provenance=embed`); the memory
rows pass.

## What the PAX image needs

Nothing on the image reads an embedded manifest directly: a search of PAX's repository finds no
reader of `.wolf.link.manifest` or of the note. One row reads provenance through ligature, staging
decides where sidecars go, and two rows compare bytes:

- The upgrade rows' U4 links a program with `WOLF_LD=/usr/bin/ligature` and runs `ligature verify`
  on it. With the default form the link also writes `PROGRAM.provenance` beside the program.
  `tests/real-ligature.py` links through the compiler's `--linker` route and verifies the program
  where the compiler wrote it, sidecar beside it, so U4 should hold as long as it verifies the
  program where it was linked; its retake on the new pin shows it. A row that copies the program
  first must copy its sidecar too, or link with `-Wl,--provenance=embed`.
- Any ligature-linked binary staged onto the image leaves its sidecar in the build directory. The
  image's RAM saving comes from not installing the sidecar; installing it puts the same bytes back
  in RAM. If the image should carry self-verifying binaries, embed them instead.
- `distribution-ligature`'s L3 (two ligature links of hello, byte-identical) and L5 (the self-built
  ligature links hello to the shipped one's bytes) compare outputs from the same ligature in the
  same form, so they hold unchanged; they compare the outputs, not the sidecars.

When the image moves its ligature pin to this head, its rows should be retaken on that pin, U4 and
the image's sizes among them.

## Decisions

Each decision is the owner's.

- **Decision 1, how this change is classed.** Every consumer's default output changes (the PAX
  image's binaries among them), though the change is confined to this repository's linker and its
  tests. Recommend classing it as this repository's module change, with the PAX pin move retaken
  in PAX's own lane as above.
- **Decision 2, a sidecar somewhere else.** `verify` and `explain` look only beside the output. An
  option naming the sidecar's path (for an image that keeps sidecars apart from its binaries)
  would be small. Recommend waiting until something needs it.
- **Decision 3, `.debug_str`.** Merging it (option D of ld08's decision 1) takes about 2 MB more
  off each output and is still its own change. Recommend it as the next size change.

## Done-when

- [x] Manifest and retained relocations in `OUTPUT.provenance` by default; `--provenance=embed`
  (and `-Wl,`) embeds them; the flag's values refused by name otherwise.
- [x] The embedded form byte-identical to trunk's output: the four captured programs (link-memory
  identity rows, `time-identity`, every round), and every ELF executable the linking tests write
  (`identity-suite`).
- [x] Every row that reads the manifest finds it in the sidecar; the byte-identity rows that moved
  are named above with the reason.
- [x] Determinism for both files: every repeated link gives one output and one sidecar
  (`sidecar-determinism`, `time-determinism`, `writer`, `self-link`, `link-cost`), on Linux and
  macOS alike.
- [x] Sizes against lld for hello, the net/process program, pelt and the self-link; memory and time
  inside #36's bounds.
- [x] Red first, one plant, the green record at the head.
