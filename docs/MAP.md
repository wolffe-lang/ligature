# PAX link map

This is the initial static x86-64 ELF input contract. The machine-readable
inventory is `census/pax-link-set.json`; it contains exact SHA-256 identities,
example sites, every extracted archive member and extraction cause, and the
401 globally/weakly defined symbols of the hello output. Counts include whole
archives, not only members selected by hello. Nonallocated debug relocations
are included: they are not silently omitted from the writer's requirements.

## Input boundary

| Input | Objects |
|---|---:|
| Nine Wolf program sets (eight PAX examples plus compiler corpus hello) | 14 |
| PAX musl-targeted libwolf_rt.a | 344 |
| musl crt1.o, crti.o, crtn.o | 3 |
| musl libc.a | 1,345 |
| libunwind.a | 8 |
| Total | 1,714 |

The std example emits six objects. The other programs emit one each. Each
structured table was parsed and re-serialized byte for byte by the Wolf
reader, including every archive member. Link instrumentation adds
`--emit-relocs`, `--trace`, `-Map` and LLD's `--why-extract`; none is passed
as a new semantic dependency to the future linker.

## Relocations

The AMD64 psABI 1.0 section 4.4 supplies the formulas; section 10 supplies TLS
relaxations. Exactly 13 encodings occur. GOTPCRELX (41) is absent;
REX_GOTPCRELX (42) is present. Unknown encodings must be refused by name.

| Encoding | Count |
|---|---:|
| `R_X86_64_32` | 433,334 |
| `R_X86_64_32S` | 489 |
| `R_X86_64_64` | 270,018 |
| `R_X86_64_DTPOFF32` | 28 |
| `R_X86_64_DTPOFF64` | 21 |
| `R_X86_64_GOTPCREL` | 7,172 |
| `R_X86_64_GOTTPOFF` | 11 |
| `R_X86_64_PC32` | 22,895 |
| `R_X86_64_PLT32` | 15,922 |
| `R_X86_64_REX_GOTPCRELX` | 78 |
| `R_X86_64_TLSGD` | 36 |
| `R_X86_64_TLSLD` | 16 |
| `R_X86_64_TPOFF32` | 779 |

## Sections

The keys below are `sh_type:sh_flags` in decimal; ELF flag bits retain their
ABI meanings. 1879048193 is the x86-64 unwind section type. The table includes
zero-sized and excluded sections. SHT_NOBITS carries no file payload.

| Type:flags | Count | Example section |
|---|---:|---|
| `0:0` | 1,714 | `` |
| `17:0` | 57 | `.group` |
| `1879048193:2` | 301 | `.eh_frame` |
| `1:0` | 12,482 | `.note.GNU-stack` |
| `1:1027` | 9 | `.tdata._RNvNCNKNvNtNtCs1NRTePXyPp9_7wolf_rt4task4pool11SCOPE_STACK0023___RUST_STD_INTERNAL_VAL` |
| `1:18` | 418 | `.rodata.cst16` |
| `1:2` | 4,462 | `.rodata` |
| `1:2147483648` | 582 | `.llvmbc` |
| `1:3` | 2,192 | `.data._RNvNtNtCs1NRTePXyPp9_7wolf_rt4task4pool4POOL.llvm.12393371654603404566` |
| `1:48` | 4,682 | `.debug_str` |
| `1:50` | 240 | `.rodata.str1.1` |
| `1:514` | 12 | `.rodata._ZN9libunwind12UnwindCursorINS_17LocalAddressSpaceENS_16Registers_x86_64EE15getRegisterNameEi` |
| `1:515` | 28 | `.data.DW.ref.rust_eh_personality` |
| `1:518` | 28 | `.text._ZN9libunwind12UnwindCursorINS_17LocalAddressSpaceENS_16Registers_x86_64EED0Ev` |
| `1:6` | 7,892 | `.text` |
| `2:0` | 1,710 | `.symtab` |
| `3:0` | 3,115 | `.strtab` |
| `4:512` | 24 | `.rela.data.DW.ref.rust_eh_personality` |
| `4:576` | 39 | `.rela.text._ZN9libunwind12UnwindCursorINS_17LocalAddressSpaceENS_16Registers_x86_64EE6jumptoEv` |
| `4:64` | 15,726 | `.rela.text` |
| `7:2` | 1,391 | `.note.gnu.property` |
| `8:1027` | 21 | `.tbss._RNvNCNKNvNtNtCs1NRTePXyPp9_7wolf_rt4task4pool12CURRENT_TASK0023___RUST_STD_INTERNAL_VAL` |
| `8:3` | 1,632 | `.bss._RNvNtNtCs1NRTePXyPp9_7wolf_rt4task4pool4HELD.llvm.12393371654603404566` |
| `8:515` | 2 | `.bss._ZN9libunwind13DwarfFDECacheINS_17LocalAddressSpaceEE14_initialBufferE` |

