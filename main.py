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
import json
import requests
import compressor
import re
import zipfile
import shutil
import cairosvg
from pypdf import PdfWriter
from gen_url import *


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
        "Referer": "https://www.doc88.com/"}
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


def init(config: dict):
    global dir_path
    dir_path = "docs/" + config["p_name"] + "/"
    global swf_path
    swf_path = dir_path + "swf/"
    global pdf_path
    pdf_path = dir_path + "pdf/"
    global svg_path
    svg_path = dir_path + "svg/"
    try:
        os.makedirs(dir_path)
    except FileExistsError:
        if choose("exists"):
            pass
        else:
            exit()
    with open(dir_path + "index.json", "w") as file:
        file.write(json.dumps(config))
    try:
        os.makedirs(swf_path)
        os.makedirs(svg_path)
        os.makedirs(pdf_path)
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
    print("文档名：" + config["p_name"])
    print("上传日期：" + config["p_upload_date"])
    print("总页数：" + str(config["pageCount"]))
    if config["p_download"] == "1":
        print("该文档为免费文档，可直接下载！")
        if choose("down"):
            try:
                if config["if_zip"] == 0:
                    doc_format = str.lower(config["p_doc_format"])
                else:
                    doc_format = "zip"
                file_path = "docs/" + config["p_name"] + "." + doc_format
                download(
                    get_request(
                        "https://www.doc88.com/doc.php?act=download&pcode="
                        + config["p_code"]
                    ).text,
                    file_path,
                )
                print("Saved file to " + file_path)
                return True
            except Exception as err:
                print("Downlaod error: " + str(err))
        else:
            print("Continuing...")
    init(config)
    try:
        get_swf(config)
        convert(config["pageCount"])
        return True
    except Exception as err:
        print(err)
        return False


def get_swf(config: dict):
    gen=gen_url(config)
    print("Downloading PK...")
    pks=[]
    for i in range(0, gen.pknum()):
        print("Downloading PK" + str(i) + "...")
        url = gen.pk(i)
        file_path = dir_path + url[25:]
        pks.append(url[25:])
        print(url)
        download(url, file_path)
    for i in range(1, config["pageCount"] + 1):
        print("Downloading page " + str(i) + "...")
        url = gen.ph(i)
        file_path = dir_path + url[25:]
        print(url)
        download(url, file_path)
        compressor.make(
            dir_path + pks[gen.level_num], dir_path + url[25:], swf_path + str(i) + ".swf"
        )
    print("Donload done. (total page: " + str(config["pageCount"]) + ")")


def convert(pageCount: int):
    print("Now start converting...")
    print(
        "!! Warnning: This process may uses very big memory(100MB-5GB), and much time. We will optimize it in future. !!"
    )
    pdf = PdfWriter()

    def execute(num: int):
        os.system(
            "java -jar ffdec/ffdec.jar -format frame:svg -select 1 -export frame "
            + r(svg_path)
            + " "
            + r(swf_path + str(num) + ".swf")
        )
        shutil.move(svg_path + "1.svg", svg_path + str(i) + "_.svg")

    for i in range(1, pageCount + 1):
        print("Converting page " + str(i) + " to svg...")
        try:
            execute(i)
        except FileNotFoundError:
            os.system(
                "java -jar ffdec/ffdec.jar -header -set frameCount 1 "
                + r(swf_path + str(i) + ".swf")
                + " "
                + r(swf_path + str(i) + ".swf")
            )
            execute(i)
        print("Converting svg to pdf...")
        cairosvg.svg2pdf(
            url=svg_path + str(i) + "_.svg", write_to=pdf_path + str(i) + ".pdf"
        )
        pdf = append_pdf(pdf, pdf_path + str(i) + ".pdf")
    pdf.write(dir_path[:-1] + ".pdf")
    print("Saved file to " + dir_path[:-1] + ".pdf")


def clean():
    print("cleaning cache...")
    shutil.rmtree(swf_path)
    shutil.rmtree(pdf_path)
    shutil.rmtree(svg_path)


if __name__ == "__main__":
    check_ffdec()
    a = sys.argv
    if len(a) == 1:
        while True:
            if main():
                try:
                    clean()
                except NameError:
                    pass
                if choose():
                    pass
                else:
                    exit()
            else:
                pass
