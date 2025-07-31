#!/usr/bin/python
# -*- coding: utf-8 -*-

print("DOC88 （预览）文档提取工具")
print("by: Cuite_Piglin")
print(
    "\n免责声明： 仅供学习或交流用，请在 24 小时内删除本程序，严禁用于任何商业或非法用途，使用该工具而产生的任何法律后果，用户需自行承担全部责任\n"
)
import os
from config import *
if cfg2.swf2svg:
    print("使用 SVG 转换功能建议同时关闭 font-face 功能，否则将会导致大量转换失败，若只需要 SVG 文件可关闭清理功能，文件将会生成到文档目录下的 svg 目录")
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
import sys
import json
import re
import shutil
from compressor import *
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfWriter
from gen_cfg import *
from get_more import *
from utils import *

def check_ffdec():
    ffdec_url = "https://ghproxy.cn/https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version24.0.1/ffdec_24.0.1.zip"
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

class get_cfg():
    def __init__(self,url: str) -> None:
        if url.find("doc88.com/p-")  == -1 and url.find("doc88.piglin.eu.org/p-") == -1:
            raise Exception("Invalid URL!")
        self.url=url
        self.content=""
        self.data=""
        self.sta=0
        if not self.get_main():
            if choose("Do you want to use CDN?(Y/n): "):
                self.__init__("https://doc88.piglin.eu.org"+url[url.find("doc88.com/")+9:])
                return None
        return None
    def req(self):
        request = get_request(self.url)
        if request.status_code == 404:
            self.sta=1
            raise Exception("404 Not found!")
        self.content=request.text

    def get_main(self):
        self.req()
        data = re.search(r"m_main.init\(\".*\"\);", self.content)
        if data == None:
            if re.search("网络环境安全验证",self.content):
                print("WAF detected!")
                return False
            raise Exception("Config data not found! May be deleted?")
        c = data.span()
        self.data = self.content[c[0] + 13 : c[1] - 3]
        return True

def append_pdf(pdf: PdfWriter, file: str):
    pdf.append(ospath(file))
    return pdf


class init():
    def __init__(self, config: dict) -> None:
        cfg2.dir_path = cfg2.o_dir_path +  config["p_name"] + "/"
        cfg2.swf_path = cfg2.dir_path + cfg2.o_swf_path
        cfg2.svg_path = cfg2.dir_path + cfg2.o_svg_path
        cfg2.pdf_path = cfg2.dir_path + cfg2.o_pdf_path
        try:
            os.makedirs(ospath(cfg2.dir_path))
        except FileExistsError:
            if choose("exists"):
                pass
            else:
                exit()
        if not os.path.exists(ospath(f"{cfg2.dir_path}index.json")):
            write_file(bytes(json.dumps(config),encoding="utf-8"),cfg2.dir_path + "index.json")
        try:
            os.makedirs(ospath(cfg2.swf_path))
            os.makedirs(ospath(cfg2.svg_path))
            os.makedirs(ospath(cfg2.pdf_path))
        except:
            print("")


def main(encoded_str,more=False):
    try:
        config = json.loads(decode(encoded_str))
    except json.decoder.JSONDecodeError:
        print("Can't read!")
        return False
    except (ValueError, UnicodeDecodeError):
        print("Can't read! Maybe keys were changed?")
        return False
    init(config)
    cfg = gen_cfg(config)
    if os.path.exists(ospath(f"{cfg2.dir_path}index.json")):
        cfg = gen_cfg(json.loads(read_file(f"{cfg2.dir_path}index.json")))
    print(f"文档名：{cfg.p_name}")
    print(f"上传日期：{cfg.p_date}")
    print(f"页数：{cfg.p_pagecount}")
    time.sleep(1)
    if int(cfg.p_pagecount) != cfg.p_count:
        more=True
        print(f"可预览页数：{cfg.p_countinfo}")
        print(f"可直接获取页数：{cfg.p_count}")
        print(f"可能有额外页面（需扫描）！")
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
                    file_path
                )
                print("Saved file to " + file_path)
                return True
            except Exception as err:
                print("Downlaod error: " + str(err))
                logw("Downlaod error: " + str(err))
        else:
            print("Continuing...")
    if more:
        if choose("即将通过扫描获取页面，是否继续（否则正常下载）？ (Y/n): "):
            print("尝试通过扫描获取页面...")
            newpageids=[]
            cfg.p_count=0
            for i in range(1,cfg.phnum()+1):
                get=get_more(cfg,i,cfg2.dir_path,cfg.p_count)
                get.start()
                newpageids+=get.newpageids
                cfg.p_count+=len(get.newpageids)
                del get
            cfg.pageids=newpageids
            config['pageInfo']=encode(','.join(newpageids))
            config['p_count']=cfg.p_count
            write_file(bytes(json.dumps(config),encoding="utf-8"),cfg2.dir_path + "index.json")
            print(f"成功扫描页数：{cfg.p_count}")
            del newpageids
            time.sleep(2)
        else:
            print("普通下载模式...")
            more=False
    try:
        if not more:
            get_swf(cfg)
        convert(cfg)
        del cfg
        return True
    except Exception as err:
        print(err)
        return False


