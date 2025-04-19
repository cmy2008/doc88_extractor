from coder import *

def gen_url(p_code: str,headerInfo: str,page: int,p_swf,pageInfo: str,ebt_host: str) -> list:
    p_code=int(p_code)
    headnums=headerInfo.replace('"',"").split(',')
    if len(headnums) == 1:
        single=True
        level = headnums[0]
    else:
        single=False
        level = headnums[int((page-1)/50)]
    pageids = decode(pageInfo).split(",")
    pageid = pageids[page - 1].split("-")
    if single:
        level_num = 1
    else:
        level_num = int((page-1)/50)+1
    PK = ebt_host + "/getebt-" + encode(f"{level_num}-0-{level}-{p_swf}",key2) + ".ebt"
    BK = ebt_host + "/getebt-" + encode(f"{level_num}-{pageid[3]}-{pageid[4]}-{p_swf}-{page}-{p_code}",key2) + ".ebt"
    return PK,BK