## Symbols

Keys are `binding:type:visibility`. Bindings: local=0, global=1, weak=2.
Types: NOTYPE=0, OBJECT=1, FUNC=2, SECTION=3, FILE=4, TLS=6.
Visibility: default=0, hidden=2, protected=3.

| Binding:type:visibility | Count |
|---|---:|
| `0:0:0` | 5,238 |
| `0:1:0` | 864 |
| `0:2:0` | 1,149 |
| `0:3:0` | 23,492 |
| `0:4:0` | 1,680 |
| `0:6:0` | 11 |
| `1:0:0` | 3,329 |
| `1:0:2` | 1,708 |
| `1:0:3` | 18 |
| `1:1:0` | 51 |
| `1:1:2` | 268 |
| `1:2:0` | 3,810 |
| `1:2:2` | 1,580 |
| `1:2:3` | 2 |
| `1:6:0` | 11 |
| `1:6:2` | 29 |
| `2:0:0` | 9 |
| `2:0:2` | 7 |
| `2:1:0` | 10 |
| `2:1:2` | 52 |
| `2:2:0` | 220 |
| `2:2:2` | 300 |

## Startup, archives and thread-local data

The link order is `crt1.o crti.o --start-group PROGRAM-OBJECTS libwolf_rt.a
libc.a libunwind.a --end-group crtn.o`. Force
`--undefined=__wolf_rt_trap_at` and define
`--defsym=wolf_trap=__wolf_rt_trap_at`; the alias alone does not extract an
archive member. LLD selects **359 members** for compiler-corpus hello:
32 runtime, 322 libc and 5 libunwind. Each reason and demanded symbol is
recorded in `oracle_observations.hello-hello.lld_extraction_reasons`.
GNU archives preserve member order, permit duplicate names, use a big-endian
32-bit symbol-index offset table and a `//` long-name table. Libunwind's index
includes one trailing NUL padding byte in its member size.

The whole input set has 30 TLS sections. Hello's PT_TLS contains 80 initialized
bytes and 272 total memory bytes, aligned to 8. TLSGD, TLSLD, GOTTPOFF and
TPOFF32 are all real inputs, not optional future work. The differ validates
the measured TLS local-exec relaxations against the output instructions and
TLS symbol offsets. A TLS header overstating its template is a named error.

There are 57 COMDAT group sections containing 132 member records. No
SHN_COMMON symbol appears in the PAX inventory; synthetic resolution tests
still cover common allocation. No input init/fini array occurs in this PAX
set. The CI fixture independently exercises a constructor and its init array;
the public GNU/Linux runtime contains an init array with `sh_entsize=0`.

## Output boundary

Compiler-corpus hello enters at `_start` (LLD address `0x219b20`, image base
`0x200000`). It has four PT_LOAD segments, PT_PHDR, PT_TLS, GNU_STACK and
GNU_RELRO. Its `.eh_frame` is 26,612 bytes; no `.eh_frame_hdr` is emitted.
339 input `.eh_frame` sections exist. Keeping unwind data without building an
unwind header matches this measured default. This does not assert that Rust's
unwind machinery is inert: the link really extracts five libunwind members.

