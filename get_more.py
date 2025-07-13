import requests
import os
from gen_cfg import *
from compressor import *
# from collections import Counter

# getebt-level_num-offset-filesize-p_swf-page-p_code
# ebt文件的编号，level_num为层数编号，offset为内容偏移量，filesize为获取的内容长度，文件排序如下：头文件1,页文件1...重置计数...头文件2,页文件51...
# get_more 尝试从隐藏文档中提取额外页

class get_more():
    def __init__(self,cfg: gen_cfg,file) -> None:
        self.cfg=cfg
        self.chunk_size=10240000
        self.header=bytearray()
        # self.heads=[]
        self.file=file
        self.newpageids=[]
        self.pagecount=0
        return None

    def start(self,level):
        ids=self.scan(level)
        return self.get_newpageids(level,ids)

    def scan(self,level,scan_range=0):
        ids=[]
        print(f"level {level} start scannig...")
        headsize=int(self.cfg.headnums[level-1])
        self.flags=[headsize]
        url=self.cfg.ebt_host + "/getebt-" + encode(f"{level}-{headsize}-{self.chunk_size}-{self.cfg.p_swf}-1-{self.cfg.p_code}",key2) + ".ebt"
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(self.file, 'wb') as file:
                size=0
                offset=0
                status=False
                setoffset=0
                try:
                    for chunk in response.iter_content(chunk_size=1):
                        if chunk:
                            if 32 <= size <= 33:
                                self.header.extend(chunk)
                            elif size > 33:
                                if chunk == struct.pack('B', self.header[0]):
                                    status=True
                                elif chunk == struct.pack('B', self.header[1]):
                                    if status==True:
                                        if size-33-offset < scan_range:
                                            print(f"pass:{size}-{size-33-offset}")
                                            status=False
                                            pass
                                        else:
                                            br=f"{headsize+offset}-{size-33-offset}"
                                            if self.test(headsize,br):
                                                # setoffset=1
                                                print(f"found:{br}")
                                                ids.append(br)
                                                offset=size-33
                                            else:
                                                print(f"zpass:{br}")
                                                status=False
                                                pass
                                    else:
                                        status=False
                                else:
                                    status=False
                                # if setoffset == 1:
                                #     setoffset=2
                                # elif setoffset==2:
                                #     setoffset=0
                                #     print(chunk.hex())
                                #     self.heads.append(chunk.hex())
                            size+=file.write(chunk)
                            file.flush()
                except requests.exceptions.ChunkedEncodingError:
                    pass
                ids.append(f"{headsize+offset}-{size-offset}")
                print(f"finish:{headsize+offset}-{size-offset}")
                print(f"total page:{len(ids)}")
                # count_dict = Counter(self.heads)
                # print(count_dict)
                return ids
    
    def test(self,headsize,byte_range: str):
        comp=Compressor()
        data=comp.load(self.file)
        ranges=byte_range.split('-')
        pk=data[int(ranges[0])-headsize:int(ranges[0])-headsize+int(ranges[1])]
        if comp.decompressEBT_PK(pk):
            return True
        else:
            return False
    
    def get_newpageids(self,level,ids):
        #2-595-841-519036-3157
        pid=f"{level}-{self.cfg.pageids[0].split('-')[1]}-{self.cfg.pageids[0].split('-')[2]}"
        for i in range(0,len(ids)):
            self.newpageids.append(f"{pid}-{ids[i]}")
        return self.newpageids