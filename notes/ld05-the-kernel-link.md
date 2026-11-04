# ld05 — the kernel link: the licensed musl link bundle

_Materialised from the body of ligature#27 at the merge (`5d460e59`)._

## Prediction

This pass completes licensed bundle staging only. The kernel/performance work is deferred; no new M4 or speed claim is made. The baseline hello link measured 261.733 seconds on Linux; the attempted phase-profiling build refused W0314, and that instrumentation has been reverted from this PR.

- `e635013`: predict licence-roster refusal, deterministic licensed packaging and unpacked execution.
- `e787d35`: commit the missing-licence regression before its fix.
- `d7b4470`: complete component licences, source inventory, strict manifest and unpacked smoke test.
- `f031a92`: name the PC32 plant failure explicitly.
- `5d460e5`: refresh README for staging and correct the obsolete Linux self-link paragraph.

## Forbidden

No external linker, libc or kernel implementation source read. Only specific licence/attribution members were extracted from upstream archives; source files stayed unopened. No publication, tag, release, label, merge or issue closure. No live binary pin changed. Upstream licence whitespace is retained byte for byte, including trailing spaces and final blank lines.

## Inputs verified

Rebased onto trunk `9f7c2e3`. The original seven control/sysroot binaries are unchanged; only the old runtime is replaced by the published wolf 0.2.36 musl runtime (`6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad`).

- LLVM 17.0.6 source archive SHA-256 `58a8818c60e6627064f312dbf46c02d9949956558340938b71cf731ad8bc0813`, read twice; only licence/credit documents extracted.
- musl 1.2.5 archive `a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4`, read twice; only COPYRIGHT extracted.
- Rust 1.97.1 distribution `9819d0a32d56bd339585319c80260e332779f5541fd66838ab7e016d6c814819`, checked twice against its published checksum; only licence and standard-library notice files extracted.
- Runtime libc bindings 0.2.189 crate `3eaf3ede3fee6db1a4c2ee091bf8a8b4dccdc6d17f656fb07896ee72867612f2`, checked twice against the runtime's Cargo.lock; only the two licence files extracted.
- PAX and runtime licences retained unchanged. The musl COPYRIGHT references notices embedded in implementation files, so an unchanged Debian musl 1.2.5 copyright inventory supplies those supplementary notices without reading source code. It is clearly identified as supplementary, not represented as Alpine's source.

`bundle/notices/SOURCES.json` records each original member, source URL, archive digest where applicable, size and text digest. `NOTICE` names every binary, its version, licence and corresponding source/build-recipe URLs. It also covers the Rust standard library, LLVM static dependencies, LLVM Support's regex/BLAKE3 notices, and the frontend/runtime licences.

## Evidence index

- Red before fix on Linux at `e787d35`: `bundle-licence-roster: missing complete notices`, exit 1.
- `tests/stage-bundle.py`: deterministic archive bytes; mandatory licences; complete MANIFEST; every member hashed twice; seven refusal cases including missing/altered/symlinked/uninventoried notices.
- `tests/bundle-smoke.py`: unpack the actual archive, hash every file twice, check the manifest and LLD version, link and execute hello through bundled cc/LLD and ligature, and verify the latter.
- `tests/pc32.py`: independent equations against candidate, LLD17 and GNU ld. Final plant branch `ld05-plant-pc32-plus-four-final`, commit `7b5e330`, one break on final head `5d460e5`; observed `FAIL pc32-equation candidate: actual=20 expected=16`. No plant PR.
- Final-head green record: six successful steps, full core gate, unpacked smoke and executable self-link (25 objects, two identical seed links and an identical bootstrap relink). Plant record: the named PC32 failure, worst=1, steps=3. Both complete records appear below, unchanged.
- Archive: `musl-link-bundle-sha256-8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a.tar.gz`, 36,514,237 bytes, 38 members. Archive SHA-256 `8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a`. MANIFEST SHA-256 `8bcea75770a47a23f619ad778d05c84a028f2e840964302d164195ea74e73886`. Every member was hashed twice after packing, twice after unpacking, and twice after transfer to the Mac.
- Durable record copies: `/Users/mfwolffe/lanes/ld05/final-evidence/green-record.log` and `/Users/mfwolffe/lanes/ld05/final-evidence/plant-record.log`. Bundle and MANIFEST: `/Users/mfwolffe/lanes/ld05/licensed-stage/`. Both linked hello outputs print `hello, wolf` and exit 0. Publication is held.

