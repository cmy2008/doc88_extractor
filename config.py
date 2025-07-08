import json,os

class Config:
    def __init__(self, config_path="config.json"):
        self.config_path=config_path
        if not os.path.exists(config_path):
            self.gen()
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        self.o_dir_path = config_data["o_dir_path"]
        self.o_swf_path = config_data["o_swf_path"]
        self.o_pdf_path = config_data["o_pdf_path"]
        self.o_svg_path = config_data["o_svg_path"]
        self.dir_path = ""
        self.swf_path = ""
        self.pdf_path = ""
        self.svg_path = ""
        self.swf2svg = config_data["swf2svg"]
        self.svgfontface = config_data["svgfontface"]
        self.clean = config_data["clean"]

    def gen(self):
        default_config = {
            "o_dir_path": "docs/",
            "o_swf_path": "swf/",
            "o_pdf_path": "pdf/",
            "o_svg_path": "svg/",
            "swf2svg": False,
            "svgfontface": False,
            "clean": True
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)

cfg2 = Config()