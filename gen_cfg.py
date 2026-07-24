# -*- coding: utf-8 -*-
"""页面配置解析模块。

将 doc88 的原始配置字典解析为结构化的页面信息对象。
"""

from dataclasses import dataclass

from coder import decode, encode, key2


@dataclass
class PageURL:
    """页面文件的名称和下载 URL。"""
    name: str
    url: str


class GenConfig:
    """文档页面配置，封装所有页面元信息和 URL 生成逻辑。"""

    def __init__(self, config: dict) -> None:
        self.header_info: str = config["headerInfo"]
        self.p_swf: str = config["p_swf"]
        self.ebt_host: str = config["ebt_host"]
        self.p_code: str = config["p_code"]
        self.page_info: str = config["pageInfo"]
        self.p_name: str = config["p_name"]
        self.p_date: str = config["p_upload_date"]
        self.p_count_info: int = config["pageCount"]
        self.p_download: str = config["p_download"]
        self.p_doc_format: str = config["p_doc_format"]
        self.p_pagecount: str = config["p_pagecount"]

        self.pageids: list[str] = decode(self.page_info).split(",")
        self.pageids.sort(key=lambda pid: int(pid.split("-")[3]))
        self.p_count: int = len(self.pageids)
        self.headnums: list[str] = self.header_info.replace('"', "").split(",")

    def ph_nums(self) -> int:
        """返回 PH 文件总数。"""
        return len(self.headnums)

    def ph_num(self, page: int) -> int:
        """返回指定页面所引用的 PH 层级编号。"""
        pageid = self.pageids[page - 1].split("-")
        return int(pageid[0])

    def ph(self, level: int) -> PageURL:
        """生成指定层级的 PH 文件 URL。"""
        name = (
            "getebt-"
            + encode(
                f"{level}-0-{self.headnums[level - 1]}-{self.p_swf}", key2
            )
            + ".ebt"
        )
        return PageURL(name=name, url=f"{self.ebt_host}/{name}")

    def pk(self, page: int) -> PageURL:
        """生成指定页面的 PK 文件 URL。"""
        pageid = self.pageids[page - 1].split("-")
        level_num = int(pageid[0])
        name = (
            "getebt-"
            + encode(
                f"{level_num}-{pageid[3]}-{pageid[4]}-{self.p_swf}-{page}-{self.p_code}",
                key2,
            )
            + ".ebt"
        )
        return PageURL(name=name, url=f"{self.ebt_host}/{name}")
