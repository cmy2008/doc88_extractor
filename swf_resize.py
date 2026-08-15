import argparse
import lzma
import struct
import zlib

PIXEL_TO_TWIP = 20


def _read_rect(reader):
    nbits = reader.read(5)
    xmin = reader.read_signed(nbits)
    xmax = reader.read_signed(nbits)
    ymin = reader.read_signed(nbits)
    ymax = reader.read_signed(nbits)
    return xmin, xmax, ymin, ymax


def _write_rect(xmin, xmax, ymin, ymax):
    nbits = max((v if v >= 0 else ~v).bit_length() + 1 for v in (xmin, xmax, ymin, ymax))
    nbits = max(nbits, 1)
    out = []
    out.extend((nbits >> i) & 1 for i in range(4, -1, -1))
    for v in (xmin, xmax, ymin, ymax):
        out.extend((v & ((1 << nbits) - 1)) >> i & 1 for i in range(nbits - 1, -1, -1))
    while len(out) % 8:
        out.append(0)
    return bytes(int("".join(map(str, out[i:i + 8])), 2) for i in range(0, len(out), 8))


class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, nbits):
        val = 0
        for _ in range(nbits):
            val = (val << 1) | ((self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1)
            self.pos += 1
        return val

    def read_signed(self, nbits):
        val = self.read(nbits)
        if val & (1 << (nbits - 1)):
            val -= 1 << nbits
        return val

    def align(self):
        self.pos = (self.pos + 7) // 8 * 8


def _decompress_body(sig, body):
    if sig[0] == ord("F"):
        return body
    if sig[0] == ord("C"):
        return zlib.decompress(body)
    if sig[0] == ord("Z"):
        size = struct.unpack("<I", body[0:4])[0]
        props = body[4:9]
        data = body[9:9 + size]
        return lzma.decompress(props + b"\xff" * 8 + data, format=lzma.FORMAT_ALONE)
    raise ValueError("Unsupported signature: %r" % sig)


def _compress_body(sig, body):
    if sig[0] == ord("F"):
        return body
    if sig[0] == ord("C"):
        return zlib.compress(body)
    if sig[0] == ord("Z"):
        alone = lzma.compress(body, format=lzma.FORMAT_ALONE)
        return struct.pack("<I", len(alone) - 13) + alone[:5] + alone[13:]
    raise ValueError("Unsupported signature: %r" % sig)


def swf_resize(input_path, output_path, width=None, height=None, framecount=None):
    with open(input_path, "rb") as f:
        data = f.read()
    if len(data) < 8:
        raise ValueError("File too short to be an SWF")

    sig = data[0:3]
    if sig not in (b"FWS", b"CWS", b"ZWS"):
        raise ValueError("Not an SWF (bad signature)")

    version = data[3]
    file_len = struct.unpack("<I", data[4:8])[0]
    body = _decompress_body(sig, data[8:])

    reader = BitReader(body)
    xmin, xmax, ymin, ymax = _read_rect(reader)
    reader.align()
    rect_end = reader.pos // 8
    rest = body[rect_end:]

    old_w = (xmax - xmin) // PIXEL_TO_TWIP
    old_h = (ymax - ymin) // PIXEL_TO_TWIP
    old_framecount = struct.unpack("<H", rest[2:4])[0]

    if width is not None:
        xmax = xmin + width * PIXEL_TO_TWIP
    if height is not None:
        ymax = ymin + height * PIXEL_TO_TWIP

    new_rect = _write_rect(xmin, xmax, ymin, ymax)
    new_body = bytearray(new_rect + rest)
    if framecount is not None:
        new_body[len(new_rect) + 2:len(new_rect) + 4] = struct.pack("<H", framecount)
    new_len = 8 + len(new_body)

    with open(output_path, "wb") as f:
        f.write(sig)
        f.write(bytes([version]))
        f.write(struct.pack("<I", new_len))
        f.write(_compress_body(sig, bytes(new_body)))
