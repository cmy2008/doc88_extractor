import os
from coder import *

def import_ebt(path: str):
    if not os.path.exists(path):
        raise Exception("无效路径")
    ph_list = []
    pk_list = []
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            if file.endswith(".ebt"):
                decode_name=decode(file[:-4][7:], key2)
                split_name=decode_name.split("-")
                if len(split_name) == 6:
                    ph_list.append({
                        "level": int(split_name[0]),
                        "headsize": int(split_name[1]),
                        "chunk_size": int(split_name[2]),
                        "p_swf": "-".join(split_name[3:]),
                        "path": os.path.join(path, file)
                    })
                elif len(split_name) == 8:
                    pk_list.append({
                        "level": int(split_name[0]),
                        "headsize": int(split_name[1]),
                        "chunk_size": int(split_name[2]),
                        "p_swf": "-".join(split_name[3:][:-2]),
                        "page": int(split_name[6]),
                        "p_code": split_name[7],
                        "path": os.path.join(path, file)
                    })
    return ph_list, pk_list

def build_cfg(ph_list, pk_list):
    # TODO: 检测混合文档的文件情况
    if not ph_list:
        raise Exception("缺少ph文件")
    pk_list.sort(key=lambda x: x["page"])
    ph_list.sort(key=lambda x: x["level"])
    cfg = {
        "headerInfo": ",".join(f"\"{item['chunk_size']}\"" for item in ph_list),
        "p_swf": ph_list[0]["p_swf"],
        "ebt_host": "https://cdn2.doc88.com",
        "p_code": pk_list[0]["p_code"],
        "pageInfo": encode(",".join(f"{item['level']}-595-841-{item['headsize']}-{item['chunk_size']}" for item in pk_list)),
        "p_name": f"Unknown Document {pk_list[0]['p_code']}",
        "p_upload_date": pk_list[0]["p_swf"].split("-")[1],
        "pageCount": len(pk_list),
        "p_download": "0",
        "p_doc_format": "pdf",
        "p_pagecount": str(len(pk_list))
    }
    return cfg