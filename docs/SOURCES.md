# Sources

Ligature is clean-room software. Linker, binutils, libc and kernel source is
not used. Executable tools are black-box references, not implementation templates.

## Specifications

* System V Application Binary Interface, Edition 4.1 (1997), chapter 4
  (ELF header, sections, string and symbol tables, relocation) and chapter 5
  (program headers, dynamic linking); generic ABI update dated 17 December
  2003, “Section Groups”, “Initialization and Termination Functions”, “Note Section”.
  <https://refspecs.linuxfoundation.org/elf/gabi4+/contents.html>
* System V AMD64 ABI, version 1.0, 22 December 2018, sections 4.1–4.4
  (object files and relocation), 5.2 (dynamic linking), 10 (TLS).
  <https://gitlab.com/x86-psABIs/x86-64-ABI>
* ELF for the Arm 64-bit Architecture (AArch64), 2025Q1, sections 5
  (object files), 6 (relocations), 7 (program loading).
  <https://github.com/ARM-software/abi-aa/releases/tag/2025Q1>
* DWARF version 5, 13 February 2017, section 7 (data representation),
  particularly 7.5 (format of debugging information).
  <https://dwarfstd.org/dwarf5std.html>
* POSIX.1-2024, `ar` utility, extended description (archive membership).
  GNU Binutils 2.42 manual, `ar`, `nm`, `objdump`, `readelf` and `ld` chapters.
  Archive name/index encodings are measured with pinned `ar` output.
* LLD 17.0.6 ELF linker documentation and `ld.lld --help`: `--trace`,
  `-Map`, `--emit-relocs`, `--gc-sections`, `--undefined`, `--defsym`.

## Own-code integration references

* wolf-lang `crates/wolf_driver/src/main.rs`, `link_objects` and `link_staged`;
  `spec/04-abi.md` section 7, `[abi.link]`.
* PAX `tools/mkdev`, `user/wolf-link.sums`, `notes/px60/build-m2.sh`,
  `notes/px60/cc-lld.py`, and `tests/mpx5-wolf` specify input order and bytes.
  No linker or libc source build is performed by this project.
* The CI tier planner is adapted from wolffe-lang/scent's `ci/tiers.py`.

## Binary identities

The wolf and lupin release archive digests are in `wolf-toolchain.toml`.
PAX's static LLD 17 binary must have SHA-256
`1217ca75f9df70439294844b2aba14895adc557e2514c6cdc76c4c6676a3757b`.
Local GNU oracle: Ubuntu binutils 2.42 in px13-ubuntu, image digest
`sha256:07a8e41ba851830767513df2cc78cd319c79d7f4638d85beb351a61486ff693b`.

| Binary | SHA-256 |
|---|---|
| ld.bfd | e9ceb054c12207970f2726dfc07e9a66b411602748628baf27399f02a9bbb31b |
| readelf | 64c58e15274bbbb5153f31078e455e9e77ee5f51489e709bba5bb788ce9df2b0 |
| nm | 3708df3d7ce16e2c1dcdcd722784ae382d4d582276a71ab7bbe2d542f5621202 |
| objdump | 325c4205a4c658a9d1e1ebc469ae55975a2b897a3d3c1e79d9b158612d37f745 |
| ar | 6452af2eea333b8c65e1adb92964fc8f97863ab003fa13f9d12bff5345cd7dbe |

The native link bundle is extracted from the published PAX dev ISO
SHA-256 `02f979bedf5520661f8a5e5623f1f9a7f5cb18b2b1d8c936b3d51f8c0336d4d9`.
The ISO contains `/boot/initramfs.cpio`; only the named binary inputs are
extracted from that archive. Both the hash and size of each file are checked
against PAX's `user/wolf-link.sums` before use. No source rebuild is substituted.

## CI binary-package oracle

CI uses only Ubuntu 24.04 binary packages, pinned in `ci/oracle.Containerfile`:
`lld-17=1:17.0.6-9ubuntu1`, `binutils=2.42-4ubuntu2.10`,
`musl-dev=1.2.4-2`, `musl-tools=1.2.4-2` and
`build-essential=12.10ubuntu1`. The lld binary SHA-256 is
`4379d66509f61190ebeb1661666609464cb51f995e4ae8d0423b1f547ae39ed4`;
the binutils hashes match the table above. The local image digest is
`sha256:4e921f9058653b9c7b0e0c127fb2247c587adbd81190bf78e81e64c1b3599495`.

The generated CI C fixture exercises musl CRT startup, TLS, initialization
arrays, static archive extraction, relocation retention and a real run.
CI does not possess the PAX-specific musl runtime archive or its exact lld
build. Wolf 0.2.35's public Linux archives target glibc and cannot substitute
for that musl runtime (the link fails on `open64`, `fstat64` and unwind
references). The full PAX/Wolf corpus is a separate local strict run; these
fixtures are not represented as that corpus.

The public glibc runtime additionally contains empty, excluded
`SHT_LLVM_ADDRSIG` sections: LLVM 17 Language Reference Extensions,
“Address-significance tables”, <https://llvm.org/docs/Extensions.html>.
The reader recognizes only the empty, `SHF_EXCLUDE` form; a nonempty table
is refused by name rather than pretending to interpret its ULEB128 payload.
The same archive emits an eight-byte `SHT_INIT_ARRAY` with `sh_entsize=0`;
the reader accepts 0 or 8 there while requiring size divisible by 8.

## Static writer references

* Generic ABI, chapter 4 "Symbol Table": strong/weak/common precedence,
  archive extraction for undefined global (not undefined weak) references,
  and propagation of the most constraining visibility; "Section Groups":
  first COMDAT selection. Chapter 5 "Program Header": LOAD and TLS images.
* AMD64 ABI 1.0, 12 March 2025, section 4.4/table 4.9 and section 4.5:
  relocation equations and static TLS offsets; section 11, tables 11.1,
  11.3, 11.7 and 11.9: recognized LP64 GD/LD transitions. Appendix B:
  GOT-load optimization is conditional on the final target being representable.
  Published PDF: <https://gitlab.com/x86-psABIs/x86-64-ABI/-/jobs/artifacts/master/raw/x86-64-ABI/abi.pdf?job=build>.
* GNU ld 2.42 manual, Options: `--start-group`, `--undefined`, `--defsym`,
  `--gc-sections`; LLD 17 ELF command documentation for the corresponding
  black-box controls. No implementation source was used.
* LLD 18.1.3 binary control identities and exact argv are recorded in
  `notes/ld01/evidence/lld18-control-results.json`. All five selected input sets
  are structurally unchanged between the pinned LLD 17 and that LLD 18 binary.
* PAX `tests/mpx5-bore`, `tools/qemu-halt`, `tools/qemu-run` and
  `tools/mkinitramfs`: guest output capture, halt proof and initramfs format.
  The copied dev ISO supplies the unchanged kernel binary; no kernel source
  was read or rebuilt.
