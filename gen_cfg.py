from coder import *
class gen_cfg:
    def __init__(self,config: dict) -> None:
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
        self.p_pagecount=config['p_pagecount']
        self.pageids=decode(self.pageInfo).split(",")
        self.p_count=len(self.pageids)
        self.headnums=self.headerInfo.replace('"',"").split(',')

    def phnum(self)-> int:
        return len(self.headnums)
    
    def ph(self, level: int)-> str:
        return self.ebt_host + "/getebt-" + encode(f"{level}-0-{self.headnums[level-1]}-{self.p_swf}",key2) + ".ebt"
    
    def ph_num(self, page: int)-> int:
        pageid = self.pageids[page - 1].split("-")
        return int(pageid[0])
    
    def pk(self,page: int)-> str:
        pageid = self.pageids[page - 1].split("-")
        self.level_num = int(pageid[0])
        return self.ebt_host + "/getebt-" + encode(f"{self.level_num}-{pageid[3]}-{pageid[4]}-{self.p_swf}-{page}-{self.p_code}",key2) + ".ebt"

