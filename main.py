print("DOC88 （预览）文档提取工具")
print("by: Cuite_Piglin")
print(
    "\n免责声明： 仅供学习或交流用，请在 24 小时内删除本程序，严禁用于任何商业或非法用途，使用该工具而产生的任何法律后果，用户需自行承担全部责任\n"
)
import os
import platform

if platform.system() == "Windows":
    print(
        "警告：你正在使用 Windows 系统下使用此工具，虽然我们有意使其在多平台下运行，但需要使用 Cairo 库才能进行 pdf 的转换，建议你安装 GTK 运行库（需要 200MB 左右的安装空间）：\nhttps://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases\n如果安装后仍然无效，请尝试将安装目录下的 bin 目录添加到系统环境的 PATH 中然后重启终端或 Vscode\n"
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
import sys
import time
import json
import requests
import compressor
import re
import zipfile
import shutil
import cairosvg
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfWriter
from gen_cfg import *
from config import *

def choose(text=""):
    if text == "exists":
        text = "The directory already exists!\nContinue? (Y/n): "
    elif text == "down":
        text = "是否下载，否则继续提取预览文档？ (Y/n): "
    else:
        text = "Continue? (Y/n): "
    try:
        user_input = input(text)
    except KeyboardInterrupt:
        exit()
    if user_input == "Y" or user_input == "y":
        return True
    else:
        return False

def logw(t: str):
        log='[' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ']: ' + t + '\n'
        log_dir='logs/'
        dirc=log_dir + time.strftime('%Y-%m-%d', time.localtime()) + '.log'
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        with open(dirc, 'a') as file:
            file.write(log)

def check_ffdec():
    ffdec_url = "https://ghproxy.cn/https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version22.0.1/ffdec_22.0.1.zip"
    if not os.path.exists("ffdec/ffdec.jar"):
        print("Ffdec not found! Now start to download ffdec.")
        print(
            "Warnning: use built download method may be very slow, if you already had ffdec files, please put these(make sure that have 'ffdec.jar') to the diretory 'ffdec'."
        )
        print("Downloading: " + ffdec_url)
        try:
            os.makedirs("ffdec")
        except FileExistsError:
            if choose("exists"):
                shutil.rmtree("ffdec")
                os.makedirs("ffdec")
                print("Continuing...")
            else:
                exit()
        try:
            download(ffdec_url, "ffdec/ffdec.zip")
        except:
            print(
                "Download error! Plase check the Internet connection or modify the 'ffdec_url' content in function 'check_ffdec'. If still not work, extract the ffdec files to diretory ffdec."
            )
            input()
            exit()
        print("Download done! Start extracting...")
        try:
            extractzip("ffdec/ffdec.zip", "ffdec/")
        except zipfile.BadZipFile:
            print(
                "Can't extract! Is the link out of date? Try to update the 'ffdec_url' in function 'check_ffdec'"
            )
            input()
            exit()
    if os.system("java -version > " + os.devnull) != 0:
        print("Java not found! Plase install java and add java to PATH.")
        input()
        exit()


def r(str):
    return '"' + str + '"'


def get_request(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39",
        "Content-Type": "text/html; charset=utf-8",
        "Referer": "https://www.doc88.com/",
    }
    return requests.get(url, headers=headers, proxies=None)


def get_cfg(url: str):
    if url.find("doc88.com/p-") == -1:
        raise Exception("Invalid URL!")
    request = get_request(url)
    if request.status_code == 404:
        raise Exception("404 Not Found!")
    a = str(request.text)
    b = re.search(r"m_main.init\(\".*\"\);", a)
    if b == None:
        raise Exception("Config data not found! May be deleted?")
    c = b.span()
    return a[c[0] + 13 : c[1] - 3]


def download(url: str, filepath: str):
    response = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(response.content)
        f.close()
    return filepath


def extractzip(file_path: str, topath: str):
    with zipfile.ZipFile(file_path, "r") as f:
        f.extractall(topath)
        f.close


def append_pdf(pdf: PdfWriter, file: str):
    with open(file, "rb") as f:
        pdf.append(f)
    return pdf


class init():
    def __init__(self, config: dict) -> None:
        cfg2.dir_path = cfg2.o_dir_path +  config["p_name"] + "/"
        cfg2.swf_path = cfg2.dir_path + cfg2.o_swf_path
        cfg2.svg_path = cfg2.dir_path + cfg2.o_svg_path
        cfg2.pdf_path = cfg2.dir_path + cfg2.o_pdf_path
        try:
            os.makedirs(cfg2.dir_path)
        except FileExistsError:
            if choose("exists"):
                pass
            else:
                exit()
        with open(cfg2.dir_path + "index.json", "w") as file:
            file.write(json.dumps(config))
        try:
            os.makedirs(cfg2.swf_path)
            os.makedirs(cfg2.svg_path)
            os.makedirs(cfg2.pdf_path)
        except:
            print("")


def main():
    try:
        url = input("请输入网址：")
    except KeyboardInterrupt:
        exit()
    try:
        encoded_str = get_cfg(url)
    except Exception as Err:
        print(Err)
        return False
    try:
        config = json.loads(decode(encoded_str))
    except json.decoder.JSONDecodeError:
        print("Can't read!")
        return False
    except (ValueError, UnicodeDecodeError):
        print("Can't read! Maybe keys were changed?")
        return False
    cfg = gen_cfg(config,more=False)
    print("文档名：" + cfg.p_name)
    print("上传日期：" + cfg.p_date)
    print("页数：" + str(cfg.p_countinfo))
    if int(cfg.p_countinfo) != cfg.p_count:
        print("实际页数：" + str(cfg.p_count))
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
                        "https://www.doc88.com/doc.php?act=download&pcode="
                        + cfg.p_code
                    ).text,
                    file_path,
                )
                print("Saved file to " + file_path)
                return True
            except Exception as err:
                print("Downlaod error: " + str(err))
                logw("Downlaod error: " + str(err))
        else:
            print("Continuing...")
    init(config)
    try:
        get_swf(cfg)
        convert(cfg)
        return True
    except Exception as err:
        print(err)
        return False
