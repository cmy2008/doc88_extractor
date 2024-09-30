print("DOC88 （预览）文档提取工具")
print("by: Cuite_Piglin")
import os
import platform
if platform.system() == "Windows":
    print("警告：你正在使用Windows系统下使用此工具，虽然我们有意使其在多平台下运行，但需要使用Cairo库才能进行pdf的转换，建议你安装GTK运行库（需要200MB左右的安装空间）：\nhttps://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases\n如果安装后仍然无效，请尝试将安装目录下的bin目录添加到系统环境的PATH中然后重启终端或vscode")
    # os.add_dll_directory()
    list=os.environ['Path'].split(';')
    # print("Warnning: You're using Windows, please follow the README.md to install Cairo.")
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
from decode import decode
from decode import get_url

def check_ffdec():
    ffdec_url="https://github.com/jindrapetrik/jpexs-decompiler/releases/download/nightly2789/ffdec_20.1.0_nightly2789.zip"
    if not os.path.exists("ffdec/ffdec.jar"):
        print("Ffdec not found! Now start downloading ffdec...")
        print("Warnning: use built download method is really really really slow, if you want faster, please put the ffdec files that from local(make sure that have 'ffdec.jar') to diretory 'ffdec'.")
        print("Download link: https://github.com/jindrapetrik/jpexs-decompiler/releases/download/nightly2789/ffdec_20.1.0_nightly2789.zip")
        try:
            os.makedirs("ffdec")
        except:
            print("Cannot create directory! Please delete it and retry.")
            exit()
        try:
            download(ffdec_url,"ffdec/ffdec.zip")
        except:
            print("Download error! Plase check the Intenet connection or modify the 'ffdec_url' variable. If still not work, extract the ffdec files to diretory ffdec.")
        print("Download done! Starting extra zip...")
        extractzip("ffdec/ffdec.zip","ffdec/")

    if os.system("java --version") != 0:
        print("Java not found! Plase install java and add java to the path.")
        exit()
def r(str):
    return "\"" + str + "\""
# m_main.init
def get_str(url):
    proxies = { "http": None, "https": None}
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39", 'Content-Type': "application/x-www-form-urlencoded"}
    request = requests.get(url, headers = headers, proxies = proxies)
    a = str(request.text)
    b=re.search( r'm_main.init\(\".*\"\);', a)
    c=b.span()
    return a[c[0]+13:c[1]-3]

def download(url,filepath):
    response = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(response.content)

def extractzip(file_path,topath):
    with zipfile.ZipFile(file_path, "r") as f:
        f.extractall(topath)
        f.close

def append_pdf(pdf,file):
    with open(file,'rb') as f:
        pdf.append(f)
    return pdf

def init(config):
    global dir_path
    dir_path = 'docs/' + config['p_name'] + '/'
    global swf_path
    swf_path=dir_path + 'swf/'
    global pdf_path
    pdf_path = dir_path + 'pdf/'
    global svg_path
    svg_path = dir_path + 'svg/'
    try:
        os.makedirs(dir_path)
    except FileExistsError:
        print("The directory already exists!")
        user_input = input("Continue? (Y/n): ")
        if user_input == "Y" or user_input == "y":
            print("Continuing...")
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
    # global dir_format
    # dir_format = "\""  + dir_path[:-1] + "\"" + '/'
    # global swf_format
    # swf_format = "\""  + dir_path[:-1] + "\"" + '/swf/'

def main():
    encoded_str = get_str(input('请输入网址：'))
    try:
        config = json.loads(decode(encoded_str))
    except:
        print("Can't read! Maybe keys were changed?")
        exit()
    # print(decode(encoded_str))
    # print(decode(config['pageInfo']))
    print("文档名：" + config['p_name'])
    print("上传日期：" + config['p_upload_date'])
    init(config)
    get_swf(config)
    convert(config['pageCount'])

def get_swf(config):
    url=get_url(config['p_code'],config['headerInfo'],1,config['p_swf'],config['pageInfo'],config['ebt_host'])
    file_path=dir_path + url[0][25:]
    print("Downloading PK...")
    download(url[0],file_path)
    for i in range(1,config['pageCount']+1):
        print("Downloading page " + str(i) + '...')
        url=get_url(config['p_code'],config['headerInfo'],i,config['p_swf'],config['pageInfo'],config['ebt_host'])
        file_path = dir_path  + url[1][25:]
        print(url[1])
        download(url[1],file_path)
        compressor.make(dir_path + url[0][25:],dir_path + url[1][25:],swf_path + str(i) + '.swf')
    print("Donload done. (total page: " + str(config['pageCount']) + ")")

def convert(pageCount):
    print("Now start converting...")
    print("!! Warnning: This process may uses very big memory(100MB-5GB), and much time. We will optimize it in future. !!")
    pdf=PdfWriter()
    def execute(num):
        os.system("java -jar ffdec/ffdec.jar -format frame:svg -select 1 -export frame " + r(svg_path) + " " + r(swf_path + str(num) + '.swf'))
        shutil.move(svg_path + '1.svg',svg_path + str(i) + '_.svg')
    for i in range(1,pageCount+1):
        print("Converting page " + str(i) + " to svg...")
        try:
            execute(i)
        except FileNotFoundError:
            os.system("java -jar ffdec/ffdec.jar -header -set frameCount 1 " + r(swf_path + str(i) + '.swf') + " " + r(swf_path + str(i) + '.swf'))
            execute(i)
        print("Converting svg to pdf...")
        cairosvg.svg2pdf(url=svg_path + str(i) + '_.svg',write_to=pdf_path + str(i) + '.pdf')
        pdf = append_pdf(pdf,pdf_path + str(i) + ".pdf")
    pdf.write(dir_path[:-1] + ".pdf")
    print("Saved file to " + dir_path[:-1] + ".pdf")

def clean():
    print("cleaning cache...")
    shutil.rmtree(swf_path)
    shutil.rmtree(pdf_path)
    shutil.rmtree(svg_path)

if __name__ == "__main__":
    check_ffdec()
    a=sys.argv
    if len(a) == 1:
        main()
        clean()
