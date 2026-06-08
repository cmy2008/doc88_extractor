# -*- coding: utf-8 -*-

import os
import sys

# 设置程序目录
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)
from config import *

print(f"DOC88 （预览）文档提取工具 V{cfg2.default_config['version']}")
print("by: Cuite_Piglin")
print(
    "\n免责声明： 仅供学习或交流用，请在 24 小时内删除本程序，严禁用于任何商业或非法用途，使用该工具而产生的任何法律后果，用户需自行承担全部责任\n"
)
# 弃用 cairosvg
'''
    if os.name == "nt":
        print(
            "警告：你正在使用 Windows 系统并使用 SVG 转换功能，虽然我们有意使其在多平台下工作，但需要使用 Cairo 库才能进行 SVG 的转换，建议你安装 GTK 运行库（需要 200MB 左右的安装空间）：\nhttps://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases\n如果安装后仍然无效，请尝试将安装目录下的 bin 目录添加到系统环境的 PATH 中然后重启终端或 Vscode\n"
        )
        list = os.environ["Path"].split(";")
        import re

        pattern = re.compile(r"GTK.?-Runtime")
        matches = [item for item in list if pattern.search(item)]
        if matches:
            try:
                os.add_dll_directory(matches[0])
            except:
                print("Error when setting environment.")
        else:
            print("GTK runtime not found, maybe not install?")
    import cairosvg
'''
import json
import re
import shutil
import subprocess
from compressor import *
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfWriter
from gen_cfg import *
from get_more import *
from utils import *
from updater import *
from ebt_import import *

    
def decode_data(encode_data) -> dict:
    try:
        return json.loads(decode(encode_data))
    except json.decoder.JSONDecodeError:
        raise Exception("Can't read data!")
    except (ValueError, UnicodeDecodeError):
        raise Exception("Can't read data! Maybe keys were changed?")

def get_main_from_url(url):
    if url.find("doc88.com/p-") == -1 and url.find("doc88.piglin.eu.org/p-") == -1:
        raise Exception("Invalid URL!")
    request = get_request(url, referer=True, cffi=True)
    if request.status_code == 404:
        raise Exception("404 Not found!")
    content = request.text
    data = re.search(r"m_main.init\(\".*\"\);", content)
    if data == None:
        if re.search("网络环境安全验证", content):
            print("WAF detected!")
            if choose("Do you want to use CDN?(Y/n): "):
                url = url.replace("www.doc88.com", "doc88.piglin.eu.org")
                return get_main_from_url(url)
            else:
                return False
        else:
            raise Exception("Can't find data in this page! Please try another.")
    c = data.span()
    encode_data = content[c[0] + 13 : c[1] - 3]
    return decode_data(encode_data)

def append_pdf(pdf: PdfWriter, file: str):
    pdf.append(ospath(file))
    return pdf



def init(config: dict) -> None:
    cfg2.dir_path = cfg2.o_dir_path + config["p_code"] + "/"
    cfg2.swf_path = cfg2.dir_path + cfg2.o_swf_path
    cfg2.svg_path = cfg2.dir_path + cfg2.o_svg_path
    cfg2.pdf_path = cfg2.dir_path + cfg2.o_pdf_path
    try:
        os.makedirs(ospath(cfg2.dir_path))
    except FileExistsError:
        if choose("exists"):
            pass
        else:
            raise Exception("Canceled.")
    if not os.path.exists(ospath(f"{cfg2.dir_path}index.json")):
        write_file(
            bytes(json.dumps(config), encoding="utf-8"),
            cfg2.dir_path + "index.json",
        )
    try:
        os.makedirs(ospath(cfg2.swf_path))
        os.makedirs(ospath(cfg2.svg_path))
        os.makedirs(ospath(cfg2.pdf_path))
    except:
        pass


