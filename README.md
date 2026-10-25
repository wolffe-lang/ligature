# ligature

A linker, written in [wolf](https://github.com/wolffe-lang/wolf-lang). A ligature
ties notes into one; this one ties the objects `wolf build` emits, the runtime
archive and a C library's objects into a program, so that a wolf toolchain
needs no C toolchain binary to link. Its first target is static x86-64 ELF for
Linux and [PAX](https://github.com/wolffe-lang/pax); its first job is to take
`lld` and the `cc` front end off the PAX image.

State: nothing links yet. Track 17 of the planning repo opened 2026-10-25; the
first lane (ld00, the map) writes the ELF reader, the relocation census over
every object PAX links, the oracle harness and this README's real contents.

Licence: Apache-2.0 (`LICENSE`).