**R-ld05-4:** retain unchanged complete component notices and strict manifest rather than publish the binary-only archive; implemented. **R-ld05-2:** stage only, leaving live download pins unchanged until publication; retained. **R-ld05-1/3:** do not remove relocation evidence for speed or change PAX's default linker; neither is changed here.

<details>
<summary>Green record (complete)</summary>

```text
RECORD repo=ligature head=5d460e59c3497017d27d5bb0cf0a0fd89da1736a tree=7314855a251223f7fbd8e681d6221acca742fa4a host=kasumi boot=db705914-53d6-4a8f-a7e1-6d768fd5271d start=2026-11-04T00:33:09Z
START fetch-toolchain
  wolf-0.2.36-x86_64-unknown-linux-gnu d383c74c8cd123b9d9dfaa268271d4f004294f85c2b230237d0ef07027d9500d
  wolf-0.2.36-x86_64-unknown-linux-gnu d383c74c8cd123b9d9dfaa268271d4f004294f85c2b230237d0ef07027d9500d
  lupin-0.1.58-x86_64-unknown-linux-gnu 34f52792bb59bc7565e0edc1235cd47d9a6ad13d5e6528993627f2e699b62193
  lupin-0.1.58-x86_64-unknown-linux-gnu 34f52792bb59bc7565e0edc1235cd47d9a6ad13d5e6528993627f2e699b62193
  wolf-rt-0.2.36-x86_64-unknown-linux-musl sha256 3aba9c8b4e5c51f2094242946fae0e6f1cd64bc7837b7484e1085ce63373aa57
  wolf-rt-0.2.36-x86_64-unknown-linux-musl sha256 3aba9c8b4e5c51f2094242946fae0e6f1cd64bc7837b7484e1085ce63373aa57
  wolf-rt-0.2.36-x86_64-unknown-linux-musl/libwolf_rt.a sha256 6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad
  wolf-rt-0.2.36-x86_64-unknown-linux-musl/libwolf_rt.a sha256 6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad
  musl runtime: archive, runtime and SHA256SUMS verified; .wolf-bin/musl/libwolf_rt.a; distinct from the link bundle
END fetch-toolchain exit=0 secs=14.846
START fetch-bundle
  link-bundle sha256 6f99a2794da54b2dd85f06713d736b27862a7cd0da9e28bd940d975a4603a1d1
  link-bundle sha256 6f99a2794da54b2dd85f06713d736b27862a7cd0da9e28bd940d975a4603a1d1
  link-bundle: exact binary inputs verified twice; ligature#13
END fetch-bundle exit=0 secs=22.637
START core
  {"event":"suite","file":"src/address_test.lu","schema":"wolf-test/0","tests":1}
  {"detail":"exit(0)","event":"test","file":"src/address_test.lu","name":"main","schema":"wolf-test/0","status":"pass"}
  {"event":"suite","file":"src/kernel_relocation_test.lu","schema":"wolf-test/0","tests":1}
  {"detail":"exit(0)","event":"test","file":"src/kernel_relocation_test.lu","name":"main","schema":"wolf-test/0","status":"pass"}
  {"event":"suite","file":"src/reader_test.lu","schema":"wolf-test/0","tests":1}
  {"detail":"exit(0)","event":"test","file":"src/reader_test.lu","name":"main","schema":"wolf-test/0","status":"pass"}
  {"event":"suite","file":"src/script_profile_test.lu","schema":"wolf-test/0","tests":1}
  {"detail":"exit(0)","event":"test","file":"src/script_profile_test.lu","name":"main","schema":"wolf-test/0","status":"pass"}
  {"event":"summary","failed":0,"filtered_out":0,"native":0,"passed":4,"rejected":0,"schema":"wolf-test/0","stopped_early":false,"unsupported":0}
  pc32-equation: three linker equations and executed outputs; 0 SKIP
  stage-bundle: deterministic licensed bytes, complete manifest, replacement runtime, seven refusals; 0 SKIP
  fetch-bundle: mismatched archive refused before extraction; 0 SKIP
  fetch-musl-runtime: mismatched archive refused before extraction; 0 SKIP
  self-link blocker: exact fetched runtime digest and reproduced argv status required; other digests hard-gated; 0 SKIP
  script-profile: 31 rows, 0 SKIP; preflight only; executable kernel links require explicit -T
  archive-write: 35 process rows, deterministic bytes and independent index; three executed links, 0 SKIP
  kernel-script: three executable links, u64 provenance, bounds, permissions, ordering, discards, independent sites, deterministic bytes and refusals; 0 SKIP
  aarch64: 51 independent ELF/range/alignment/mask/pair/GOT/refusal rows; no fixture execution claimed, 0 SKIP
  addrsig: valid symbol index consumed without folding; four malformed forms refused; 0 SKIP
  integration: 43 process rows, 0 SKIP
  oracle: 2 musl links, 2 deterministic relinks, 2 differ plants, 4 verify plants, 0 SKIP
  resolution: 16 oracle rows, 0 SKIP
  resolve: strong/weak/common, indexed archives, groups, duplicate names, COMDAT; 0 SKIP
  lazy-order: forward/backward discovery matches LLD, four-member cyclic graph selected once; 0 SKIP
  writer: 10 three-linker behavior rows, determinism, named refusals and TLS-negative rows; 0 SKIP
  relocation-witness: three linkers, retained sites, unused data/debug corruption red, local/entry normalization; 0 SKIP
  relocation-witness: all writer cases independently decoded, including four TLS models; 0 SKIP
  cc frontend: exact compiler-style option subset links and runs; 0 SKIP
  provenance: canonical manifest, independent SHA256 checks, four negative rows; 0 SKIP
  attribution: complete disjoint coverage, explain, deterministic relink, delta locality, five resealed negative rows; 0 SKIP
  attribution: aliases, archive path, TLS/NOBITS, ambiguous locals and explicit member selection; 0 SKIP
  compact-manifest: legacy JSON explain parity and dropped provenance record refused; 0 SKIP
  explain: dependency sites and distinct discarded-section causes; 0 SKIP
  compact-manifest: five resealed decoder corruptions rejected, signed addend endpoints preserved; 0 SKIP
  compact-manifest: arbitrary-byte symbol text matches legacy JSON origins; 0 SKIP
  PAX transcript validator: one genuine capture, four rejected mutations; replay only, 0 SKIP
  PAX staging: gzip evidence preserves exact program bytes and identical initramfs; 0 SKIP
  static-pax runner: report preserved, nonzero differ status preserved, 0 SKIP
  TLS classification: same named payload despite ordering/binding changes; changed payload remains unequal; no findings waived; 0 SKIP
  named-findings: 87 individually retained; 0 waivers; 0 SKIP
  named-findings: five mutation witnesses rejected; 0 SKIP
  kernel edge: lld17 refuses -2147483652; GNU default refuses, GNU --no-relax keeps GOT load; LLD18 control is separate in tests/ld04-controls.py
  layout-controls: three-linker merge/unwind measurements and two-oracle kernel.ld scope; no high-half ELF executed; 0 SKIP
  roundtrip: PASS .wolf-bin/libwolf_rt.a
END core exit=0 secs=5.131
START stage-licensed-bundle
  {
    "archive": "musl-link-bundle-sha256-8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a.tar.gz",
    "bytes": 36514237,
    "format": "ligature.staged-bundle.v2",
    "members": {
      "LICENSES/libc-rust/LICENSE-APACHE": {
        "sha256": "62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a",
        "sha256_read_twice": [
          "62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a",
          "62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a"
        ],
        "size": 9723
      },
      "LICENSES/libc-rust/LICENSE-MIT": {
        "sha256": "123a331b5dbf04c30097fa43b8f858bc85df671fe776de498d01f3d6b7c1f69e",
        "sha256_read_twice": [
          "123a331b5dbf04c30097fa43b8f858bc85df671fe776de498d01f3d6b7c1f69e",
          "123a331b5dbf04c30097fa43b8f858bc85df671fe776de498d01f3d6b7c1f69e"
        ],
        "size": 1066
      },
      "LICENSES/llvm/compiler-rt/CREDITS.TXT": {
        "sha256": "a9901f47a089da41e4690682d00ce4cedaa2baf41fedbe79beee366d43ac2461",
        "sha256_read_twice": [
          "a9901f47a089da41e4690682d00ce4cedaa2baf41fedbe79beee366d43ac2461",
          "a9901f47a089da41e4690682d00ce4cedaa2baf41fedbe79beee366d43ac2461"
        ],
        "size": 1049
      },
      "LICENSES/llvm/compiler-rt/LICENSE.TXT": {
        "sha256": "1a8f1058753f1ba890de984e48f0242a3a5c29a6a8f2ed9fd813f36985387e8d",
        "sha256_read_twice": [
          "1a8f1058753f1ba890de984e48f0242a3a5c29a6a8f2ed9fd813f36985387e8d",
          "1a8f1058753f1ba890de984e48f0242a3a5c29a6a8f2ed9fd813f36985387e8d"
        ],
        "size": 16708
      },
      "LICENSES/llvm/libcxx/CREDITS.TXT": {
        "sha256": "054e099bf5954c8821b880f5751d2fbf221bf43cf7c57ac1c2c5ff6263d6d9c3",
        "sha256_read_twice": [
          "054e099bf5954c8821b880f5751d2fbf221bf43cf7c57ac1c2c5ff6263d6d9c3",
          "054e099bf5954c8821b880f5751d2fbf221bf43cf7c57ac1c2c5ff6263d6d9c3"
        ],
        "size": 4124
      },
      "LICENSES/llvm/libcxx/LICENSE.TXT": {
        "sha256": "539dd7aed86e8a4f12cbdd0e6c50c189c7d74847e4fecc64ce2c6ee3a01da38b",
        "sha256_read_twice": [
          "539dd7aed86e8a4f12cbdd0e6c50c189c7d74847e4fecc64ce2c6ee3a01da38b",
          "539dd7aed86e8a4f12cbdd0e6c50c189c7d74847e4fecc64ce2c6ee3a01da38b"
        ],
        "size": 16703
      },
      "LICENSES/llvm/libcxxabi/CREDITS.TXT": {
        "sha256": "a259fff28a51623f14917dd68f97f3af7804984087ddc1bfd8196d08ebb75b83",
        "sha256_read_twice": [
          "a259fff28a51623f14917dd68f97f3af7804984087ddc1bfd8196d08ebb75b83",
          "a259fff28a51623f14917dd68f97f3af7804984087ddc1bfd8196d08ebb75b83"
        ],
        "size": 1660
      },
      "LICENSES/llvm/libcxxabi/LICENSE.TXT": {
        "sha256": "e2b35be49f7284a45b7baca8fc7b3ab7440e7902392b2528a457816b5bb2a15c",
        "sha256_read_twice": [
          "e2b35be49f7284a45b7baca8fc7b3ab7440e7902392b2528a457816b5bb2a15c",
          "e2b35be49f7284a45b7baca8fc7b3ab7440e7902392b2528a457816b5bb2a15c"
        ],
        "size": 16706
      },
      "LICENSES/llvm/libunwind/LICENSE.TXT": {
        "sha256": "b5efebcaca80879234098e52d1725e6d9eb8fb96a19fce625d39184b705f7b6d",
        "sha256_read_twice": [
          "b5efebcaca80879234098e52d1725e6d9eb8fb96a19fce625d39184b705f7b6d",
          "b5efebcaca80879234098e52d1725e6d9eb8fb96a19fce625d39184b705f7b6d"
        ],
        "size": 16706
      },
      "LICENSES/llvm/lld/LICENSE.TXT": {
        "sha256": "f7891568956e34643eb6a0db1462db30820d40d7266e2a78063f2fe233ece5a0",
        "sha256_read_twice": [
          "f7891568956e34643eb6a0db1462db30820d40d7266e2a78063f2fe233ece5a0",
          "f7891568956e34643eb6a0db1462db30820d40d7266e2a78063f2fe233ece5a0"
        ],
        "size": 15138
      },
      "LICENSES/llvm/llvm/LICENSE.TXT": {
        "sha256": "8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee",
        "sha256_read_twice": [
          "8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee",
          "8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee"
        ],
        "size": 15141
      },
      "LICENSES/llvm/llvm/include/llvm/Support/LICENSE.TXT": {
        "sha256": "54cbc326a78b9400065bfc5830a57fdcdaf808286d4ac35d8a9e324aa77b7241",
        "sha256_read_twice": [
          "54cbc326a78b9400065bfc5830a57fdcdaf808286d4ac35d8a9e324aa77b7241",
          "54cbc326a78b9400065bfc5830a57fdcdaf808286d4ac35d8a9e324aa77b7241"
        ],
        "size": 303
      },
      "LICENSES/llvm/llvm/lib/Support/BLAKE3/LICENSE": {
        "sha256": "6a94bedb8b707ed97f6e310d0d015ab14e0683ffa0a612b02958581b9cc9fc0e",
        "sha256_read_twice": [
          "6a94bedb8b707ed97f6e310d0d015ab14e0683ffa0a612b02958581b9cc9fc0e",
          "6a94bedb8b707ed97f6e310d0d015ab14e0683ffa0a612b02958581b9cc9fc0e"
        ],
        "size": 18691
      },
      "LICENSES/llvm/llvm/lib/Support/COPYRIGHT.regex": {
        "sha256": "0424e57d4303164dc59a8509c20dae0518b853692e5c2b0e98b11816fdbc97c7",
        "sha256_read_twice": [
          "0424e57d4303164dc59a8509c20dae0518b853692e5c2b0e98b11816fdbc97c7",
          "0424e57d4303164dc59a8509c20dae0518b853692e5c2b0e98b11816fdbc97c7"
        ],
        "size": 2718
      },
      "LICENSES/musl/COPYRIGHT": {
        "sha256": "f9bc4423732350eb0b3f7ed7e91d530298476f8fec0c6c427a1c04ade22655af",
        "sha256_read_twice": [
          "f9bc4423732350eb0b3f7ed7e91d530298476f8fec0c6c427a1c04ade22655af",
          "f9bc4423732350eb0b3f7ed7e91d530298476f8fec0c6c427a1c04ade22655af"
        ],
        "size": 6204
      },
      "LICENSES/musl/debian-copyright": {
        "sha256": "8d51fb83b8860aca6362ccf2b4eaa71362e7c2ca54c09cdaa5da18e419ef4a91",
        "sha256_read_twice": [
          "8d51fb83b8860aca6362ccf2b4eaa71362e7c2ca54c09cdaa5da18e419ef4a91",
          "8d51fb83b8860aca6362ccf2b4eaa71362e7c2ca54c09cdaa5da18e419ef4a91"
        ],
        "size": 10801
      },
      "LICENSES/pax/LICENSE": {
        "sha256": "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
        "sha256_read_twice": [
          "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
          "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"
        ],
        "size": 35149
      },
      "LICENSES/pax/LICENSE-TRAINING-DATA": {
        "sha256": "39d16667f8215642b3e1f6b65c5169dc4ca288c5cef87b17f2c16a0be5a74da3",
        "sha256_read_twice": [
          "39d16667f8215642b3e1f6b65c5169dc4ca288c5cef87b17f2c16a0be5a74da3",
          "39d16667f8215642b3e1f6b65c5169dc4ca288c5cef87b17f2c16a0be5a74da3"
        ],
        "size": 1450
      },
      "LICENSES/rust/COPYRIGHT-library.html": {
        "sha256": "0a65bb747c49c7bb816cbc7188319bd6e4e8d08091c1190b8a3c0971c47968ed",
        "sha256_read_twice": [
          "0a65bb747c49c7bb816cbc7188319bd6e4e8d08091c1190b8a3c0971c47968ed",
          "0a65bb747c49c7bb816cbc7188319bd6e4e8d08091c1190b8a3c0971c47968ed"
        ],
        "size": 279302
      },
      "LICENSES/rust/licenses/Apache-2.0.txt": {
        "sha256": "074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff",
        "sha256_read_twice": [
          "074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff",
          "074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff"
        ],
        "size": 10280
      },
      "LICENSES/rust/licenses/BSD-2-Clause.txt": {
        "sha256": "f32fb3b417a194167cfad068223fc975ba96c5960513a10f66a3c28720aec1df",
        "sha256_read_twice": [
          "f32fb3b417a194167cfad068223fc975ba96c5960513a10f66a3c28720aec1df",
          "f32fb3b417a194167cfad068223fc975ba96c5960513a10f66a3c28720aec1df"
        ],
        "size": 1267
      },
      "LICENSES/rust/licenses/LLVM-exception.txt": {
        "sha256": "e34c58338bd89d43e709e226610d8f32b3e3c47f4ad9a99a8dc1d4ac7842488e",
        "sha256_read_twice": [
          "e34c58338bd89d43e709e226610d8f32b3e3c47f4ad9a99a8dc1d4ac7842488e",
          "e34c58338bd89d43e709e226610d8f32b3e3c47f4ad9a99a8dc1d4ac7842488e"
        ],
        "size": 919
      },
      "LICENSES/rust/licenses/MIT.txt": {
        "sha256": "b85dcd3e453d05982552c52b5fc9e0bdd6d23c6f8e844b984a88af32570b0cc0",
        "sha256_read_twice": [
          "b85dcd3e453d05982552c52b5fc9e0bdd6d23c6f8e844b984a88af32570b0cc0",
          "b85dcd3e453d05982552c52b5fc9e0bdd6d23c6f8e844b984a88af32570b0cc0"
        ],
        "size": 1078
      },
      "LICENSES/rust/licenses/NCSA.txt": {
        "sha256": "39cb0234065c92b9e6cee3830cbb52b1aa289aa8fe9ba2e66730fec5cf05c630",
        "sha256_read_twice": [
          "39cb0234065c92b9e6cee3830cbb52b1aa289aa8fe9ba2e66730fec5cf05c630",
          "39cb0234065c92b9e6cee3830cbb52b1aa289aa8fe9ba2e66730fec5cf05c630"
        ],
        "size": 1676
      },
      "LICENSES/rust/licenses/Unicode-3.0.txt": {
        "sha256": "f5062c9a188d81dfe66b56db4182dcf9e4b17c0d9b0d311a8e20b3a1b075c443",
        "sha256_read_twice": [
          "f5062c9a188d81dfe66b56db4182dcf9e4b17c0d9b0d311a8e20b3a1b075c443",
          "f5062c9a188d81dfe66b56db4182dcf9e4b17c0d9b0d311a8e20b3a1b075c443"
        ],
        "size": 1995
      },
      "LICENSES/wolf/LICENSE": {
        "sha256": "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
        "sha256_read_twice": [
          "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
          "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"
        ],
        "size": 35149
      },
      "LICENSES/wolf/LICENSE-EXCEPTION": {
        "sha256": "a0eec20d7b98b1cd0e5b4d23c3965667c97b68fb365ec95a9516b0c3cbc4fec4",
        "sha256_read_twice": [
          "a0eec20d7b98b1cd0e5b4d23c3965667c97b68fb365ec95a9516b0c3cbc4fec4",
          "a0eec20d7b98b1cd0e5b4d23c3965667c97b68fb365ec95a9516b0c3cbc4fec4"
        ],
        "size": 1273
      },
      "MANIFEST": {
        "sha256": "8bcea75770a47a23f619ad778d05c84a028f2e840964302d164195ea74e73886",
        "sha256_read_twice": [
          "8bcea75770a47a23f619ad778d05c84a028f2e840964302d164195ea74e73886",
          "8bcea75770a47a23f619ad778d05c84a028f2e840964302d164195ea74e73886"
        ],
        "size": 3510
      },
      "NOTICE": {
        "sha256": "d63118282bb45cc651d8614f4281f60617d46a1102a320329fd1f7ce0a0db94f",
        "sha256_read_twice": [
          "d63118282bb45cc651d8614f4281f60617d46a1102a320329fd1f7ce0a0db94f",
          "d63118282bb45cc651d8614f4281f60617d46a1102a320329fd1f7ce0a0db94f"
        ],
        "size": 5135
      },
      "SOURCES.json": {
        "sha256": "849c40ac2f9f148063110b6aa8f2ee772cab626426753f1015ba6b81c38a808d",
        "sha256_read_twice": [
          "849c40ac2f9f148063110b6aa8f2ee772cab626426753f1015ba6b81c38a808d",
          "849c40ac2f9f148063110b6aa8f2ee772cab626426753f1015ba6b81c38a808d"
        ],
        "size": 11717
      },
      "cc": {
        "sha256": "3161aea27abb8beeb669cc6499fa9dc162014b69eecc6fb0d169eed5def25b11",
        "sha256_read_twice": [
          "3161aea27abb8beeb669cc6499fa9dc162014b69eecc6fb0d169eed5def25b11",
          "3161aea27abb8beeb669cc6499fa9dc162014b69eecc6fb0d169eed5def25b11"
        ],
        "size": 499760
      },
      "ld.lld": {
        "sha256": "1217ca75f9df70439294844b2aba14895adc557e2514c6cdc76c4c6676a3757b",
        "sha256_read_twice": [
          "1217ca75f9df70439294844b2aba14895adc557e2514c6cdc76c4c6676a3757b",
          "1217ca75f9df70439294844b2aba14895adc557e2514c6cdc76c4c6676a3757b"
        ],
        "size": 66247008
      },
      "libwolf_rt.a": {
        "sha256": "6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad",
        "sha256_read_twice": [
          "6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad",
          "6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad"
        ],
        "size": 46700882
      },
      "sysroot/crt1.o": {
        "sha256": "51dba24287eb9b1e74f3c7cb8ea5464491d3a4ba54c016722f149179d08f90f6",
        "sha256_read_twice": [
          "51dba24287eb9b1e74f3c7cb8ea5464491d3a4ba54c016722f149179d08f90f6",
          "51dba24287eb9b1e74f3c7cb8ea5464491d3a4ba54c016722f149179d08f90f6"
        ],
        "size": 5560
      },
      "sysroot/crti.o": {
        "sha256": "5cbc84c78a23cdddda0db8cdcd5ec3b5a15b6b555510bd97e4c5a0334aca7b49",
        "sha256_read_twice": [
          "5cbc84c78a23cdddda0db8cdcd5ec3b5a15b6b555510bd97e4c5a0334aca7b49",
          "5cbc84c78a23cdddda0db8cdcd5ec3b5a15b6b555510bd97e4c5a0334aca7b49"
        ],
        "size": 2816
      },
      "sysroot/crtn.o": {
        "sha256": "d884ee5f9120490b98bb43496f88983ee379a0d2ebf027574fcca7eae9aaa1e7",
        "sha256_read_twice": [
          "d884ee5f9120490b98bb43496f88983ee379a0d2ebf027574fcca7eae9aaa1e7",
          "d884ee5f9120490b98bb43496f88983ee379a0d2ebf027574fcca7eae9aaa1e7"
        ],
        "size": 2760
      },
      "sysroot/libc.a": {
        "sha256": "8e69a73c464a86fd8b278f3aa08ab2640b720157e92b45a2d34441c22248ddd4",
        "sha256_read_twice": [
          "8e69a73c464a86fd8b278f3aa08ab2640b720157e92b45a2d34441c22248ddd4",
          "8e69a73c464a86fd8b278f3aa08ab2640b720157e92b45a2d34441c22248ddd4"
        ],
        "size": 10961970
      },
      "sysroot/libunwind.a": {
        "sha256": "264296d61db52859cc7a8cd6a7a09fc62bde189aa3ea8867fb62ef5129b694bc",
        "sha256_read_twice": [
          "264296d61db52859cc7a8cd6a7a09fc62bde189aa3ea8867fb62ef5129b694bc",
          "264296d61db52859cc7a8cd6a7a09fc62bde189aa3ea8867fb62ef5129b694bc"
        ],
        "size": 201794
      }
    },
    "published": false,
    "runtime_sha256": "6892dac8a6e211f12c6823c0f19497d820a47fdbfe7fb569cd967acf86461aad",
    "sha256_read_twice": [
      "8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a",
      "8210ac2223d969ab8f0845cc74950a1c68226b58b10dd083cd2e2113acd3e37a"
    ]
  }
  STAGED ONLY: no release, tag, upload or live pin change
END stage-licensed-bundle exit=0 secs=16.914
START bundle-unpacked-smoke
  bundle-smoke: every unpacked file hashed twice; LLD version; cc/LLD and ligature hello executed; 0 SKIP
END bundle-unpacked-smoke exit=0 secs=259.820
START self-link
  musl-argv glibc 0 b'argc=3\n[--version]\n[space word]\n[]\n' b''
  musl-argv lld 0 b'argc=3\n[--version]\n[space word]\n[]\n' b''
  musl-argv gnu 0 b'argc=3\n[--version]\n[space word]\n[]\n' b''
  musl-argv c-musl 0 b'argc=3\n[--version]\n[space word]\n[]\n' b''
  musl-argv: all three Wolf links and pinned C/musl control preserve argv; 0 SKIP
  SELF-LINK objects START
  SELF-LINK objects PASS
  SELF-LINK first START
  SELF-LINK first PASS
  SELF-LINK second START
  SELF-LINK second PASS
  SELF-LINK verify START
  SELF-LINK verify PASS
  SELF-LINK execute START
  SELF-LINK execute PASS
  SELF-LINK third START
  SELF-LINK third PASS
  SELF-LINK hello-objects START
  SELF-LINK hello-objects PASS
  SELF-LINK hello-link START
  SELF-LINK hello-link PASS
  SELF-LINK hello-execute START
  SELF-LINK hello-execute PASS
  SELF-LINK hello-verify START
  SELF-LINK hello-verify PASS
  self-link: own objects, two seed links, executable bootstrap link, byte identity, executed hello; 0 SKIP
END self-link exit=0 secs=1005.950
RECORD-END worst=0 steps=6 end=2026-11-04T00:55:14Z
```
</details>

