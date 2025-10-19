import os
import json

class Config:
    def __init__(self, config_path="config.json"):
        self.default_config ={
            "version": "1.8",
            "ffdec_version": "version24.1.0",
            "o_dir_path": "docs/",
            "o_swf_path": "swf/",
            "o_pdf_path": "pdf/",
            "o_svg_path": "svg/",
            "proxy_url": "https://ghproxy.cn/",
            "check_update": True,
            "swf2svg": False,
            "svgfontface": False,
            "clean": True,
            "get_more": False,
            "path_replace": True,
            "download_workers": 10,
            "convert_workers": 5
        }
        self.config_path=config_path
        if not os.path.exists(config_path):
            self.gen()
        self.load()

    def load(self):
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)
        keys = self.default_config.keys()
        self.version = config_data["version"] if "version" in config_data else "1.6"
        self.ffdec_version = config_data["ffdec_version"] if "ffdec_version" in config_data else "UNKONWN"
        for key in keys:
            if key not in config_data:
                config_data[key] = self.default_config[key]
        self.o_dir_path = config_data["o_dir_path"]
        self.o_swf_path = config_data["o_swf_path"]
        self.o_pdf_path = config_data["o_pdf_path"]
        self.o_svg_path = config_data["o_svg_path"]
        self.dir_path = ""
        self.swf_path = ""
        self.pdf_path = ""
        self.svg_path = ""
        self.proxy_url = config_data["proxy_url"]
        self.check_update = config_data["check_update"]
        self.swf2svg = config_data["swf2svg"]
        self.svgfontface = config_data["svgfontface"]
        self.clean = config_data["clean"]
        self.get_more = config_data["get_more"]
        self.path_replace = config_data["path_replace"]
        self.download_workers = config_data["download_workers"]
        self.convert_workers = config_data["convert_workers"]

    def gen(self):        
        with open(self.config_path, 'w') as f:
            json.dump(self.default_config, f, indent=4)

    def reload(self):
        self.load()
    
    def save(self):
        config_data = {
            "version": self.version,
            "ffdec_version": self.ffdec_version,
            "o_dir_path": self.o_dir_path,
            "o_swf_path": self.o_swf_path,
            "o_pdf_path": self.o_pdf_path,
            "o_svg_path": self.o_svg_path,
            "proxy_url": self.proxy_url,
            "check_update": self.check_update,
            "swf2svg": self.swf2svg,
            "svgfontface": self.svgfontface,
            "clean": self.clean,
            "get_more": self.get_more,
            "path_replace": self.path_replace,
            "download_workers": self.download_workers,
            "convert_workers": self.convert_workers
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

cfg2 = Config()