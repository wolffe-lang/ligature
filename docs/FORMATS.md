# Link formats

These are version 1 contracts. Inspection, link plans, the embedded note and a
byte-and-patch provenance manifest are implemented, along with `explain`.
Unknown versions must be refused, not interpreted as the nearest known version.
All offsets and lengths are unsigned 64-bit integers; arithmetic is checked.

## Link plan

`ligature --print-plan` writes one JSON object with `format` equal to
`ligature.plan.v1`. `argv` preserves every argument in its original order.
`inputs`, `libraries`, `search_paths`, `undefined` and `definitions` are
convenience projections, not permission to reorder archive/library searches.
`output` names the output; `static`, `nostdlib` and `gc_sections` are booleans.
A plan is declarative: printing it neither opens input files nor links them.
Unrecognized options and missing values are errors on stderr with status 1.
No implicit sysroot is selected by this format. A future executor must record
its resolved CRT order and library paths in the provenance manifest.

## Inspection stream and census

`inspect` emits JSON Lines, in file/member order. An `elf` row begins an
object; `section`, `program`, `symbol`, `rela`, `group`, `note`, `array` and
`dynamic` rows follow. `member` identifies archive membership by name, offset
and size; duplicate names are not merged. `archive_symbol` stores the index
symbol and member-header offset. A relocation's `symbol` is an index in the
symbol table selected by the relocation section's `link`. `addend_bits` is
the exact two's-complement 64-bit pattern, not a signed JSON number. Names
are byte-preserving JSON Latin-1 escapes, not a claim that ELF names are UTF-8.

`ligature.census.v1` contains input SHA-256 and byte counts, object counts,
relocation and section/symbol category counts with example sites, feature
occurrences, link options, and oracle observations. The reader performs
parse/serialize equality checks while reading fixed-layout tables. Opaque
section payloads are not represented as parsed records and are not rewritten.

## Embedded provenance

The canonical JSON has `format: "wolf.link.provenance.v1"` and
`coverage: "bytes-and-patches"`. Keys are lexicographically sorted, integers
are decimal, encoding is compact UTF-8, and the document ends with one LF.
Logical input basenames and member ordinals replace absolute staging paths.
No timestamp, host name or output filename is embedded.

* `inputs` and `members` identify complete inputs and selected members by
  size and SHA-256. Object ordinals follow lazy discovery order.
* `input_ranges` maps retained input sections to output sections; NOBITS has
  an empty file range. `memory_ranges` describes NOBITS separately.
* `ranges` is a sorted, disjoint, nonempty partition of **every file byte**.
  Input origins carry member ordinal, section index and member-relative input
  offset. Generated origins name ELF/program/section headers, padding or the
  output section (GOT, symbol/string tables, retained RELA, note and manifest).
* `patches` preserves original relocation type/addend, input member/section/
  offset, target symbol identity, output byte interval, before/after hex bytes
  and transition reason. TLS call records name their consuming relocation.
  Patch intervals can overlap; the complete file partition cannot.
* `symbols` supplies definition/alias origins, address, size, input identity
  and file interval. `alias_of` names the canonical definition when applicable.
  TLS addresses are module offsets. NOBITS and absolute definitions have
  `file_start=file_end=-1`; they never claim bytes at a conceptual file offset.
* `pulls` records selected object, demanding parent object (`-1` for a forced
  root), archive/member/header and demanded symbol. Parent ordinals precede
  children; no recursive expansion or cycle is accepted.
* `sections` records output layout. `output.sha256` stays null to avoid a hash
  cycle; the note seals the whole file. `zz_padding` is a reserved string of
  zero characters which rounds the canonical document to 4096 bytes. This
  stabilizes the otherwise self-referential alignment-gap description without
  adding noncanonical whitespace. It has no provenance meaning.

`verify` checks both digests before validating coverage, input-slice bounds,
patch bytes and extraction edges. A valid digest is not authentication or a
proof that a claimed target is correct: `tools/differ` independently evaluates
retained relocation equations. Mutation tests forge matching patch claims and
re-seal both digests, then require that independent check to fail.

Older `coverage: "sections"` files remain verifiable but `explain` refuses them.
No sidecar, signature scheme or general linker-script format is implemented.

## `.note.wolf.link`

ELF `SHT_NOTE`, alignment 4, not allocated. The ELF note header is three
little-endian u32 values: `namesz=5`, `descsz=96`, `type=1`. The owner bytes
are `WOLF\0` followed by three zero padding bytes. The descriptor is:

