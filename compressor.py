# -*- coding: utf-8 -*-
"""SWF 压缩/解压模块。

负责将 doc88 的 .ebt (PH/PK) 文件合并解码为 SWF 文件。
"""

import struct
import zlib

from utils import load_file, write_file


class Compressor:
    """SWF 文件处理器：解压 EBT PH/PK 并合成为 SWF。"""

    def process_swf(self, file_ebt: str, file_ebt_pk: str, path: str) -> None:
        """读取 PH 和 PK 文件，合成 SWF 并写入 path。"""
        ph = self._decompress_ebt_ph(load_file(file_ebt))
        pk = self._decompress_ebt_pk(load_file(file_ebt_pk))
        swf = self._makeup(ph, pk)
        # 释放中间缓冲区，减少内存峰值
        del ph, pk
        write_file(swf, path)
        del swf

    @staticmethod
    def _makeup(ebt_ph: bytearray, ebt_pk: bytearray) -> bytearray:
        """合并 PH 和 PK 数据，写入文件长度头。"""
        buff = bytearray()
        buff.extend(ebt_ph)
        buff.extend(ebt_pk)
        buff.extend(struct.pack("<BBBB", 64, 0, 0, 0))
        buff[4:8] = struct.pack("<I", len(buff))
        return buff

    @staticmethod
    def _decompress_ebt_ph(data: bytes) -> bytearray:
        """解压 EBT PH 文件数据（跳过 40 字节头）。"""
        buff = bytearray()
        try:
            buff.extend(zlib.decompress(data[40:]))
            buff[4:8] = struct.pack("<I", len(buff))
        except zlib.error:
            return bytearray()
        return buff

    @staticmethod
    def _decompress_ebt_pk(data: bytes) -> bytes:
        """解压 EBT PK 文件数据（跳过 32 字节头）。"""
        try:
            return zlib.decompress(data[32:])
        except zlib.error:
            return b""


def make_swf(file_ebt: str, file_ebt_pk: str, path: str) -> None:
    """便捷函数：从 PH/PK 文件合成 SWF。"""
    Compressor().process_swf(file_ebt, file_ebt_pk, path)
