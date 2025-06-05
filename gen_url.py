from coder import *

class gen_url:
    def __init__(self,config: dict) -> None:
        self.headerInfo=config['headerInfo']
        self.p_swf=config['p_swf']
        self.ebt_host=config['ebt_host']
        self.p_code=config['p_code']
        self.pageInfo=config['pageInfo']

    def pknum(self)-> int:
        headnums=self.headerInfo.replace('"',"").split(',')
        return len(headnums)
    
    def pk(self, page: int)-> str:
        headnums=self.headerInfo.replace('"',"").split(',')
        return self.ebt_host + "/getebt-" + encode(f"{page}-0-{headnums[page]}-{self.p_swf}",key2) + ".ebt"
        
    def ph(self,page: int)-> str:
        pageids = decode(self.pageInfo).split(",")
        pageid = pageids[page - 1].split("-")
        self.level_num = int(pageid[0])
        return self.ebt_host + "/getebt-" + encode(f"{self.level_num}-{pageid[3]}-{pageid[4]}-{self.p_swf}-{page}-{self.p_code}",key2) + ".ebt"