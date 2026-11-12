"""Where a linked output's provenance lives, read independently for the test witnesses.

A ligature output carries a 116-byte `.note.wolf.link`. With note flags 0 the manifest is the
output's own `.wolf.link.manifest` section and the retained relocations are its SHT_RELA sections
(the embedded form, `--provenance=embed`). With flags 1 both are in the sidecar file beside the
output, OUTPUT.provenance (the default): a 40-byte head ("WLPROV01", the output's size, the table
count, the manifest's offset and size, little-endian u64s), a 32-byte record per retained table
(target section, symbol table, entries' offset, entry count), the tables' Elf64_Rela entries, then
the manifest. The note's first digest is the manifest's (embedded) or the whole sidecar's; the
second is the output's with both digest slots zero.
"""
import hashlib
import pathlib
import struct

SIDECAR_MAGIC = b'WLPROV01'


def sidecar(path):
    """The sidecar's path beside an output."""
    return pathlib.Path(str(path) + '.provenance')


def section_table(data):
    """The output's section headers, and a map from each section name to its header."""
    shoff = struct.unpack_from('<Q', data, 40)[0]
    count, names = struct.unpack_from('<HH', data, 60)
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + 64 * i) for i in range(count)]
    strings = data[headers[names][4]:headers[names][4] + headers[names][5]]
    return {strings[h[0]:].split(b'\0', 1)[0].decode(): h for h in headers}, headers


def load(path):
    """Read an output's provenance from wherever its note says it is."""
    path = pathlib.Path(path)
    data = path.read_bytes()
    sections, headers = section_table(data)
    n = sections['.note.wolf.link']
    note = data[n[4]:n[4] + n[5]]
    flags = struct.unpack_from('<I', note, 24)[0]
    p = {'path': path, 'data': data, 'sections': sections, 'headers': headers, 'note_offset': n[4],
         'note': note}
    if flags == 1:
        side = sidecar(path).read_bytes()
        magic, total, count, offset, size = struct.unpack_from('<8sQQQQ', side, 0)
        assert magic == SIDECAR_MAGIC and total == len(data) and offset + size == len(side), (
            'sidecar head', magic, total, len(data), offset, size, len(side))
        tables = []
        for t in range(count):
            info, link, at, entries = struct.unpack_from('<QQQQ', side, 40 + 32 * t)
            tables.append({'info': info, 'link': link, 'entries': side[at:at + 24 * entries]})
        p.update(mode='sidecar', side=side, manifest_offset=offset, manifest_size=size,
                 manifest=side[offset:offset + size], tables=tables)
    else:
        m = sections['.wolf.link.manifest']
        tables = [{'info': h[7], 'link': h[6], 'entries': data[h[4]:h[4] + h[5]]}
                  for h in headers if h[1] == 4]
        p.update(mode='embedded', side=None, manifest_offset=m[4], manifest_size=m[5],
                 manifest=data[m[4]:m[4] + m[5]], tables=tables)
    return p


def write(p, path, data=None, manifest=None, side=None, pad=b'\0', reseal=True):
    """Write p's output (or `data`) to path, with its sidecar (or `side`) beside it when p has
    one, the manifest replaced by `manifest` padded with `pad` to its size; `reseal` recomputes
    both of the note's digests, so that a check past the digests must refuse the change."""
    out = bytearray(p['data'] if data is None else data)
    holder = None if p['mode'] == 'embedded' else bytearray(p['side'] if side is None else side)
    target = out if holder is None else holder
    if manifest is not None:
        size = p['manifest_size']
        assert len(manifest) <= size, (len(manifest), size)
        target[p['manifest_offset']:p['manifest_offset'] + size] = manifest + pad * (size - len(manifest))
    if reseal:
        n = p['note_offset']
        out[n + 44:n + 108] = bytes(64)
        whole = hashlib.sha256(out).digest()
        bound = holder if holder is not None else out[p['manifest_offset']:p['manifest_offset'] + p['manifest_size']]
        out[n + 44:n + 76] = hashlib.sha256(bound).digest()
        out[n + 76:n + 108] = whole
    path = pathlib.Path(path)
    path.write_bytes(out)
    if holder is not None:
        sidecar(path).write_bytes(holder)
    elif sidecar(path).exists():
        sidecar(path).unlink()
    return path


def same_files(a, b):
    """Whether two outputs are the same file and, when they have sidecars, the same sidecar."""
    a, b = pathlib.Path(a), pathlib.Path(b)
    if a.read_bytes() != b.read_bytes() or sidecar(a).exists() != sidecar(b).exists():
        return False
    return not sidecar(a).exists() or sidecar(a).read_bytes() == sidecar(b).read_bytes()
