import requests
import os
import json
from gen_cfg import *
from compressor import *
from utils import *

# getebt-self.level_num-offset-filesize-p_swf-page-p_code
# ebt文件的编号，self.level_num为层数编号，offset为内容偏移量，filesize为获取的内容长度，文件排序如下：头文件1,页文件1...重置计数...头文件2,页文件51...
# get_more 尝试从隐藏文档中提取额外页


class get_more:
    def __init__(self, cfg: gen_cfg, level, filepath, page=0) -> None:
        self.cfg = cfg
        self.level = level
        self.chunk_size = 10240000
        self.header = bytearray()
        self.filepath = filepath
        self.newpageids = []
        self.pagecount = page
        self.PH_data = requests.get(self.cfg.ph(self.level).url).content
        self.progressfile = filepath + "progress.json"
        self.progress = {"pk": [], "ph": []}
        self.save_progress("ph", self.level)
        self.PK_data = bytearray()
        self.ids = []
        return None

    def read_progress(self):
        self.progress = json.loads(read_file(self.progressfile))

    def save_progress(self, type: str, page: int):
        self.progress[type].append(page)
        writes_file(json.dumps(self.progress), self.progressfile)

    def start(self):

        write_file(self.PH_data, f"{self.filepath}{self.cfg.ph(self.level).name}")
        if self.scan(self.level):
            return self.get_newpageids()

    def scan(self, scan_range=0):
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
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(ospath(f"{self.filepath}cache.ebt"), "wb") as file:
                size = 0
                offset = 0
                status = False
                try:
                    for chunk in response.iter_content(chunk_size=1):
                        if chunk:
                            self.PK_data.extend(chunk)
                            if 32 <= size <= 33:
                                self.header.extend(chunk)
                            elif size > 33:
                                if chunk == struct.pack("B", self.header[0]):
                                    status = True
                                elif chunk == struct.pack("B", self.header[1]):
                                    if status == True:
                                        if size - 33 - offset < scan_range:
                                            print(f"pass:{size}-{size-33-offset}")
                                            status = False
                                            pass
                                        else:
                                            br = f"{headsize+offset}-{size-33-offset}"
                                            if self.test():
                                                write_file(
                                                    self.PK_data,
                                                    f"{self.filepath}getebt-{encode(f'{self.level}-{headsize+offset}-{size-offset-33}-{self.cfg.p_swf}-{self.pagecount+len(self.ids)+1}-{self.cfg.p_code}',key2)}.ebt",
                                                )
                                                self.save_progress(
                                                    "pk",
                                                    self.pagecount + len(self.ids) + 1,
                                                )
                                                self.PK_data = self.PK_data[
                                                    size - 33 - offset :
                                                ]
                                                print(f"found:{br}")
                                                self.ids.append(br)
                                                offset = size - 33
                                            else:
                                                print(f"zpass:{br}")
                                                status = False
                                                pass
                                    else:
                                        status = False
                                else:
                                    status = False
                            size += file.write(chunk)
                except requests.exceptions.ChunkedEncodingError:
                    pass
                if self.test():
                    write_file(
                        self.PK_data,
                        f"{self.filepath}getebt-{encode(f'{self.level}-{headsize+offset}-{size-offset}-{self.cfg.p_swf}-{self.pagecount+len(self.ids)+1}-{self.cfg.p_code}',key2)}.ebt",
                    )
                    self.save_progress("pk", self.pagecount + len(self.ids) + 1)
                    self.ids.append(f"{headsize+offset}-{size-offset}")
                    print(f"finish:{headsize+offset}-{size-offset}")
                else:
                    print("Except ending, is the file too big?")
                print(f"total page:{len(self.ids)}")
                return True

    def test(self):
        comp = Compressor()
        pk = comp.decompressEBT_PK(self.PK_data)
        ph = comp.decompressEBT_PH(self.PH_data)
        if pk:
            write_file(
                comp.makeup(ph, pk),
                f"{self.filepath}swf/{self.pagecount+len(self.ids)+1}.swf",
            )
            return True
        else:
            return False

    def get_newpageids(self):
        pid = f"{self.level}-{self.cfg.pageids[0].split('-')[1]}-{self.cfg.pageids[0].split('-')[2]}"
        for i in range(0, len(self.ids)):
            self.newpageids.append(f"{pid}-{self.ids[i]}")
        self.ids.clear()
        return self.newpageids
