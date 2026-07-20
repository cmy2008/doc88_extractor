# -*- coding: utf-8 -*-
"""EBT 文件导入模块。

从本地 .ebt 文件目录或 xml 文件解析文档配置。
"""

import os
from xmltodict import parse
from coder import decode, encode, key2


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
        for file in os.listdir(path):
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

    pk_list.sort(key=lambda x: x["page"])
    ph_list.sort(key=lambda x: x["level"])

    cfg = {
        "headerInfo": ",".join(f'"{item["chunk_size"]}"' for item in ph_list),
        "p_swf": ph_list[0]["p_swf"],
        "ebt_host": ebt_host,
        "p_code": pk_list[0]["p_code"],
        "pageInfo": encode(
            ",".join(
                f"{item['level']}-"
                + f"{item['width'] + '-' + item['height'] if item['width'] is not None and item['height'] is not None else '612-858'}"
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