<details>
<summary>Plant record (complete)</summary>

```text
RECORD repo=ligature head=7b5e33007c22989e61bdbcacf4ac236fefdca3fe tree=7ab4352bc3bc5cd748db569ac1ee9dfc731e8370 host=kasumi boot=db705914-53d6-4a8f-a7e1-6d768fd5271d start=2026-11-04T00:55:14Z
PLANT base=5d460e59c3497017d27d5bb0cf0a0fd89da1736a branch=ld05-plant-pc32-plus-four-final
PLANT-ROW pc32-equation
START build
END build exit=0 secs=0.993
START pc32-equation
  FAIL pc32-equation candidate: actual=20 expected=16
  Traceback (most recent call last):
    File "/work/tests/pc32.py", line 47, in <module>
      raise AssertionError(('pc32-equation', name, actual, expected))
  AssertionError: ('pc32-equation', 'candidate', 20, 16)
FAIL pc32-equation candidate: actual=20 expected=16
END pc32-equation exit=1 secs=0.347
START record-wrapper
END record-wrapper exit=1 secs=0
RECORD-END worst=1 steps=3 end=2026-11-04T00:55:15Z
```
</details>

## Done-when


- [x] Rebase onto current CI routing; preserve the unfinished work separately.
- [x] Commit prediction and observe missing-licence regression red before the fix.
- [x] Include unchanged licence/notice texts and version/source attribution.
- [x] README read and refreshed in its own commit.
- [x] Final-head local green record, complete core/self-link gate and unpacked smoke.
- [x] Final-head PC32 plant red record.
- [x] Licensed archive MANIFEST and exact held publication command handed back.
- [x] Local lane audit exactly once: `AUDIT CLEAN (footprint: module)`. The sole informational warning is the boot UUID prefix being read as a possible bare commit token.

Publication remains held. Keep #12 and #13 open; no current-kernel qualification is claimed by this bundle-only completion. The earlier unlicensed staged archive must not be published.

