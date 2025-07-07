from coder import *

class gen_cfg:
    def __init__(self,config: dict,more: bool = False) -> None:
        self.headerInfo=config['headerInfo']
        self.p_swf=config['p_swf']
        self.ebt_host=config['ebt_host']
        self.p_code=config['p_code']
        self.pageInfo=config['pageInfo']
        self.p_name=config["p_name"]
        self.p_date=config["p_upload_date"]
        self.p_countinfo=config['pageCount']
        self.p_download=config['p_download']
        self.p_doc_format=config['p_doc_format']
        self.pageids=decode(self.pageInfo).split(",")
        self.p_count=len(self.pageids)
        self.page_levels = {}
        for idx, pageid in enumerate(self.pageids):
            parts = pageid.split('-')
            self.page_levels[idx+1] = int(parts[0])
        
        if more:
            self.get_more()

    def pknum(self)-> int:
        headnums=self.headerInfo.replace('"',"").split(',')
        return len(headnums)
    
    def pk(self, page: int)-> str:
        headnums=self.headerInfo.replace('"',"").split(',')
        return self.ebt_host + "/getebt-" + encode(f"{page}-0-{headnums[page-1]}-{self.p_swf}",key2) + ".ebt"
        
    def ph(self,page: int)-> str:
        pageid = self.pageids[page - 1].split("-")
        level_num = self.page_levels[page]
        return self.ebt_host + "/getebt-" + encode(
            f"{level_num}-{pageid[3]}-{pageid[4]}-{self.p_swf}-{page}-{self.p_code}", key2
        ) + ".ebt"
    
    def get_more(self)-> None:
        ids=self.pageids
        next=int(ids[0].split("-")[3])
        more=[]
        for i in ids + [ids[self.p_count-1]]:
            pageid=i.split("-")
            if next == int(pageid[3]):
                pre=pageid
                next = next + int(pageid[4])
            else:
                self.p_count=self.p_count+1
                pageid[3]=str(next)
                more.append('-'.join(pre))
                pre=pageid
                next=int(pageid[3])+int(pageid[4])
        self.pageids=self.pageids+more
