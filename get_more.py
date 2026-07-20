# -*- coding: utf-8 -*-
"""文档额外页面扫描模块。

通过扫描 CDN 上的连续数据块，尝试获取预览中不可见的额外页面。
"""

import gc
import json
import struct
import requests
from coder import encode, key2
from compressor import Compressor
from gen_cfg import GenConfig
from utils import ospath, read_file, write_file, writes_file, get_request


class GetMore:
    """扫描并下载超出预览范围的隐藏页面。"""

    def __init__(
        self, cfg: GenConfig, level: int, filepath: str, page: int = 0
    ) -> None:
        self.cfg = cfg
        self.comp = Compressor()
        self.level = level
        self.chunk_size = 1024000
        self.header = bytearray()
        self.filepath = filepath
        self.newpageids: list[str] = []
        self.pagecount = page
        self.PH_data = requests.get(self.cfg.ph(self.level).url).content
        self.progressfile = filepath + "progress.json"
        self.progress: dict = {"pk": [], "ph": []}
        self.save_progress("ph", self.level)
        self.PK_data = bytearray()
        self.ids: list[str] = []

    def read_progress(self) -> None:
        """从磁盘读取下载进度。"""
        self.progress = json.loads(read_file(self.progressfile))

    def save_progress(self, progress_type: str, page: int) -> None:
        """保存下载进度到磁盘。"""
        self.progress[progress_type].append(page)
        writes_file(json.dumps(self.progress), self.progressfile)

    def start(self) -> list[str] | None:
        """开始扫描流程。"""
        write_file(self.PH_data, f"{self.filepath}{self.cfg.ph(self.level).name}")
        if self._scan(self.level):
            return self._get_newpageids()
        self.PK_data.clear()
        self.PH_data = b""
        return None

    def _scan(self, scan_range: int = 0) -> bool:
        """先将当前层数据全部下载到内存，再扫描页面边界。"""
        print(f"level {self.level} start scanning...")
        headsize = int(self.cfg.headnums[self.level - 1])
        self.flags = [headsize]

        # 分块下载：每次请求 chunk_size 字节，服务器在数据超限时断开并抛出 ChunkedEncodingError
        self.PK_data = bytearray()
        offset = headsize
        page_num = 0
        while True:
            page_num += 1
            url = (
                self.cfg.ebt_host
                + "/getebt-"
                + encode(
                    f"{self.level}-{offset}-{self.chunk_size}-{self.cfg.p_swf}-{page_num}-{self.cfg.p_code}",
                    key2,
                )
                + ".ebt"
            )
            try:
                response = get_request(url, cffi=False, content_type="", stream=True)
            except Exception:
                break
            if response.status_code != 200:
                break
            buf = bytearray()
            chunked_error = False
            try:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        buf.extend(chunk)
            except requests.exceptions.ChunkedEncodingError:
                chunked_error = True
                # 尾部逐字节补全（可能无数据）
                try:
                    while True:
                        b = response.raw.read(1)
                        if not b:
                            break
                        buf.extend(b)
                except Exception:
                    pass
            if not buf:
                break
            self.PK_data.extend(buf)
            # 未触发截断且数据量不足 chunk_size → 文件末尾
            if not chunked_error and len(buf) < self.chunk_size:
                break
            offset += self.chunk_size

        if len(self.PK_data) == 0:
            return False

        # 在内存中扫描页面边界
        self.header = bytearray()
        pos = 0
        page_start = 0
        status = False
        while pos < len(self.PK_data):
            b = self.PK_data[pos]
            if 32 <= pos <= 33:
                self.header.append(b)
            elif pos > 33:
                if b == self.header[0]:
                    status = True
                elif b == self.header[1]:
                    if status:
                        page_size = pos - 33 - page_start
                        if page_size < scan_range:
                            print(f"pass:{pos}-{page_size}")
                            status = False
                        else:
                            br = f"{headsize + page_start}-{page_size}"
                            page_data = self.PK_data[page_start:pos + 1]
                            if self._test_bytearray(page_data):
                                write_file(
                                    page_data,
                                    f"{self.filepath}getebt-"
                                    f"{encode(f'{self.level}-{headsize + page_start}-{page_size}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
                                )
                                self.save_progress(
                                    "pk",
                                    self.pagecount + len(self.ids) + 1,
                                )
                                print(f"found:{br}")
                                self.ids.append(br)
                                page_start = pos - 33
                            else:
                                print(f"zpass:{br}")
                                status = False
                    else:
                        status = False
                else:
                    status = False
            pos += 1

        # 处理剩余数据
        remaining_data = self.PK_data[page_start:]
        if remaining_data and self._test_bytearray(remaining_data):
            br = f"{headsize + page_start}-{len(remaining_data)}"
            write_file(
                remaining_data,
                f"{self.filepath}getebt-"
                f"{encode(f'{self.level}-{headsize + page_start}-{len(remaining_data)}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
            )
            self.save_progress("pk", self.pagecount + len(self.ids) + 1)
            self.ids.append(br)
            print(f"finish:{br}")
        else:
            print("Error in the last page, maybe the header is changed?")

        print(f"total page:{len(self.ids)}")
        self.PK_data.clear()
        self.PH_data = b""
        gc.collect()
        return True


    def _test_bytearray(self, data: bytearray) -> bool:
        """验证指定的 PK 数据是否可成功解压为 SWF。"""
        pk = self.comp._decompress_ebt_pk(data)
        ph = self.comp._decompress_ebt_ph(self.PH_data)
        if pk:
            write_file(
                self.comp._makeup(ph, bytearray(pk)),
                f"{self.filepath}swf/{self.pagecount + len(self.ids) + 1}.swf",
            )
            return True
        return False

    def _get_newpageids(self) -> list[str]:
        """根据扫描到的 ID 生成新的 page ID 列表。"""
        pid = (
            f"{self.level}-"
            f"{self.cfg.pageids[0].split('-')[1]}-"
            f"{self.cfg.pageids[0].split('-')[2]}"
        )
        for i in range(len(self.ids)):
            self.newpageids.append(f"{pid}-{self.ids[i]}")
        self.ids.clear()
        return self.newpageids
