import struct
import zlib

class Compressor:
    MAGIC_ZWS = b"ZWS"
    MAGIC_CWS = b"CWS"
    MAGIC_FWS = b"FWS"
    MAGIC_EBT = b"YBD"
    MAGIC_EBK = b"EBT_PK"

    def __init__(self):
        self.ref = None
        self.buffer = None
        self.glue = b""
        self.dos = b"Nothing"
        self.MAKEUP = True

    def load(self, file):
        with open(file, 'rb') as f:
            self.ref = f.read()
        return self.ref

    def processSWF(self,file_EBT,file_EBK,path):
        swf = None
        swf = self.decompressEBT_PH(self.load(file_EBT))
        swf = self.decompressEBT_PK(self.load(file_EBK))
        is_ebt = self.glue == self.MAGIC_EBT
        swf = self.makeup(self.buffer if is_ebt else swf, swf if is_ebt else self.buffer)
        self.glue = None
        with open(path, 'wb') as f:
            f.write(swf)

    def makeup(self, ebt_ph, ebt_pk):
        buff = bytearray()
        buff.extend(ebt_ph)
        buff.extend(ebt_pk)
        buff.extend(struct.pack('<BBBB', 64, 0, 0, 0))
        buff[4:8] = struct.pack('<I', len(buff))
        return buff

    def decompressEBT_PH(self, data):
        data = data[40:]
        buff = bytearray()
        ebt = bytearray(data)

        try:
            decompressed = zlib.decompress(ebt)
            buff.extend(decompressed)
            buff[4:8] = struct.pack('<I', len(buff))
        except zlib.error:
            return None

        if not self.buffer:
            self.buffer = buff
            self.glue = self.MAGIC_EBT

        return buff

    def decompressEBT_PK(self, data):
        data = data[32:]
        ebt = bytearray()
        buff = bytearray(data)

        try:
            decompressed = zlib.decompress(buff)
            ebt.extend(decompressed)
        except zlib.error:
            return None

        if not self.buffer:
            self.buffer = buff
            self.glue = self.MAGIC_EBK

        return ebt

    def compress(self, data):
        header = data[3:8]
        decompressed = data[8:]
        compressed = bytearray()

        compressed.extend(b"CWS")
        compressed.extend(header)
        compressed.extend(zlib.compress(decompressed))

        return compressed

    def decompress(self, data):
        header = data[3:8]
        compressed = data[8:]
        decompressed = bytearray()

        decompressed.extend(header)
        decompressed.extend(zlib.decompress(compressed))

        return decompressed

def make(file_EBT,file_EBK,path):
    compressor = Compressor()
    compressor.processSWF(file_EBT,file_EBK,path)
