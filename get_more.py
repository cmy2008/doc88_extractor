# -*- coding: utf-8 -*-
"""文档额外页面扫描模块。

通过扫描 CDN 上的连续数据块，尝试获取预览中不可见的额外页面。
"""

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
        self.chunk_size = 10240000
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
        return None

    def _scan(self, scan_range: int = 0) -> bool:
        """对指定层级进行字节级扫描，寻找隐藏页面。"""
        print(f"level {self.level} start scannig...")
        headsize = int(self.cfg.headnums[self.level - 1])
        self.flags = [headsize]
        url = (
            self.cfg.ebt_host
            + "/getebt-"
            + encode(
                f"{self.level}-{headsize}-{self.chunk_size}-{self.cfg.p_swf}-1-{self.cfg.p_code}",
                key2,
            )
            + ".ebt"
        )
        response = get_request(url, cffi=False, content_type="", stream=True)
        if response.status_code != 200:
            return False

        with open(ospath(f"{self.filepath}cache.ebt"), "wb") as file:
            size = 0
            offset = 0
            status = False
            try:
                for chunk in response.iter_content(chunk_size=1):
                    if not chunk:
                        continue
                    self.PK_data.extend(chunk)
                    if 32 <= size <= 33:
                        self.header.extend(chunk)
                    elif size > 33:
                        if chunk == struct.pack("B", self.header[0]):
                            status = True
                        elif chunk == struct.pack("B", self.header[1]):
                            if status:
                                if size - 33 - offset < scan_range:
                                    print(f"pass:{size}-{size - 33 - offset}")
                                    status = False
                                else:
                                    br = f"{headsize + offset}-{size - 33 - offset}"
                                    if self._test():
                                        write_file(
                                            self.PK_data,
                                            f"{self.filepath}getebt-"
                                            f"{encode(f'{self.level}-{headsize + offset}-{size - offset - 33}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
                                        )
                                        self.save_progress(
                                            "pk",
                                            self.pagecount + len(self.ids) + 1,
                                        )
                                        self.PK_data = self.PK_data[
                                            size - 33 - offset:
                                        ]
                                        print(f"found:{br}")
                                        self.ids.append(br)
                                        offset = size - 33
                                    else:
                                        print(f"zpass:{br}")
                                        status = False
                            else:
                                status = False
                        else:
                            status = False
                    size += file.write(chunk)
            except requests.exceptions.ChunkedEncodingError:
                pass

            if self._test():
                write_file(
                    self.PK_data,
                    f"{self.filepath}getebt-"
                    f"{encode(f'{self.level}-{headsize + offset}-{size - offset}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
                )
                self.save_progress("pk", self.pagecount + len(self.ids) + 1)
                self.ids.append(f"{headsize + offset}-{size - offset}")
                print(f"finish:{headsize + offset}-{size - offset}")
            else:
                print("Unexpected ending, is the file too big?")
            print(f"total page:{len(self.ids)}")
            return True

    def _test(self) -> bool:
        """验证当前 PK 数据是否可成功解压为 SWF。"""
        pk = self.comp._decompress_ebt_pk(bytes(self.PK_data))
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
