# -*- coding: utf-8 -*-
"""DOC88 文档提取工具 — 主入口模块。

功能流程：
  输入 URL/ID/m_main 数据 → 下载 SWF 资源 → 转换为 PDF（可选 SVG 中转）。
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfWriter, errors
from coder import decode, encode
from compressor import make_swf
from config import Config, cfg2
from ebt_import import build_cfg, import_ebt
from gen_cfg import GenConfig
from get_more import GetMore
from updater import Update
from utils import (
    choose,
    download,
    get_request,
    input_break,
    logw,
    ospath,
    read_file,
    special_path,
    write_file,
    writes_file,
)

# ---------------------------------------------------------------------------
# 模块级调试开关
# ---------------------------------------------------------------------------
_DEBUG: bool = False


# ---------------------------------------------------------------------------
# 数据解码
# ---------------------------------------------------------------------------

def decode_data(encode_data: str) -> dict:
    """解码 m_main.init 中的加密数据为配置字典。"""
    try:
        return json.loads(decode(encode_data))
    except json.decoder.JSONDecodeError:
        raise Exception("Can't read data!")
    except (ValueError, UnicodeDecodeError):
        raise Exception("Can't read data! Maybe keys were changed?")


# ---------------------------------------------------------------------------
# URL 解析
# ---------------------------------------------------------------------------

def get_main_from_url(url: str) -> dict | bool:
    """从 doc88 页面 URL 提取文档配置数据。

    Returns:
        配置字典，或 False（WAF 检测且用户拒绝使用 CDN）。
    """
    if url.find("doc88.com/p-") == -1 and url.find("doc88.piglin.eu.org/p-") == -1:
        raise Exception("Invalid URL!")

    request = get_request(url, referer=True, cffi=True)
    if request.status_code == 404:
        raise Exception("404 Not found!")

    content = request.text
    data = re.search(r'm_main\.init\(".*"\);', content)
    if data is None:
        if re.search("网络环境安全验证", content):
            print("WAF detected!")
            if choose("Do you want to use CDN?(Y/n): "):
                url = url.replace("www.doc88.com", "doc88.piglin.eu.org")
                return get_main_from_url(url)
            return False
        raise Exception("Can't find data in this page! Please try another.")

    c = data.span()
    encode_data = content[c[0] + 13 : c[1] - 3]
    return decode_data(encode_data)


# ---------------------------------------------------------------------------
# PDF 拼接
# ---------------------------------------------------------------------------

def append_pdf(pdf: PdfWriter, file: str) -> PdfWriter:
    """向 PdfWriter 追加一个 PDF 文件页。

    自动跳过损坏/空文件并记录日志。
    """
    if isinstance(file, str) and os.path.exists(file) and os.path.getsize(file) > 0:
        try:
            pdf.append(ospath(file))
            return pdf
        except errors.EmptyFileError:
            print(f"跳过损坏的文件: {file}")
            logw(f"跳过损坏的文件: {file}")
    else:
        print(f"跳过不存在或为空的文件: {file}")
        logw(f"跳过不存在或为空的文件: {file}")
    return pdf


# ---------------------------------------------------------------------------
# 初始化
# ---------------------------------------------------------------------------

def init(config: dict) -> None:
    """根据文档配置初始化输出目录结构。"""
    cfg2.dir_path = cfg2.o_dir_path + config["p_code"] + "/"
    cfg2.swf_path = cfg2.dir_path + cfg2.o_swf_path
    cfg2.svg_path = cfg2.dir_path + cfg2.o_svg_path
    cfg2.pdf_path = cfg2.dir_path + cfg2.o_pdf_path

    try:
        os.makedirs(ospath(cfg2.dir_path))
    except FileExistsError:
        if not choose("exists"):
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
    except FileExistsError:
        pass


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(config: dict, more: bool = False, initial: bool = True) -> bool:
    """文档提取主流程。

    Args:
        config: 文档配置字典。
        more: 是否尝试扫描额外页面。
        initial: 是否首次调用（需要初始化目录）。

    Returns:
        提取是否成功。
    """
    if initial:
        init(config)

    cfg = GenConfig(config)
    if os.path.exists(ospath(f"{cfg2.dir_path}index.json")):
        cfg = GenConfig(json.loads(read_file(f"{cfg2.dir_path}index.json")))

    print(f"文档名：{cfg.p_name}")
    print(f"文档 ID：{cfg.p_code}")
    print(f"上传日期：{cfg.p_date}")
    print(f"页数：{cfg.p_pagecount}")

    if int(cfg.p_pagecount) != cfg.p_count:
        more = True
        print(f"可预览页数：{cfg.p_count_info}")
        print(f"可直接获取页数：{cfg.p_count}")
        print("可能有额外页面（需扫描）！")

    if not choose("开始提取？ (Y/n): "):
        return False

    # 免费文档直接下载
    if cfg.p_download == "1":
        print("该文档为免费文档，可直接下载！")
        if choose("down"):
            try:
                doc_format = (
                    "zip" if config.get("if_zip", 0) != 0
                    else str.lower(cfg.p_doc_format)
                )
                file_path = "docs/" + cfg.p_name + "." + doc_format
                download(
                    get_request(
                        "https://www.doc88.com/doc.php?act=download&pcode="
                        + cfg.p_code,
                        referer=True,
                        cffi=True,
                    ).text,
                    file_path,
                )
                print("Saved file to " + file_path)
                return True
            except Exception as err:
                print("Download error: " + str(err))
                logw("Download error: " + str(err))
        else:
            print("Continuing...")

    # 额外页面扫描
    if more:
        if choose("即将通过扫描获取页面，是否继续（否则正常下载）？ (Y/n): "):
            print("尝试通过扫描获取页面...")
            newpageids: list[str] = []
            cfg.p_count = 0
            for i in range(1, cfg.ph_nums() + 1):
                getter = GetMore(cfg, i, cfg2.dir_path, cfg.p_count)
                getter.start()
                newpageids += getter.newpageids
                cfg.p_count += len(getter.newpageids)
                del getter
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
        if not _DEBUG:
            convert(cfg)
            del cfg
        return True
    except Exception as err:
        print(err)
        return False


# ---------------------------------------------------------------------------
# SWF 下载器
# ---------------------------------------------------------------------------

class Downloader:
    """并发下载 PH/PK 文件并合成为 SWF。"""

    def __init__(self, cfg: GenConfig) -> None:
        self.cfg = cfg
        self.downloaded = True
        self.progressfile = cfg2.dir_path + "progress.json"
        if os.path.isfile(ospath(self.progressfile)):
            self._read_progress()
        else:
            self.progress: dict[str, list[int]] = {"pk": [], "ph": []}

    def _read_progress(self) -> None:
        try:
            self.progress = json.loads(read_file(self.progressfile))
        except json.decoder.JSONDecodeError:
            self.progress = {"pk": [], "ph": []}

    def save_progress(self, ptype: str, page: int) -> None:
        self.progress[ptype].append(page)
        writes_file(json.dumps(self.progress), self.progressfile)

    def download_ph(self, i: int) -> None:
        """下载单个 PH 文件。"""
        url = self.cfg.ph(i)
        print(f"Downloading PH {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["ph"]:
            print("Using Cache...")
            return
        try:
            download(url.url, file_path)
            self.save_progress("ph", i)
        except Exception as e:
            logw(f"Download PH {i} error: {e}")
            self.downloaded = False

    def download_pk(self, i: int) -> None:
        """下载单个 PK 文件。"""
        url = self.cfg.pk(i)
        print(f"Downloading page {i}: \n{url.url}")
        file_path = cfg2.dir_path + url.name
        if i in self.progress["pk"]:
            print("Using Cache...")
            return
        try:
            download(url.url, file_path)
            self.save_progress("pk", i)
        except Exception as e:
            logw(f"Download page {i} error: {e}")
            self.downloaded = False

    def make_swf(self, i: int) -> None:
        """将 PH+PK 合成为 SWF。"""
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


def get_swf(cfg: GenConfig) -> None:
    """并发下载并合成所有页面的 SWF 文件。"""
    max_workers = cfg2.download_workers
    down = Downloader(cfg)

    print("Downloading PH...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.ph_nums() + 1):
            executor.submit(down.download_ph, i)

    print("Downloading PK...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.download_pk, i)

    if not down.downloaded:
        raise Exception("Download error")

    print("Making pages...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i in range(1, cfg.p_count + 1):
            executor.submit(down.make_swf, i)

    print(f"Download done. (total page: {cfg.p_count})")


# ---------------------------------------------------------------------------
# 格式转换器 (SWF → SVG/PDF)
# ---------------------------------------------------------------------------

class Converter:
    """SWF → SVG/PDF 转换器。

    通过 ffdec (Java) 将 SWF 转为 SVG 或 PDF 帧，最终合并为单个 PDF。
    """

    def __init__(self, config: Config) -> None:
        self.cfg2 = config
        self.pdf = PdfWriter()
        self.pdflist: list[str] = []

    # -- SWF 帧画布修正 --

    def fix_displayrect(self, i: int, w: str, h: str) -> None:
        """修正 SWF 帧的 displayRect 宽高。"""
        subprocess.run(
            [
                "java", "-jar", "ffdec/ffdec.jar",
                "-header",
                "-set", "width", f"{w}px",
                "-set", "height", f"{h}px",
                f"{self.cfg2.swf_path}{i}.swf",
                f"{self.cfg2.swf_path}{i}.swf",
            ],
            capture_output=True,
            text=True,
        )

    # -- SWF 分组 --

    def divide_swfs(self, count: int) -> None:
        """将 SWF 文件按工作线程数均匀分配到子目录。"""
        swf_path = ospath(self.cfg2.swf_path)
        file_index = os.listdir(swf_path)
        swf_files = sorted(
            [f for f in file_index if f.endswith(".swf")],
            key=lambda x: int(x[:-4]),
        )
        for idx, swf_file in enumerate(swf_files):
            group_num = idx % count
            group_path = ospath(f"{self.cfg2.swf_path}{group_num}/")
            try:
                os.makedirs(group_path)
            except FileExistsError:
                pass
            shutil.copy(
                os.path.join(swf_path, swf_file),
                os.path.join(group_path, swf_file),
            )

    # -- SWF → SVG --

    def swf2svg(self, group_id: int) -> None:
        """将分组内的 SWF 转为 SVG 帧。"""
        swf_dir = ospath(f"{self.cfg2.swf_path}{group_id}")
        if os.listdir(swf_dir) == []:
            return
        print(f"SWF -> SVG converting worker {group_id} started.")
        log = ""
        try:
            dirpath = self.cfg2.svg_path + str(group_id) + "/"
            run = subprocess.run(
                [
                    "java", "-jar", "ffdec/ffdec.jar",
                    "-format", "frame:svg",
                    "-select", "1",
                    "-export", "frame", dirpath,
                    f"{self.cfg2.swf_path}{group_id}",
                ],
                capture_output=True,
                text=True,
            )
            log = run.stdout
            if run.returncode != 0:
                logw("SVG converting error: " + (run.stderr or run.stdout))

            # 移动输出文件
            for f in os.listdir(ospath(dirpath)):
                if os.path.isdir(ospath(f"{dirpath}{f}")):
                    shutil.move(
                        ospath(f"{dirpath}{f}/1.svg"),
                        ospath(f"{self.cfg2.svg_path}{f[:-4]}.svg"),
                    )
            # 清理 ffdec 临时目录
            _safe_rmtree(ospath(dirpath))
            # 删除分组文件夹
            _safe_rmtree(ospath(swf_dir))
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")
            logw("SVG converting error: " + log)

    # -- SWF → PDF --

    def swf2pdf(self, group_id: int) -> None:
        """将分组内的 SWF 直接转为 PDF 帧。"""
        swf_dir = ospath(f"{self.cfg2.swf_path}{group_id}")
        if os.listdir(swf_dir) == []:
            return
        print(f"SWF -> PDF converting worker {group_id} started.")
        log = ""
        try:
            dirpath = self.cfg2.pdf_path + str(group_id) + "/"
            run = subprocess.run(
                [
                    "java", "-jar", "ffdec/ffdec.jar",
                    "-format", "frame:pdf",
                    "-zoom", str(self.cfg2.pdf_scale),
                    "-select", "1",
                    "-export", "frame", dirpath,
                    f"{self.cfg2.swf_path}{group_id}",
                ],
                capture_output=True,
                text=True,
            )
            log = run.stdout
            if run.returncode != 0:
                logw("PDF converting error: " + (run.stderr or run.stdout))

            for f in os.listdir(ospath(dirpath)):
                if os.path.isdir(ospath(f"{dirpath}{f}")):
                    shutil.move(
                        ospath(f"{dirpath}{f}/frames.pdf"),
                        ospath(f"{self.cfg2.pdf_path}{f[:-4]}.pdf"),
                    )
                    self.pdflist.append(f[:-4])
            _safe_rmtree(ospath(dirpath))
            _safe_rmtree(ospath(swf_dir))
        except FileNotFoundError:
            print("Can't convert this page! Skipping...")
            logw("PDF converting error: " + log)

    # -- SVG → PDF --

    def svg2pdf(self, i: int) -> None:
        """将单页 SVG 转为 PDF。"""
        try:
            print(f"Converting page {i} to pdf...")
            subprocess.run(
                [
                    "./svg2pdf",
                    f"{self.cfg2.svg_path}{i}.svg",
                    f"{self.cfg2.pdf_path}{i}.pdf",
                ],
                text=True,
                capture_output=True,
            )
            self.pdflist.append(str(i))
        except FileNotFoundError as e:
            print("Can't convert this page! Skipping...")
            logw(f"SVG to PDF converting error: {e}")

    # -- 合并 PDF --

    def makepdf(self) -> None:
        """合并所有单页 PDF 为最终文档。"""
        self.pdflist = sorted(self.pdflist, key=lambda x: int(x))
        for i in self.pdflist:
            self.pdf = append_pdf(
                self.pdf,
                str(ospath(f"{self.cfg2.pdf_path}{i}.pdf")),
            )
            if not self.cfg2.swf2svg:
                self.pdf.pages[-1].scale_by(1 / self.cfg2.pdf_scale)


def _safe_rmtree(path: str) -> None:
    """安全删除目录（忽略权限错误和文件不存在）。"""
    try:
        shutil.rmtree(path)
    except PermissionError:
        print("Can't delete temporary folder, maybe file is opened?")
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# 转换调度
# ---------------------------------------------------------------------------

def convert(cfg: GenConfig) -> None:
    """协调多线程 SWF → PDF 转换流程。"""
    print("开始转换...")
    if cfg2.swf2svg:
        print(
            "!! 警告: 此过程可能会使用较高的 CPU 使用率。"
            "您可以在配置文件中修改线程数以平衡性能 !!"
        )
    else:
        print(
            "!! 警告: 此过程可能会使用较高的 CPU 使用率，以及较长的时间。"
            "您可以在配置文件中修改线程数以平衡性能 !!"
        )

    max_workers = cfg2.convert_workers
    doc = Converter(cfg2)

    # 修正 SWF 帧画布大小
    if cfg2.fix_displayrect:
        print("Now start fixing swf displayrect, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(1, cfg.p_count + 1):
                parts = cfg.pageids[i - 1].split("-")
                executor.submit(doc.fix_displayrect, i, parts[1], parts[2])

    doc.divide_swfs(cfg2.convert_workers)

    if not cfg2.swf2svg:
        print("Now start SWF -> PDF converting, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(max_workers):
                executor.submit(doc.swf2pdf, i)
    else:
        print("Now start SWF -> SVG converting, please wait...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(max_workers):
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
        "Tip: 在 Edge 中查看文档可能会无法正常显示文本，"
        "但您也可以使用其他阅读器，例如 Chrome。"
    )


# ---------------------------------------------------------------------------
# 清理
# ---------------------------------------------------------------------------

def clean(config: Config) -> None:
    """清理文档处理过程中产生的缓存和临时文件。"""
    print("正在清理缓存...")
    shutil.rmtree(ospath(config.swf_path))
    shutil.rmtree(ospath(config.pdf_path))
    shutil.rmtree(ospath(config.svg_path))
    for i in os.listdir(ospath(config.dir_path)):
        if i.endswith(".ebt") or i == "progress.json":
            os.remove(ospath(config.dir_path + i))


# ---------------------------------------------------------------------------
# 交互模式
# ---------------------------------------------------------------------------

class Mode:
    """命令行交互模式路由器。

    根据用户输入的类型（URL/ID/路径/m_main数据）分发到对应的处理流程。
    """

    def cli(self) -> bool:
        """读取用户输入并路由到对应的处理方法。"""
        try:
            user_input = input("请输入：").strip()
        except KeyboardInterrupt:
            exit()

        if user_input.startswith("http"):
            return self._from_url(user_input)
        if user_input.isdigit():
            return self._from_pcode(user_input)
        if os.path.isfile(ospath(user_input)):
            if user_input.endswith(".xdf"):
                return self._from_dirs(user_input)
            print("错误的文件类型！")
            return False
        if os.path.isdir(ospath(user_input)):
            try:
                if any(f.endswith(".ebt") for f in os.listdir(ospath(user_input))):
                    return self._from_dirs(user_input)
                print("该文件夹内没有ebt文件！")
                return False
            except PermissionError:
                print("无权访问该文件夹！")
                return False

        # 尝试作为 m_main 数据解码
        try:
            config = decode_data(user_input)
            main(config, cfg2.get_more)
            return True
        except Exception:
            print("无效输入！")
            return False

    @staticmethod
    def _from_url(url: str) -> bool:
        try:
            return main(get_main_from_url(url), cfg2.get_more)
        except Exception as err:
            print(err)
            return False

    @staticmethod
    def _from_pcode(p_code: str) -> bool:
        try:
            return Mode._from_url(
                f"https://www.doc88.com/p-{p_code}.html"
            )
        except Exception as err:
            print(err)
            return False

    @staticmethod
    def _from_dirs(dir_path: str) -> bool:
        """从本地 EBT 文件目录导入文档。"""
        try:
            ebts = import_ebt(dir_path)
            config = build_cfg(*ebts)
            cfg = GenConfig(config)
            init(config)
            # 复制文件到对应目录并生成下载缓存
            progress = Downloader(cfg)
            for ph in ebts[0]:
                shutil.copy(ospath(ph["path"]), ospath(cfg2.dir_path))
                progress.save_progress("ph", ph["level"])
            for pk in ebts[1]:
                shutil.copy(ospath(pk["path"]), ospath(cfg2.dir_path))
                progress.save_progress("pk", pk["page"])
            return main(config, cfg2.get_more, initial=False)
        except Exception as err:
            print(err)
            return False


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(
        f"DOC88 （预览）文档提取工具 V{cfg2.default_config['version']}"
    )
    print("by: Cuite_Piglin")
    print(
        "\n免责声明： 仅供学习或交流用，请在 24 小时内删除本程序，"
        "严禁用于任何商业或非法用途，使用该工具而产生的任何法律后果，"
        "用户需自行承担全部责任\n"
    )

    # 初始化更新管理器
    update = Update(cfg2)
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
        print(
            "请尝试：\n"
            "1. 检查 Java 是否正常并使用了推荐版本\n"
            "2. 检查 ffdec 是否安装正确且能正常运行"
        )
        if os.name == "nt":
            print(
                "3. 删除 ffdec 的配置文件"
                "（通常在 %APPDATA%\\JPEXS\\FFDec\\config.toml）后重试"
            )
        else:
            print("3. 删除 ffdec 的配置文件后重试")
        input_break()
        exit()

    # SVG 转 PDF 工具链
    if cfg2.swf2svg:
        print(
            "使用 SVG 转换功能建议同时关闭 font-face 功能，"
            "否则将会导致字体丢失，若只需要 SVG 文件可关闭清理功能，"
            "文件将会生成到对应文档 ID 目录下的 svg 目录"
        )
        if not update.check_svg2pdf():
            print("svg2pdf 工具安装失败，将继续以 SWF 到 PDF 方式转换。")
            cfg2.swf2svg = False

    # 调试模式
    _DEBUG = "--debug" in sys.argv

    # 交互主循环
    print("支持输入网址/文档ID/含有ebt文件的文件夹路径/m_main数据")
    print("注：浏览器控制台输入以下代码并回车即可一键复制m_main数据")
    print(
        "(match = document.documentElement.outerHTML.match("
        "/m_main\\.init\\(\"([^\"]*)\"\\);/)) ? "
        "(copy(match[1]), console.log('复制成功')) : "
        "console.log('未找到')"
    )
    print(
        "输入示例：\n"
        "网址：https://www.doc88.com/p-12345678.html\n"
        "文档ID：12345678\n"
        "含有ebt文件的文件夹路径：./ebtfiles/\n"
        "m_main数据：eyJwX2NvZGVz..."
    )

    user = Mode()
    while True:
        if user.cli():
            if cfg2.clean:
                try:
                    clean(cfg2)
                except NameError:
                    pass
            if not choose():
                exit()
