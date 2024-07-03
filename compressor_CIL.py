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

    def open(self):
        file_path = input("Please enter the path to the SWF or EBT file: ")
        self.load(file_path)

    def load(self, file_path):
        with open(file_path, 'rb') as f:
            self.ref = f.read()
        self.processSWF()

    def processSWF(self):
        self.dos = self.ref[:3]
        swf = None

        if self.dos == self.MAGIC_CWS:
            print("1")
            swf = self.decompress(self.ref)
        elif self.dos == self.MAGIC_ZWS:
            print("2")
            print("ZWS detected, do nothing. SWF 13 and later use LZMA.")
        elif self.dos == self.MAGIC_FWS:
            print("3")
            swf = self.compress(self.ref)
        elif self.dos == self.MAGIC_EBT:
            print("4")
            swf = self.decompressEBT_PH(self.ref)
        else:
            print("5")
            self.dos = self.MAGIC_EBK
            swf = self.decompressEBT_PK(self.ref)

        if swf and self.glue and self.MAKEUP:
            print("6")
            print("Need the 2nd part of EBT to makeup a page.")
            self.MAKEUP = False
            self.open()
            return  # Return here to wait for the second part of EBT
        elif swf and self.glue and self.dos != self.glue:
            print("7")
            is_ebt = self.glue == self.MAGIC_EBT
            swf = self.makeup(self.buffer if is_ebt else swf, swf if is_ebt else self.buffer)
            self.glue = None

        if (swf and not self.glue) or self.dos == self.glue:
            print("8")
            print(f"{self.dos.decode('us-ascii')} Detected.")
            with open('output.swf', 'wb') as f:
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
            ebt.extend(self.MAGIC_FWS)
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

        decompressed.extend(b"FWS")
        decompressed.extend(header)
        decompressed.extend(zlib.decompress(compressed))

        return decompressed

if __name__ == "__main__":
    compressor = Compressor()
    compressor.open()
