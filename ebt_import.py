# -*- coding: utf-8 -*-
"""EBT 文件导入模块。

从本地 .ebt 文件目录或 xml 文件解析文档配置。
"""

import json
import os
from xmltodict import parse
from coder import decode, encode, key2
from gen_cfg import GenConfig, ph_cache_name, pk_cache_name


def import_ebt(path: str) -> tuple[list[dict], list[dict]]:
    """扫描目录中的 .ebt 文件，分离为 PH 列表和 PK 列表。

    Args:
        path: 包含 .ebt 文件的目录路径。

    Returns:
        (ph_list, pk_list) 元组，每个元素为字典列表。

    Raises:
        Exception: 路径无效时抛出。
    """
    if not os.path.exists(path):
        raise Exception("无效路径")

    ph_list: list[dict] = []
    pk_list: list[dict] = []

    if os.path.isdir(path):
        files = os.listdir(path)
        # 短命名缓存（ph1.ebt / pk1.ebt ...）不含元数据，需从 index.json 还原
        short_names = [
            f for f in files
            if f.endswith(".ebt") and f[:-4][:2] in ("ph", "pk")
            and f[:-4][2:].isdigit()
        ]
        if short_names:
            index_path = os.path.join(path, "index.json")
            if not os.path.isfile(index_path):
                raise Exception("短命名缓存缺少 index.json，无法还原配置")
            with open(index_path, encoding="utf-8") as f:
                config = json.load(f)
            ph_list, pk_list = _ebts_from_config(config)
            ph_list = [p for p in ph_list if ph_cache_name(p["level"]) in files]
            pk_list = [p for p in pk_list if pk_cache_name(p["page"]) in files]
            return ph_list, pk_list

        for file in files:
            if not file.endswith(".ebt"):
                continue
            decode_name = decode(file[:-4][7:], key2)
            split_name = decode_name.split("-")
            file_path = os.path.join(path, file)

            if len(split_name) == 6:
                ph_list.append(
                    {
                        "level": int(split_name[0]),
                        "headsize": int(split_name[1]),
                        "chunk_size": int(split_name[2]),
                        "p_swf": "-".join(split_name[3:]),
                        "path": file_path,
                    }
                )
            elif len(split_name) == 8:
                pk_list.append(
                    {
                        "level": int(split_name[0]),
                        "headsize": int(split_name[1]),
                        "chunk_size": int(split_name[2]),
                        "p_swf": "-".join(split_name[3:][:-2]),
                        "page": int(split_name[6]),
                        "p_code": split_name[7],
                        "path": file_path,
                    }
                )

    return ph_list, pk_list


def _ebts_from_config(config: dict) -> tuple[list[dict], list[dict]]:
    """从文档配置还原 PH/PK 信息列表，供短命名缓存导入使用。"""
    cfg = GenConfig(config)
    ph_list = [
        {
            "level": level,
            "chunk_size": cfg.headnums[level - 1],
            "p_swf": cfg.p_swf,
        }
        for level in range(1, cfg.ph_nums() + 1)
    ]
    pk_list = []
    for page, pageid in enumerate(cfg.pageids, 1):
        parts = pageid.split("-")
        pk_list.append(
            {
                "level": int(parts[0]),
                "width": parts[1],
                "height": parts[2],
                "headsize": parts[3],
                "chunk_size": parts[4],
                "p_swf": cfg.p_swf,
                "page": page,
                "p_code": cfg.p_code,
            }
        )
    return ph_list, pk_list


def import_xml(xml: str):
    xml_cfg = parse(xml)["doc"]
    if xml_cfg["p_404"] == "1":
        raise Exception("404 Not Found!")
    ph_list: list[dict] = []
    pk_list: list[dict] = []
    p_code = xml_cfg["p_code"]
    p_name = xml_cfg["p_name"]
    ebt_host = xml_cfg["p_ebthost"]
    p_swf = xml_cfg["p_swf"]
    p_struct = xml_cfg["p_struct"]
    for h in p_struct["h"] if type(p_struct["h"]) is list else [p_struct["h"]]:
        ph_list.append(
            {
                "level": h["@n"],
                "chunk_size": h["#text"],
                "p_swf": p_swf,
            }
        )
    for p in p_struct["p"]:
        pk_list.append(
            {
                "level": p["e"],
                "width": p["w"],
                "height": p["h"],
                "headsize": p["p"],
                "chunk_size": p["l"],
                "p_swf": p_swf,
                "page": p["@n"],
                "p_code": p_code,
            }
        )
    return ph_list, pk_list, p_name, ebt_host

# TODO: 直接构造 GenConfig
def build_cfg(
    ph_list: list[dict],
    pk_list: list[dict],
    doc_name: str = "",
    ebt_host: str = "https://cdn2.doc88.com"
) -> dict:
    """根据 PH/PK 列表构建文档配置字典。

    Args:
        ph_list: PH 文件信息列表。
        pk_list: PK 文件信息列表。

    Returns:
        符合 main.py 要求的配置字典。

    Raises:
        Exception: PH 列表为空时抛出。
    """
    if not ph_list:
        raise Exception("缺少ph文件")

    pk_list.sort(key=lambda x: int(x["page"]))
    ph_list.sort(key=lambda x: int(x["level"]))

    def page_size(item: dict) -> str:
        width, height = item.get("width"), item.get("height")
        return f"{width}-{height}" if width and height else "612-858"

    cfg = {
        "headerInfo": ",".join(f'"{item["chunk_size"]}"' for item in ph_list),
        "p_swf": ph_list[0]["p_swf"],
        "ebt_host": ebt_host,
        "p_code": pk_list[0]["p_code"],
        "pageInfo": encode(
            ",".join(
                f"{item['level']}-{page_size(item)}"
                + f"-{item['headsize']}-{item['chunk_size']}"
                for item in pk_list
            )
        ),
        "p_name": f"Unknown Document {pk_list[0]['p_code']}"
        if not doc_name
        else doc_name,
        "p_upload_date": pk_list[0]["p_swf"].split("-")[1],
        "pageCount": len(pk_list),
        "p_download": "0",
        "p_doc_format": "pdf",
        "p_pagecount": str(len(pk_list)),
    }
    return cfg