def main(config, more=False, initial=True):
    if initial:
        init(config)
    cfg = gen_cfg(config)
    if os.path.exists(ospath(f"{cfg2.dir_path}index.json")):
        cfg = gen_cfg(json.loads(read_file(f"{cfg2.dir_path}index.json")))
    print(f"文档名：{cfg.p_name}")
    print(f"文档 ID：{cfg.p_code}")
    print(f"上传日期：{cfg.p_date}")
    print(f"页数：{cfg.p_pagecount}")
    if int(cfg.p_pagecount) != cfg.p_count:
        more = True
        print(f"可预览页数：{cfg.p_countinfo}")
        print(f"可直接获取页数：{cfg.p_count}")
        print(f"可能有额外页面（需扫描）！")
    if not choose("开始提取？ (Y/n): "):
        return False
    if cfg.p_download == "1":
        print("该文档为免费文档，可直接下载！")
        if choose("down"):
            try:
                if config["if_zip"] == 0:
                    doc_format = str.lower(cfg.p_doc_format)
                else:
                    doc_format = "zip"
                file_path = "docs/" + cfg.p_name + "." + doc_format
                download(
                    get_request(
                        "https://www.doc88.com/doc.php?act=download&pcode=" + cfg.p_code
                    , referer=True, cffi=True).text,
                    file_path,
                )
                print("Saved file to " + file_path)
                return True
            except Exception as err:
                print("Download error: " + str(err))
                logw("Download error: " + str(err))
        else:
            print("Continuing...")
    if more:
        if choose("即将通过扫描获取页面，是否继续（否则正常下载）？ (Y/n): "):
            print("尝试通过扫描获取页面...")
            newpageids = []
            cfg.p_count = 0
            for i in range(1, cfg.ph_nums() + 1):
                get = get_more(cfg, i, cfg2.dir_path, cfg.p_count)
                get.start()
                newpageids += get.newpageids
                cfg.p_count += len(get.newpageids)
                del get
            cfg.pageids = newpageids
            config["pageInfo"] = encode(",".join(newpageids))
            config["p_count"] = cfg.p_count
            write_file(
                bytes(json.dumps(config), encoding="utf-8"),
                cfg2.dir_path + "index.json",
            )
            print(f"成功扫描页数：{cfg.p_count}")
            del newpageids
            time.sleep(2)
        else:
            print("普通下载模式...")
            more = False
    try:
        if not more:
            get_swf(cfg)
        if not debug:
            convert(cfg)
            del cfg
        return True
    except Exception as err:
        print(err)
        return False


