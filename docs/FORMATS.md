# Link formats

These are version 1 design contracts. Inspection and link-plan output exist;
provenance writing, the embedded note and `explain` are not implemented yet.
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

## Provenance sidecar

The future sidecar is UTF-8 JSON with `format: "wolf.link.provenance.v1"`:

* `output`: final byte count, target, ELF type, entry symbol and SHA-256.
* `inputs`: stable ordinal, logical path, SHA-256 of complete original input,
  archive member name/header offset if any, and member SHA-256.
* `options`: ordered semantic link options; tool/version and profile hashes.
* `ranges`: sorted, disjoint, nonempty half-open output file ranges
  `[start, end)`. Every byte is covered exactly once, including headers,
  alignment fill, section tables and the provenance note itself.
* Each range has `origin`: either `{input, section_index, section_name,
  input_offset, symbol_index, symbol_name}` or a named generated origin
  (`elf-header`, `program-headers`, `padding`, `got`, `relaxation`,
  `string-table`, `section-headers`, `provenance-note`). Symbol fields may be
  null when no input symbol owns those bytes. Overlapping symbol aliases are
  an ordered `aliases` list, not overlapping range records.
* `patches`: output range, relocation type, input relocation location,
  original addend, target identity, final encoded bytes and relaxation rule.
  A relaxation retains the input origin and names its generated-byte reason.
* `memory_ranges`: NOBITS/TLS memory ranges, separate from file-byte ranges.
* `pulls`: archive-member node and the ordered edge that demanded it: an
  unresolved input symbol, `--undefined`, or an explicit whole-archive root.
  Weak references do not manufacture an extraction edge. Cycles are represented
  by node references, never recursively expanded JSON.
* `discarded`: sections and named causes (unreachable, COMDAT loser, excluded).

Paths are logical, relative input labels. Absolute staging paths, wall-clock
times, hostnames and random identifiers are forbidden. Object and archive
input order is explicit. Keys are lexicographically sorted, integers decimal,
no insignificant whitespace, one final LF. Range and edge ordering is defined
by output start and discovery ordinal, never hash-map enumeration.

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

`explain --symbol NAME` returns all definition/alias ranges and origins;
ambiguous local names require an input ordinal. `--address VA` reports load
mapping, section, symbol aliases and file range, or explicitly NOBITS/TLS.
`--why NAME` returns the archive extraction path from a root, including the
unresolved reference which caused each edge. Unknown names are status 1;
invalid or mismatched manifests are status 2 and produce no trusted answer.

The writer's gates must reject gaps, overlaps, out-of-range input slices,
wrong hashes, altered note length/version and cyclic expansion. Two builds
from identical ordered inputs must be byte-identical. A one-input edit must
change only the ranges and generated metadata predicted by the dependency
edges; the test compares actual byte deltas, not just manifest descriptions.
