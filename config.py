class config():
    def __init__(self) -> None:
        self.o_dir_path = "docs/" # Default: "docs/"
        self.o_swf_path = "swf/" # Default: "swf/"
        self.o_pdf_path = "pdf/" # Default: "pdf/"
        self.o_svg_path = "svg/" # Default: "svg/"
        self.dir_path = "" # Default: ""
        self.swf_path = "" # Default: ""
        self.pdf_path = "" # Default: ""
        self.svg_path = "" # Default: ""
        self.swf2pdf = True # Default: True, if False, then convert swf -> svg -> pdf
        self.svgfontface = True # Default: True (only worked when swf2pdf is False), if False, then convert the texts to shapes
        self.clean = True # Default: True, if False, the swf,svg,pdf files will be kept
cfg2=config()