class downloader:
    def __init__(self, cfg: gen_cfg) -> None:
        self.cfg = cfg
        self.downloaded = True
        self.progressfile = cfg2.dir_path + "progress.json"
        if os.path.isfile(ospath(self.progressfile)):
            self.read_progress()
        else:
            self.progress = {"pk": [], "ph": []}

    def read_progress(self):
        try:
            self.progress = json.loads(read_file(self.progressfile))
        except json.decoder.JSONDecodeError:
            self.progress = {}

    def save_progress(self, type: str, page: int):
        self.progress[type].append(page)
        writes_file(json.dumps(self.progress), self.progressfile)

    def ph(self, i: int):
        url = self.cfg.ph(i)
        print(f"Downloading PH {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["ph"]:
            print("Using Cache...")
            return None
        try:
            download(url.url, file_path)
            self.save_progress("ph", i)
        except Exception as e:
            logw(f"Download PH {i} error: {e}")
            self.downloaded = False

    def pk(self, i: int):
        url = self.cfg.pk(i)
        print(f"Downloading page {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["pk"]:
            print("Using Cache...")
            return None
        try:
            download(url.url, file_path)
            self.save_progress("pk", i)
        except Exception as e:
            logw(f"Download page {i} error: {e}")
            self.downloaded = False

    def makeswf(self, i: int):
        try:
            level_num = self.cfg.ph_num(i)
            make_swf(
                cfg2.dir_path + self.cfg.ph(level_num).name,
                cfg2.dir_path + self.cfg.pk(i).name,
                cfg2.swf_path + str(i) + ".swf",
            )
        except Exception as e:
            print(f"Can't decompress page {i}! Skipping...")
            logw(str(e))
            self.cfg.p_count -= 1


def get_swf(cfg: gen_cfg):
    max_workers = cfg2.download_workers
    down = downloader(cfg)
    print("Downloading PH...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.ph_nums() + 1):
            executor.submit(down.ph, i)
    print("Downloading PK...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.pk, i)
    if not down.downloaded:
        raise Exception("Download error")
    print("Making pages...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.makeswf, i)
    print(f"Download done. (total page: {cfg.p_count})")

# TODO: 移除 cfg2 全局变量
class converter:
    def __init__(self) -> None:
        self.pdf = PdfWriter()
        self.pdflist = []

    # 帧画布大小修正
    def set_swf(self, i: int, w, h):
        return subprocess.run(
                ["java", "-jar", "ffdec/ffdec.jar", "-header", "-set", "width", f"{w}px", "-set", "height", f"{h}px", f"{cfg2.swf_path}{i}.swf", f"{cfg2.swf_path}{i}.swf"],
                capture_output=True,
                text=True,
            )

    def swf2svg(self, i: int):
        print(f"SWF -> SVG converting worker {i} started.")
        if os.listdir(ospath(f"{cfg2.swf_path}{i}")) == []:
            return
        log = ""
        try:
            dirpath = cfg2.svg_path + str(i) + "/"
            run = subprocess.run(
                ["java", "-jar", "ffdec/ffdec.jar", "-format", "frame:svg", "-select", "1", "-export", "frame", dirpath, f"{cfg2.swf_path}{i}"],
                capture_output=True,
                text=True,
            )
            log = run.stdout
            if run.returncode != 0:
                logw("SVG converting error: " + (run.stderr or run.stdout))
            for f in os.listdir(ospath(dirpath)):
                if os.path.isdir(ospath(f"{dirpath}{f}")):
                    shutil.move(
                        ospath(f"{dirpath}{f}/1.svg"), ospath(f"{cfg2.svg_path}{f[:-4]}.svg")
                    )
            # 删除ffdec的临时文件夹
            try:
                shutil.rmtree(ospath(f"{dirpath}"))
            except PermissionError:
                print("Can't delete temporary folder, maybe file is opened?")
            # 删除分组文件夹
            try:
                shutil.rmtree(ospath(f"{cfg2.swf_path}{i}/"))
            except PermissionError:
                print("Can't delete temporary folder, maybe file is opened?")
            except FileNotFoundError:
                pass
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")
            logw("SVG converting error: " + log)

    def swf2pdf(self, i: int):
        if os.listdir(ospath(f"{cfg2.swf_path}{i}")) == []:
            return
        print(f"SWF -> PDF converting worker {i} started.")
        log = ""
        try:
            dirpath = cfg2.pdf_path + str(i) + "/"
            run = subprocess.run(
                ["java", "-jar", "ffdec/ffdec.jar", "-format", "frame:pdf", "-zoom", str(cfg2.pdf_scale), "-select", "1", "-export", "frame", dirpath, f"{cfg2.swf_path}{i}"],
                capture_output=True,
                text=True,
            )
            log = run.stdout
            if run.returncode != 0:
                logw("PDF converting error: " + (run.stderr or run.stdout))
            for f in os.listdir(ospath(dirpath)):
                if os.path.isdir(ospath(f"{dirpath}{f}")):
                    shutil.move(
                        ospath(f"{dirpath}{f}/frames.pdf"), ospath(f"{cfg2.pdf_path}{f[:-4]}.pdf")
                    )
                    self.pdflist.append(f[:-4])
            # 删除ffdec的临时文件夹
            try:
                shutil.rmtree(ospath(f"{dirpath}"))
            except PermissionError:
                print("Can't delete temporary folder, maybe file is opened?")
            # 删除分组文件夹
            try:
                shutil.rmtree(ospath(f"{cfg2.swf_path}{i}/"))
            except PermissionError:
                print("Can't delete temporary folder, maybe file is opened?")
            except FileNotFoundError:
                pass
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")
            logw("PDF converting error: " + log)

    def svg2pdf(self, i: int):
        try:
            print(f"Converting page {i} to pdf...")
            # cairosvg.svg2pdf(
            #     url=f"{cfg2.pdf_path}{i}_.svg",
            #     write_to=str(ospath(f"{cfg2.pdf_path}{i}.pdf")),
            # )
            run=subprocess.run(
                ["./svg2pdf", f"{cfg2.svg_path}{i}.svg", f"{cfg2.pdf_path}{i}.pdf"], text=True, capture_output=True
            )
            self.pdflist.append(i)
        except FileNotFoundError as e:
            print("Can't convert this page! Skipping...")
            logw(f"SVG to PDF converting error: {e}")

    def makepdf(self):
        self.pdflist = sorted(self.pdflist, key=lambda x: int(x))
        for i in self.pdflist:
            self.pdf = append_pdf(
                self.pdf, str(ospath(f"{cfg2.pdf_path}{i}.pdf"))
            )
    # 根据工作流数量平均分配 SWF 文件到各组文件夹中
    def divide_swfs(self, count: int):
        file_index = os.listdir(ospath(cfg2.swf_path))
        swf_files = sorted([f for f in file_index if f.endswith('.swf')], key=lambda x: int(x[:-4]))
        for idx, swf_file in enumerate(swf_files):
            group_num = idx % count
            group_path = ospath(f"{cfg2.swf_path}{group_num}/")
            try:
                os.makedirs(group_path)
            except FileExistsError:
                pass
            src_path = os.path.join(ospath(cfg2.swf_path), swf_file)
            dest_path = os.path.join(group_path, swf_file)
            shutil.copy(src_path, dest_path)


def convert(cfg: gen_cfg):
    print("开始转换...")
    if cfg2.swf2svg:
        print(
            "!! 警告: 此过程可能会使用较高的 CPU 使用率。您可以在配置文件中修改线程数以平衡性能 !!"
        )
    else:
        print("!! 警告: 此过程可能会使用较高的 CPU 使用率，以及较长的时间。您可以在配置文件中修改线程数以平衡性能 !!")
    max_workers = cfg2.convert_workers
    doc = converter()
    if cfg2.fix_displayrect:
        print("Now start fixing swf displayrect, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                executor.submit(doc.set_swf, i, cfg.pageids[i-1].split("-")[1], cfg.pageids[i-1].split("-")[2])
    doc.divide_swfs(cfg2.convert_workers)
    if not cfg2.swf2svg:
        print("Now start SWF -> PDF converting, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(0, max_workers):
                executor.submit(doc.swf2pdf, i)
    else:
        print("Now start SWF -> SVG converting, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(0, max_workers):
                executor.submit(doc.swf2svg, i)
        print("Now start SVG -> PDF converting, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                executor.submit(doc.svg2pdf, i)
    print("Now start making pdf, please wait...")
    doc.makepdf()
    pdf_name = cfg2.o_dir_path + special_path(cfg.p_name) + ".pdf"
    doc.pdf.write(str(ospath(pdf_name)))
    print("转换完成！")
    print("已将文件保存至 " + pdf_name)
    print(
        "Tip: 在 Edge 中查看文档可能会无法正常显示文本，但您也可以使用其他阅读器，例如 Chrome。"
    )


def clean(cfg2):
    print("正在清理缓存...")
    shutil.rmtree(ospath(cfg2.swf_path))
    shutil.rmtree(ospath(cfg2.pdf_path))
    shutil.rmtree(ospath(cfg2.svg_path))
    for i in os.listdir(ospath(cfg2.dir_path)):
        if i.endswith(".ebt"):
            os.remove(ospath(cfg2.dir_path + i))
        elif i == "progress.json":
            os.remove(ospath(cfg2.dir_path + i))


class mode:
    def __init__(self) -> None:
        return None

    def cli(self):
        user_input = input("请输入：").strip()
        if user_input.startswith("http"):
            return self.url(user_input)
        if user_input.isdigit():
            return self.pcode(user_input)
        elif os.path.isfile(ospath(user_input)):
            if user_input.endswith(".xdf"):
                return self.dirs(user_input)
            else:
                print("错误的文件类型！")
                return False
        elif os.path.isdir(ospath(user_input)):
            try:
                if any(f.endswith(".ebt") for f in os.listdir(ospath(user_input))):
                    return self.dirs(user_input)
                else:
                    print("该文件夹内没有ebt文件！")
                    return False
            except PermissionError:
                print("无权访问该文件夹！")
                return False
        else:
            print("无效输入！")
            return False
    def url(self, url):
        try:
            return main(get_main_from_url(url), cfg2.get_more)
        except Exception as Err:
            print(Err)
            return False

    def pcode(self, p_code=None):
        try:
            return self.url(f"https://www.doc88.com/p-{p_code}.html")
        except Exception as Err:
            print(Err)
            return False

    def dirs(self, dir_path):
        try:
            ebts = import_ebt(dir_path)
            config = build_cfg(*ebts)
            cfg = gen_cfg(config)
            init(config)
            # 复制文件到对应目录并生成下载缓存列表
            progress = downloader(cfg)
            for ph in ebts[0]:
                shutil.copy(ospath(ph["path"]), ospath(cfg2.dir_path))
                progress.save_progress("ph", ph["level"])
            for pk in ebts[1]:
                shutil.copy(ospath(pk["path"]), ospath(cfg2.dir_path))
                progress.save_progress("pk", pk["page"])
            return main(config, cfg2.get_more, False)
        except Exception as Err:
            print(Err)
            return False


if __name__ == "__main__":
    update=Update(cfg2)
    if not update.check_java():
        input_break()
        exit()
    if cfg2.check_update or not os.path.isfile("ffdec/ffdec.jar"):
        update.check_ffdec_update()
    if cfg2.check_update:
        update.check_update()
    update.upgrade()
    if not update.ffdec_configure():
        print("ffdec 配置失败！")
        print("请尝试：\n1. 检查 Java 是否正常并使用了推荐版本\n2. 检查 ffdec 是否安装正确且能正常运行")
        if os.name == "nt":
            print("3. 删除 ffdec 的配置文件（通常在 %APPDATA%\\JPEXS\\FFDec\\config.toml）后重试")
        else:
            print("3. 删除 ffdec 的配置文件后重试")
        input_break()
        exit()
    if cfg2.swf2svg:
        print(
            "使用 SVG 转换功能建议同时关闭 font-face 功能，否则将会导致字体丢失，若只需要 SVG 文件可关闭清理功能，文件将会生成到对应文档 ID 目录下的 svg 目录"
        )
        if not update.check_svg2pdf():
            print("svg2pdf 工具安装失败，将继续以 SWF 到 PDF 方式转换。")
            cfg2.swf2svg = False
    a = sys.argv
    user = mode()
    if "--debug" in a:
        global debug
        debug = True
    else:
        debug = False
    # TODO: 命令传参；XDF文件支持
    print("支持输入网址/文档ID/含有ebt文件的文件夹路径")
    print("输入示例：\n网址：https://www.doc88.com/p-12345678.html\n文档ID：12345678\n含有ebt文件的文件夹路径：./ebtfiles/")
    while True:
        if user.cli():
            if cfg2.clean:
                try:
                    clean(cfg2)
                except NameError:
                    pass
            if choose():
                pass
            else:
                exit()
        else:
            pass