Static non-PIE ET_EXEC is the first writer target. PAX's recorded dev-image
plant rejects ET_DYN with “a PIE or shared object (PIE is later)”
(`pax/notes/px60-wolf-on-pax.md`, the exec-refusal witness). No kernel source
was used and no new PAX boot is claimed here. Both oracles' hello binaries and
all eight other program pairs pass reader verification and produce identical
stdout, stderr and status in the Linux container.

## Named structural differences

The hello differential is deliberately not waived. Its complete record is
hashed in the census; compact examples are in
`notes/ld00-evidence/structural-differences.json`.

* **Symbols:** LLD retains more local/debug symbols and represents some
  hidden definitions and synthetic boundaries differently. The normalized
  multisets differ by 1,028 LLD-only and 215 GNU-only records.
* **Segments:** LLD emits PT_PHDR and two writable LOADs; GNU has two read-only
  LOADs and one writable LOAD. GNU_STACK alignment is 0 versus 16. These are
  more than free base-address changes and remain named differences.
* **Entry aliases:** both enter `_start`; LLD additionally places empty
  init/fini-array boundary symbols at that address. The strict alias-set
  comparison reports this rather than discarding the aliases.
* **Relocation records:** local/section-symbol choices, debug tombstones,
  retained debug tables and relaxation forms differ. Each output independently
  satisfies the relocation equations the differ supports. The cross-output
  record lists remain unequal; behavior agreement is not presented as a
  green structural comparison.

The duplicate-resolution witnesses agree: strong beats weak, strong overrides
common, the first weak wins, common/common takes maximum size/alignment,
duplicate strong definitions fail, and an indexed archive extracts its first
needed definition. The future writer should implement these gABI semantics,
not infer a new resolution rule from layout/synthetic-symbol differences.

## Static writer

`src/resolve` selects indexed archive members in ordered groups and resolves
strong, weak, COMMON, COMDAT and visibility constraints. `src/layout` computes
reachability, section merges and the fixed 0x200000 image layout. `src/relocate`
applies the thirteen census types, including nonallocated debug relocations,
and recognized static TLS transitions. `src/writer` emits ELF tables and symbols;
`src/provenance` writes and independently verifies the versioned integrity note.

The writer emits two LOAD segments (RX and RW), PT_TLS when needed and a
non-executable GNU_STACK. It does not emit PT_PHDR or GNU_RELRO for this static
non-PIE mode. Segment differences are explicit, not reduced to a base-address
waiver. Hello reproduces all 359 archive pulls and the 401 public definitions;
its TLS is 80 initialized bytes, 272 memory bytes, alignment 8.

GOTPCREL uses reserved GOT entries. Recognized REX_GOTPCRELX loads relax only
when the final post-layout displacement fits signed 32 bits; otherwise the load
keeps its GOT entry. The high-half fixture at 0xffffffff80000000 demonstrates
that -2147483652 must not relax. Unknown types are named refusals.

The fourteen Linux cases agree in stdout, stderr and status, verify successfully
and relink deterministically. Their structural findings are indexed in
`notes/ld01/evidence/structural-classes.json`; exact large reports are retained
in the compressed local evidence archive. Five LLD 18 controls agree structurally
with LLD 17 and leave the same classes against ligature. None of these five
classes is attributable to the separate high-half kernel failure.

The hello archive-member multiset is exact, including multiplicities, but 349
positions in the extraction sequence differ from LLD's lazy recursive order.
The indexed scanner preserves archive member identities and first-needed
selection; it does not claim LLD's discovery order. The complete two sequences
are in `notes/ld01/evidence/hello-member-comparison.json`.

Live PAX BIOS evidence includes fourteen three-linker cases. Thirteen equal the
Linux records; the fork case stays explicitly red across hosts, identically
under all three linkers. On fresh PAX trunk native and release kernels, unquieted
diagnostics identify `fork` syscall 57 returning `-ENOSYS` (pax#175). The copied
ISO had no commit banner (pax#176), so these controls use recorded kernel hashes
and the full checkout's commit rather than guessing a version from the greeting.
