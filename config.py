# -*- coding: utf-8 -*-
"""配置管理模块。

提供 Config 类用于读写 config.json，以及全局默认配置实例 cfg2。
"""

import json
import os
from typing import Any


class Config:
    """应用程序配置管理。

    自动从 config.json 加载配置，若文件不存在则使用默认值生成。
    """

    def __init__(self, config_path: str = "config.json") -> None:
        self.default_config: dict[str, Any] = {
            "version": "2.3",
            "ffdec_version": "version26.2.1",
            "o_dir_path": "docs/",
            "o_swf_path": "swf/",
            "o_pdf_path": "pdf/",
            "o_svg_path": "svg/",
            "proxy_url": "",
            "ffdec_repo": "jindrapetrik/jpexs-decompiler",
            "svg2pdf_repo": "cmy2008/svg2pdf",
            "presse_repo" : "cmy2008/presse",
            "check_update": True,
            "swf2svg": False,
            "svgfontface": False,
            "clean": True,
            "get_more": False,
            "path_replace": True,
            "download_workers": 10,
            "convert_workers": 5,
            "pdf_scale": 1.0,
        }
        self.config_path = config_path
        # 运行时路径（非持久化）
        self.dir_path = ""
        self.swf_path = ""
        self.pdf_path = ""
        self.svg_path = ""

        if not os.path.exists(config_path):
            self._gen_default()
        self.load()

    def load(self) -> None:
        """从 JSON 文件加载配置，缺失项回退到默认值。"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data: dict = json.load(f)

        # 用默认值补全缺失的键
        for key, default_val in self.default_config.items():
            setattr(self, key, config_data.get(key, default_val))

    def _gen_default(self) -> None:
        """生成默认配置文件。"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.default_config, f, indent=4)

    def reload(self) -> None:
        """重新加载配置文件。"""
        self.load()

    def save(self) -> None:
        """将当前配置保存到 JSON 文件。"""
        config_data = {key: getattr(self, key) for key in self.default_config}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)


# 全局默认配置实例
cfg2 = Config()
