import struct
import zlib

class Compressor:
    def __init__(self):
        return None

    def load(self, file):
        with open(file, 'rb') as f:
            return f.read()

    def processSWF(self,file_EBT,file_EBK,path):
        ph = self.decompressEBT_PH(self.load(file_EBT))
        pk = self.decompressEBT_PK(self.load(file_EBK))
        swf = self.makeup(ph,pk)
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
        buff = bytearray()
        try:
            buff.extend(zlib.decompress(data[40:]))
            buff[4:8] = struct.pack('<I', len(buff))
        except zlib.error:
            return None
        return buff

    def decompressEBT_PK(self, data):
        try:
            return zlib.decompress(data[32:])
        except zlib.error:
            return None

def make(file_EBT,file_EBK,path):
    compressor = Compressor()
    compressor.processSWF(file_EBT,file_EBK,path)
