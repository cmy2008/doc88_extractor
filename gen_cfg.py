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
    def ph_nums(self)-> int:
        return len(self.headnums)

    def ph_num(self, page: int)-> int:
        pageid = self.pageids[page - 1].split("-")
        return int(pageid[0])

    def ph(self,level):
        return self.c_ph(self,level)
    
    def pk(self,page):
        return self.c_pk(self,page)
    class c_ph():
        def __init__(self, cfg, level: int) -> None:
            self.name="getebt-" + encode(f"{level}-0-{cfg.headnums[level-1]}-{cfg.p_swf}",key2) + ".ebt"
            self.url=f"{cfg.ebt_host}/{self.name}"

    class c_pk():
        def __init__(self, cfg, page: int) -> None:
            pageid = cfg.pageids[page - 1].split("-")
            level_num = int(pageid[0])
            self.name="getebt-" + encode(f"{level_num}-{pageid[3]}-{pageid[4]}-{cfg.p_swf}-{page}-{cfg.p_code}",key2) + ".ebt"
            self.url = f"{cfg.ebt_host}/{self.name}"