| Offset | Width | Field |
|---:|---:|---|
| 0 | 4 | Format version, 1 |
| 4 | 4 | Flags, zero in version 1 |
| 8 | 8 | Full output file byte count |
| 16 | 8 | Canonical manifest byte count |
| 24 | 32 | SHA-256 of canonical embedded manifest |
| 56 | 32 | SHA-256 of output with this descriptor's digest fields zeroed |
| 88 | 8 | Embedded manifest file offset |

The canonical embedded manifest is a separate nonallocated
`.wolf.link.manifest` section. To avoid hash cycles its `output.sha256` is
null and its own generated ranges carry no content hashes. The sidecar may
add the final output hash in an outer envelope; the canonical embedded
manifest bytes remain identical. The descriptor and manifest hashes are
verified before trusting any byte-range claim. This note is a digest, **not
a digital signature**. Authentication requires a separately specified signed
envelope; no signing scheme is implied here.

## Queries and tests for the writer

```
ligature explain FILE --symbol NAME [--input MEMBER_ORDINAL]
ligature explain FILE --address DECIMAL_OR_0x_HEX
ligature explain FILE --why NAME [--input MEMBER_ORDINAL]
```

Queries return JSON arrays only after validation. Symbol results include aliases;
ambiguous local names require the selected member's ordinal. Address results
include containing sections and symbol aliases, with NOBITS/TLS explicit.
`--why` walks extraction edges from the selected object toward its root; an
explicit input with no extraction edge returns its definition origin. Misses
and invalid arguments return 1. Invalid/mismatched manifests return 2 and no
trusted stdout. These digests establish integrity, never signer identity.

Tests reject gaps, overlaps, invalid input slices, mismatched patch bytes,
wrong hashes and unknown coverage. Same-input relinks are byte-identical. A
same-size input-data edit changes only that data and the predicted manifest/note
metadata; the gate compares actual byte deltas. Separate positive/negative
fixtures cover local/entry normalization, unused data/debug relocation patches,
alias queries, TLS/NOBITS and ambiguous local names.

## Compact patch tables (WLPATCH2)

New outputs keep the 116-byte note and its digest rules unchanged. The
nonallocated `.wolf.link.manifest` begins with eight ASCII bytes `WLPATCH2`,
then four little-endian u64 lengths: metadata bytes, string count, patch-row
count, and patch-table bytes. Canonical compact JSON metadata follows, with
`patches: []` and no `zz_padding`. Every other attribution field is retained.
A first-use-ordered UTF-8 pool follows; each string has a minimal unsigned
LEB128 byte length. The patch table follows the pool; zero bytes round the
complete section to a 4096-byte boundary for layout convergence.

Each row starts with a little-endian u16 presence mask (bit 15 reserved zero).
Columns, in order, are `addend`, `after`, `before`, `consumed_by`, `end`, `index`,
`member`, `offset`, `rule`, `section_index`, `start`, `symbol`, `target_member`,
`target_symbol`, `type`. The four string columns contain pool indexes. `end`
is encoded as patch width. `addend` is absolute; all other values are deltas
from the previous row, initially zero. Present values use minimal unsigned
LEB128 of zigzag signed integers (`2*n` if nonnegative, `-2*n-1` otherwise).
Zero values omit their bit and bytes. All original row values reconstruct
exactly, including signed 64-bit addends. Encoding order is independent of
hash-bucket iteration. Unknown masks, overflows, truncated lengths, invalid
pool references, duplicate pooled strings and nonzero padding are refusals.

The reader accepts both this table and legacy JSON. `verify` additionally
requires one patch per retained RELA record and strictly increasing original
patch indexes; independent relocation equations remain `tools/differ`'s job.
This count check is not a claim that digest-sealed metadata proves its own
truth. The independent test encoder reconstructs the exact compact bytes.

New metadata adds `discarded`: each absent selected-input section records its
member, section index/name, size and cause (`GC-unreachable`, `duplicate-COMDAT`,
`SHF_EXCLUDE`, regenerated metadata, consumed group metadata or stack policy).
Unselected archive members are not read and are not called discarded sections.
`explain --discarded SECTION [--input N]` returns these records; legacy files
without causes refuse that query explicitly. `explain --dependencies SYMBOL`
returns the original relocation patches in the definition's input section,
including target identities and transition reasons. This is section dependency
information, not a claim to recover source-language call graphs.