class downloader():
    def __init__(self,cfg) -> None:
        self.pks = []
        self.cfg=cfg
        self.downloaded=False
        self.progressfile=cfg2.dir_path + "progress.json"
        if os.path.isfile(self.progressfile):
            self.read_progress()
        else:
            self.progress={
                "pk": [],
                "ph": []
            }
    
    def read_progress(self):
        with open(self.progressfile, "r") as file:
            self.progress = json.loads(file.read())
            file.close()

    def save_progress(self,type: str, page: int):
        self.progress[type].append(page)
        with open(self.progressfile, "w") as file:
            file.write(json.dumps(self.progress))
            file.close()

    def pk(self,i):
        print(f"Downloading PK {i}...")
        url = self.cfg.pk(i)
        file_path = cfg2.dir_path + url[25:]
        self.pks.append(url[25:])
        if i in self.progress["pk"]:
            print("Using Cache...")
            return None
        print(url)
        try:
            download(url, file_path)
            self.save_progress("pk",i)
        except Exception as e:
            logw(f"Download PK {i} error: {e}")
            self.downloaded=False

    def ph(self,i):
        print(f"Downloading page {i}...")
        url = self.cfg.ph(i)
        file_path = cfg2.dir_path + url[25:]
        if i in self.progress["ph"]:
            print("Using Cache...")
            return None
        print(url)
        try:
            download(url, file_path)
            self.save_progress("ph",i)
        except Exception as e:
            logw(f"Download PH {i} error: {e}")
            self.downloaded=False

    def makeswf(self,i):
        try:
            compressor.make(
                cfg2.dir_path + self.pks[self.cfg.level_num - 1],
                cfg2.dir_path + self.cfg.ph(i)[25:],
                cfg2.swf_path + str(i) + ".swf",
            )
        except Exception as e:
            print("Can't decompress this page! Skipping...")
            logw(str(e))
            self.cfg.p_count-=1

def get_swf(cfg):
    max_workers=5
    down=downloader(cfg)
    print("Downloading PK...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(0, cfg.pknum()):
            executor.submit(down.pk, i)
    print("Downloading PH...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.ph, i)
    print("Making pages...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.makeswf, i)
    print("Donload done. (total page: " + str(cfg.p_count) + ")")

class converter():
    def __init__(self) -> None:
        self.pdf=PdfWriter()
        self.pdflist=[]
    def swf2svg(self,i: int):
        def execute(num: int):
            dirpath=cfg2.svg_path + str(num) + '/'
            log=os.popen(
                "java -jar ffdec/ffdec.jar -format frame:svg -select 1 -export frame "
                + r(dirpath)
                + " "
                + r(cfg2.swf_path + str(num) + ".swf")
            ).read()
            shutil.move(dirpath + "1.svg", cfg2.svg_path + str(i) + "_.svg")
            shutil.rmtree(dirpath)
        
        print("Converting page " + str(i) + " to svg...")
        try:
            execute(i)
        except FileNotFoundError:
            log=os.popen(
                "java -jar ffdec/ffdec.jar -header -set frameCount 1 "
                + r(cfg2.swf_path + str(i) + ".swf")
                + " "
                + r(cfg2.swf_path + str(i) + ".swf")
            ).read()
            try:
                execute(i)
            except FileNotFoundError:
                print("Can't convert this page! Skipping...")
                logw("SVG converting error: " + log)
    def svg2pdf(self,i: int):
        try:
            print(f"Converting page {i} to pdf...")
            cairosvg.svg2pdf(
                url=cfg2.svg_path + str(i) + "_.svg", write_to=cfg2.pdf_path + str(i) + ".pdf"
            )
            self.pdflist.append(i)
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")

    def makepdf(self):
        for i in self.pdflist:
            self.pdf = append_pdf(self.pdf, cfg2.pdf_path + str(i) + ".pdf")

def convert(cfg):
    print("Now start converting...")
    print(
        "!! Warnning: This process may uses very big memory(100MB-5GB), and much time. We will optimize it in future. !!"
    )
    max_workers=5
    doc=converter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(doc.swf2svg, i)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(doc.svg2pdf, i)
    doc.makepdf()
    doc.pdf.write(cfg2.dir_path[:-1] + ".pdf")
    print("Saved file to " + cfg2.dir_path[:-1] + ".pdf")


def clean(cfg2):
    print("cleaning cache...")
    shutil.rmtree(cfg2.swf_path)
    shutil.rmtree(cfg2.pdf_path)
    shutil.rmtree(cfg2.svg_path)


if __name__ == "__main__":
    check_ffdec()
    a = sys.argv
    if len(a) == 1:
        while True:
            if main():
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
