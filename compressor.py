import struct
import zlib
from utils import *


class Compressor:
    def __init__(self):
        return None

    def processSWF(self, file_EBT, file_EBT_PK, path):
        ph = self.decompressEBT_PH(load_file(file_EBT))
        pk = self.decompressEBT_PK(load_file(file_EBT_PK))
        swf = self.makeup(ph, pk)
        write_file(swf, path)

    def makeup(self, ebt_ph, ebt_pk):
        buff = bytearray()
        buff.extend(ebt_ph)
        buff.extend(ebt_pk)
        buff.extend(struct.pack("<BBBB", 64, 0, 0, 0))
        buff[4:8] = struct.pack("<I", len(buff))
        return buff

    def decompressEBT_PH(self, data):
        buff = bytearray()
        try:
            buff.extend(zlib.decompress(data[40:]))
            buff[4:8] = struct.pack("<I", len(buff))
        except zlib.error:
            return False
        return buff

    def decompressEBT_PK(self, data):
        try:
            return zlib.decompress(data[32:])
        except zlib.error:
            return False


def make_swf(file_EBT, file_EBT_PK, path):
    compressor = Compressor()
    compressor.processSWF(file_EBT, file_EBT_PK, path)