class downloader():
    def __init__(self,cfg: gen_cfg) -> None:
        self.cfg=cfg
        self.downloaded=True
        self.progressfile=cfg2.dir_path + "progress.json"
        if os.path.isfile(ospath(self.progressfile)):
            self.read_progress()
        else:
            self.progress={
                "pk": [],
                "ph": []
            }
    
    def read_progress(self):
        try:
            self.progress = json.loads(read_file(self.progressfile))
        except json.decoder.JSONDecodeError:
            self.progress = {}

    def save_progress(self,type: str, page: int):
        self.progress[type].append(page)
        writes_file(json.dumps(self.progress),self.progressfile)

    def ph(self,i: int):
        url = self.cfg.ph(i)
        print(f"Downloading PH {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["ph"]:
            print("Using Cache...")
            return None
        try:
            download(url.url, file_path)
            self.save_progress("ph",i)
        except Exception as e:
            logw(f"Download PH {i} error: {e}")
            self.downloaded=False

    def pk(self,i: int):
        url = self.cfg.pk(i)
        print(f"Downloading page {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["pk"]:
            print("Using Cache...")
            return None
        try:
            download(url.url, file_path)
            self.save_progress("pk",i)
        except Exception as e:
            logw(f"Download page {i} error: {e}")
            self.downloaded=False

    def makeswf(self, i: int):
        try:
            level_num = self.cfg.ph_num(i)
            make_swf(
                cfg2.dir_path + self.cfg.ph(level_num).name,
                cfg2.dir_path + self.cfg.pk(i).name,
                cfg2.swf_path + str(i) + ".swf"
            )
        except Exception as e:
            print(f"Can't decompress page {i}! Skipping...")
            logw(str(e))
            self.cfg.p_count -= 1


def get_swf(cfg: gen_cfg):
    max_workers=10
    down=downloader(cfg)
    print("Downloading PH...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.phnum()+1):
            executor.submit(down.ph, i)
    print("Downloading PK...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.pk, i)
    if not down.downloaded:
        print("Downlaod error")
    print("Making pages...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.makeswf, i)
    print("Donload done. (total page: " + str(cfg.p_count) + ")")

class converter():
    def __init__(self) -> None:
        self.pdf=PdfWriter()
        self.pdflist=set()
        try:
            if cfg2.svgfontface:
                log=os.popen(
                    "java -jar ffdec/ffdec.jar -config textExportExportFontFace=true"
                ).read()
            else:
                log=os.popen(
                    "java -jar ffdec/ffdec.jar -config textExportExportFontFace=flase"
                ).read()
        except Exception as err:
            logw(str(err))
    def set_swf(self,i:int):
        return os.popen(
                "java -jar ffdec/ffdec.jar -header -set frameCount 1 "
                + r(cfg2.swf_path + str(i) + ".swf")
                + " "
                + r(cfg2.swf_path + str(i) + ".swf")
        ).read()
    
    def swf2svg(self,i: int):
        def execute(num: int):
            dirpath=cfg2.svg_path + str(num) + '/'
            log=os.popen(
                "java -jar ffdec/ffdec.jar -format frame:svg -select 1 -export frame "
                + r(dirpath)
                + " "
                + r(cfg2.swf_path + str(num) + ".swf")
            ).read()
            shutil.move(ospath(dirpath + "1.svg"), ospath(cfg2.svg_path + str(i) + "_.svg"))
            shutil.rmtree(ospath(dirpath))
        
        print("Converting page " + str(i) + " to svg...")
        try:
            execute(i)
        except FileNotFoundError:
            log=self.set_swf(i)
            try:
                execute(i)
            except FileNotFoundError:
                print("Can't convert this page! Skipping...")
                logw("SVG converting error: " + log)
    
    def swf2pdf(self,i: int):
        def execute(num: int):
            dirpath=cfg2.pdf_path + str(num) + '/'
            log=os.popen(
                "java -jar ffdec/ffdec.jar -format frame:pdf -select 1 -export frame "
                + r(dirpath)
                + " "
                + r(cfg2.swf_path + str(num) + ".swf")
            ).read()
            shutil.move(ospath(dirpath + "frames.pdf"), ospath(cfg2.pdf_path + str(i) + "_.pdf"))
            shutil.rmtree(dirpath)
            shutil.move(ospath(cfg2.pdf_path + str(i) + "_.pdf"), ospath(cfg2.pdf_path + str(i) + ".pdf"))
            self.pdflist.add(i)
        print("Converting page " + str(i) + " to pdf...")
        try:
            execute(i)
        except FileNotFoundError:
            log=self.set_swf(i)
            try:
                execute(i)
            except FileNotFoundError:
                print("Can't convert this page! Skipping...")
                logw("PDF converting error: " + log)

    def svg2pdf(self,i: int):
        try:
            print(f"Converting page {i} to pdf...")
            cairosvg.svg2pdf(
                url=cfg2.svg_path + str(i) + "_.svg", write_to=str(ospath(cfg2.pdf_path + str(i) + ".pdf"))
            )
            self.pdflist.add(i)
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")

    def makepdf(self):
        for i in self.pdflist:
            self.pdf = append_pdf(self.pdf, str(ospath(cfg2.pdf_path + str(i) + ".pdf")))


def convert(cfg):
    print("Now start converting...")
    print(
        "!! Warnning: This process may uses very big memory(100MB-5GB), and much time. We will optimize it in future. !!"
    )
    max_workers=5
    doc=converter()
    if not cfg2.swf2svg:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                executor.submit(doc.swf2pdf, i)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                executor.submit(doc.swf2svg, i)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                executor.submit(doc.svg2pdf, i)
    print("Now start making pdf, please wait...")
    doc.makepdf()
    doc.pdf.write(str(ospath(cfg2.dir_path[:-1] + ".pdf")))
    print("Saved file to " + cfg2.dir_path[:-1] + ".pdf")
    print("Tip: Sometimes viewing the file in Edge will cause some problems that can't display texts properly, but you can use another viewer such as Chrome.")


def clean(cfg2):
    print("cleaning cache...")
    shutil.rmtree(ospath(cfg2.swf_path))
    shutil.rmtree(ospath(cfg2.pdf_path))
    shutil.rmtree(ospath(cfg2.svg_path))

class mode():
    def __init__(self) -> None:
        self.encode=""
    
    def url(self):
        try:
            url = input("请输入网址：")
        except KeyboardInterrupt:
            exit()
        try:
            return main(get_cfg(url).data,cfg2.get_more)
        except Exception as Err:
            print(Err)
            return False
    
    def pcode(self):
        try:
            p_code = input("请输入id：")
        except KeyboardInterrupt:
            exit()
        try:
            return main(get_cfg(f"https://www.doc88.com/p-{p_code}.html").data,cfg2.get_more)
        except Exception as Err:
            print(Err)
            return False

    def data(self):
        try:
            data = input("请输入init_data：")
        except KeyboardInterrupt:
            exit()
        try:
            return main(data,cfg2.get_more)
        except Exception as Err:
            print(Err)
            return False

if __name__ == "__main__":
    check_ffdec()
    a = sys.argv
    user=mode()
    if len(a) == 1:
        exe=user.url
    elif "-p" in a:
        exe=user.pcode
    elif "-d" in a:
        exe=user.data
    while True:
        if exe() and cfg2.clean:
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