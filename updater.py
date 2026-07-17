# -*- coding: utf-8 -*-
"""更新与工具链管理模块。

负责检查 Java 环境、下载/更新 ffdec 和 svg2pdf、配置文件迁移等。
"""

import json
import os
import platform
import re
import shutil
import subprocess
import zipfile

from config import Config
from utils import (
    GitHubRelease,
    choose,
    download,
    extract,
    input_break,
    logw,
    ospath,
)


class Update:
    """应用程序更新及工具链管理器。"""

    def __init__(self, config: Config) -> None:
        self.cfg2 = config
        self.docs_dir = os.path.normpath(self.cfg2.o_dir_path)

    # ------------------------------------------------------------------
    # ffdec 相关
    # ------------------------------------------------------------------

    def get_ffdec_asset(self) -> tuple[GitHubRelease, str | None]:
        """获取 ffdec 最新 release 和匹配的 zip 资源名。

        Returns:
            (GitHubRelease, asset_name) — asset_name 可能为 None。
        """
        rel = GitHubRelease(self.cfg2.ffdec_repo)
        version = rel.latest_version.lstrip("v").lstrip("V")
        releases = rel.releases
        desired_name = f"ffdec_{version}.zip"

        if desired_name in releases:
            return rel, desired_name

        # 按版本号降序查找最佳匹配
        candidates = []
        for name in releases:
            m = re.match(r'^ffdec_(\d+\.\d+\.\d+)\.zip$', name)
            if m:
                candidates.append((name, m.group(1)))
        if candidates:
            candidates.sort(
                key=lambda x: tuple(int(y) for y in x[1].split(".")),
                reverse=True,
            )
            return rel, candidates[0][0]

        return rel, None

    def download_ffdec(self) -> bool:
        """下载并解压 ffdec 工具。"""
        try:
            rel, asset_name = self.get_ffdec_asset()
        except Exception as e:
            print(f"获取 ffdec 版本信息时出错: {e.__class__.__name__}: {e}")
            return False

        if not asset_name:
            print("未找到匹配的 ffdec zip 发行文件。")
            return False

        ffdec_url = self.cfg2.proxy_url + rel.releases[asset_name]
        print("开始下载 ffdec...")
        print(
            "警告: 使用内置下载可能会非常慢，建议手动下载 ffdec 的压缩包，"
            "并将文件（确保包含 'ffdec.jar'）解压到 'ffdec' 目录中。"
        )
        print("正在下载: " + ffdec_url)

        try:
            os.makedirs("ffdec")
        except FileExistsError:
            if choose("exists"):
                shutil.rmtree("ffdec")
                os.makedirs("ffdec")
                print("Continuing...")
            else:
                return False

        try:
            download(ffdec_url, "ffdec/ffdec.zip")
        except Exception:
            print(
                "下载出错! 请检查网络连接或修改配置中的 'proxy_url' 内容。"
                "如果仍然无法下载，请手动下载 ffdec 文件并提取到目录 ffdec 中。"
            )
            input_break()
            return False

        print("下载完成! 开始解压...")
        try:
            extract("ffdec/ffdec.zip", "ffdec/")
            os.remove("ffdec/ffdec.zip")
            print("解压完成!")
            return True
        except zipfile.BadZipFile:
            print(
                "解压失败! 链接可能已失效? 请尝试修改配置文件中 'ffdec_repo' 的内容。"
            )
            input_break()
            return False

    def ffdec_update(self) -> bool:
        """更新/重新下载 ffdec（保留或删除旧版本）。"""
        if os.path.isfile("ffdec/ffdec.jar"):
            if choose(
                "是否删除旧版本ffdec，否则创建备份？ (Y: 删除, N: 备份): "
            ):
                try:
                    shutil.rmtree("ffdec")
                except Exception as e:
                    print(f"Error occurred while removing old version: {e}")
            else:
                try:
                    name = self.cfg2.ffdec_version
                    for i in range(1, 100):
                        if os.path.isdir(f"ffdec_{name}") or os.path.isdir(
                            f"ffdec_{name}_{i}"
                        ):
                            name = f"{name}_{i + 1}"
                            break
                    shutil.move("ffdec", f"ffdec_{name}")
                except Exception as e:
                    print(f"Error occurred while updating old version: {e}")
        return self.download_ffdec()

    # ------------------------------------------------------------------
    # Java 环境
    # ------------------------------------------------------------------

    @staticmethod
    def check_java() -> bool:
        """检查 Java 是否可用。"""
        text = "Java 不正常，请尝试重新安装 Java。"
        text2 = "Java 未找到! 请安装 Java 并将其添加到 PATH 或 JAVA_HOME 中。"
        try:
            output = subprocess.run(
                ["java", "-version"], capture_output=True, text=True
            )
            if output.returncode != 0:
                print(text)
                return False
            return True
        except FileNotFoundError:
            if os.name == "nt":
                java_home = os.environ.get("JAVA_HOME", "")
                if java_home:
                    java_path = os.path.join(java_home, "bin", "java.exe")
                    if os.path.isfile(java_path):
                        os.environ["PATH"] = os.pathsep.join([
                            os.path.join(java_home, "bin"),
                            os.environ.get("PATH", ""),
                        ])
                        try:
                            result = subprocess.run(
                                ["java", "-version"], capture_output=True
                            )
                            if result.returncode == 0:
                                print(
                                    "警告: Java 未配置到 PATH 中，但在 JAVA_HOME 中找到了，建议将其添加到 PATH 中。"
                                )
                                return True
                            print(text)
                            return False
                        except FileNotFoundError:
                            print(text2)
                            return False
                    print(text2)
                    return False
                print(text2)
                return False
            print(text2)
            return False

    # ------------------------------------------------------------------
    # ffdec 配置
    # ------------------------------------------------------------------

    def ffdec_configure(self) -> bool:
        """配置 ffdec 的临时目录和 font-face 导出选项。"""
        # 配置临时目录
        if self.cfg2.replace_jna_tmp_path:
            jna_path = os.path.abspath(ospath("ffdec/jna_temp/"))
            if not os.path.exists(ospath("ffdec/jna_temp/")):
                try:
                    os.makedirs(ospath("ffdec/jna_temp/"))
                except FileNotFoundError:
                    print(
                        "Error when creating temporary folder for ffdec, "
                        "maybe permission denied?"
                    )
            try:
                subprocess.run(
                    [
                        "java", "-jar", "ffdec/ffdec.jar",
                        "-config", f"jnaTempDirectory={jna_path}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except Exception as err:
                logw(str(err))
                return False
        else:
            try:
                subprocess.run(
                    [
                        "java", "-jar", "ffdec/ffdec.jar",
                        "-config", 'jnaTempDirectory=""',
                    ],
                    capture_output=True,
                    text=True,
                )
            except Exception as err:
                logw(str(err))

        # 配置 font-face
        font_face_value = (
            "true" if self.cfg2.svgfontface else "false"
        )
        try:
            subprocess.run(
                [
                    "java", "-jar", "ffdec/ffdec.jar",
                    "-config",
                    f"textExportExportFontFace={font_face_value}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except Exception as err:
            logw(str(err))
            return False

        return True

    # ------------------------------------------------------------------
    # 主程序 / 资源更新
    # ------------------------------------------------------------------

    def check_update(self) -> bool:
        """检查主程序是否有新版本。"""
        try:
            main_info = GitHubRelease("cmy2008/doc88_extractor")
            if (
                main_info.latest_version.lstrip("V")
                > self.cfg2.default_config["version"]
            ):
                print(
                    f"主程序检测到新版本 {main_info.latest_version}，"
                    f"下载连接：\n{main_info.download_url}"
                )
            return True
        except Exception as e:
            print(f"检测主程序更新时出错: {e.__class__.__name__}: {e}")
            return False

    def check_ffdec_update(self) -> bool:
        """检查 ffdec 版本并在需要时更新。"""
        try:
            rel, asset_name = self.get_ffdec_asset()
            display_name = asset_name if asset_name else rel.latest_version
            if (
                rel.latest_version != self.cfg2.ffdec_version
                and os.path.isfile("ffdec/ffdec.jar")
                and self.cfg2.check_update
            ):
                if not choose(
                    f"当前 ffdec 版本 {self.cfg2.ffdec_version}, "
                    f"检测到新版本(文件名：{display_name})，是否更新？ (Y/n): "
                ):
                    return False
            if (
                rel.latest_version == self.cfg2.ffdec_version
                and os.path.isfile("ffdec/ffdec.jar")
            ):
                return False
            if not self.ffdec_update() and not os.path.isfile("ffdec/ffdec.jar"):
                exit()
            self.cfg2.ffdec_version = rel.latest_version
            self.cfg2.save()
            return True
        except Exception as e:
            print(f"检测 ffdec 更新时出错: {e.__class__.__name__}: {e}")
            if not os.path.isfile("ffdec/ffdec.jar"):
                print(
                    "请手动下载 ffdec 的压缩包，并将文件（确保包含 'ffdec.jar'）"
                    "解压到 'ffdec' 目录中：\n"
                    "https://github.com/jindrapetrik/jpexs-decompiler/releases"
                )
                input_break()
                exit()
            return False

    def upgrade(self) -> None:
        """执行版本升级和资源迁移。"""
        if self.cfg2.version < "1.7":
            print("检测到旧版本资源文件，正在更新...")
            self._resource_update()
        self._gen_indexes()
        self.cfg2.version = self.cfg2.default_config["version"]
        self.cfg2.save()

    def _resource_update(self) -> None:
        """将旧版资源目录结构迁移到新版（以 p_code 命名）。"""
        if not os.path.isdir(self.docs_dir):
            return
        for name in os.listdir(self.docs_dir):
            subdir = os.path.join(self.docs_dir, name)
            index_path = os.path.join(subdir, "index.json")
            if os.path.isdir(subdir) and os.path.isfile(index_path):
                try:
                    with open(index_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    p_code = data["p_code"]
                    new_dir = os.path.join(self.docs_dir, p_code)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    for file in os.listdir(subdir):
                        shutil.move(
                            os.path.join(subdir, file),
                            os.path.join(new_dir, file),
                        )
                    shutil.rmtree(subdir)
                except Exception as e:
                    print(f"资源文件迁移失败: {subdir} -> {e}")

    def _gen_indexes(self) -> None:
        """生成文档索引文件 indexs.json。"""
        indexes = {}
        if not os.path.isdir(self.docs_dir):
            os.makedirs(self.docs_dir)
        for name in os.listdir(self.docs_dir):
            subdir = os.path.join(self.docs_dir, name)
            index_path = os.path.join(subdir, "index.json")
            if os.path.isdir(subdir) and os.path.isfile(index_path):
                try:
                    with open(index_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    indexes[data["p_code"]] = data["p_name"]
                except Exception as e:
                    print(f"资源文件索引生成失败: {subdir} -> {e}")
        with open(
            os.path.join(self.docs_dir, "indexs.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(indexes, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 工具依赖管理（必需 / 可选）
    # ------------------------------------------------------------------

    @staticmethod
    def _tool_asset_name(tool_name: str) -> str | None:
        """返回当前平台对应的工具发行包文件名。"""
        sys_platform = platform.system()
        arch = platform.machine().lower()
        if sys_platform == "Windows":
            if "arm64" in arch or "aarch64" in arch:
                return f"{tool_name}-aarch64-pc-windows-msvc.zip"
            return f"{tool_name}-x86_64-pc-windows-msvc.zip"
        elif sys_platform == "Darwin":
            if "arm64" in arch or "aarch64" in arch:
                return f"{tool_name}-aarch64-apple-darwin.tar.gz"
            return f"{tool_name}-x86_64-apple-darwin.tar.gz"
        elif sys_platform == "Linux":
            if "arm64" in arch or "aarch64" in arch:
                return f"{tool_name}-aarch64-unknown-linux-musl.tar.gz"
            return f"{tool_name}-x86_64-unknown-linux-gnu.tar.gz"
        return None

    @staticmethod
    def _tool_binary_name(tool_name: str) -> str:
        """返回当前平台对应的工具可执行文件名。"""
        if os.name == "nt":
            return f"{tool_name}.exe"
        return tool_name

    def _download_tool(self, tool_name: str) -> bool:
        """下载并解压指定工具（不包含存在性检查）。"""
        try:
            info = GitHubRelease(getattr(self.cfg2, f"{tool_name}_repo"))
        except Exception as e:
            print(f"获取 {tool_name} 版本信息时出错: {e.__class__.__name__}: {e}")
            return False

        file_name = self._tool_asset_name(tool_name)
        if not file_name:
            print(
                f"当前操作系统或架构不受支持，请自行编译安装 {tool_name}：\n"
                f"https://github.com/cmy2008/{tool_name}"
            )
            return False

        tool_url = self.cfg2.proxy_url + info.releases[file_name]
        print(f"开始下载 {tool_name}...")
        print(f"正在下载: {tool_url}")

        try:
            download(tool_url, file_name)
        except Exception:
            print(
                f"下载出错! 请检查网络连接或修改配置文件中 'proxy_url' 的内容。"
                f"如果仍然无法下载，请手动下载 {tool_name} 。"
            )
            input_break()
            return False

        print("下载完成! 开始解压...")
        try:
            extract(file_name, ".")
            os.remove(file_name)
            print("解压完成!")
            return True
        except zipfile.BadZipFile:
            print(
                "解压失败! 链接可能已失效? 请尝试修改配置文件中 "
                f"'{tool_name}_repo' 的内容。"
            )
            input_break()
            return False

    def download_tool(self, tool_name: str) -> bool:
        """下载并解压指定工具（保留对外兼容接口）。"""
        return self._download_tool(tool_name)

    def check_required_tool(self, tool_name: str) -> bool:
        """检查必需工具，缺失则自动下载，下载失败返回 False。"""
        binary = self._tool_binary_name(tool_name)
        if os.path.isfile(binary):
            return True
        print(f"检测到必要工具 {tool_name} 未安装，正在自动下载...")
        if not self._download_tool(tool_name):
            print(f"自动下载 {tool_name} 失败，请检查网络连接后重试")
            return False
        return True

    # ------------------------------------------------------------------
    # 统一的启动工具链检查入口
    # ------------------------------------------------------------------

    def check_tools(self) -> bool:
        """统一检查并下载所有必需 / 可选工具。

        必需：Java 环境 + ffdec、presse
        可选：svg2pdf（仅在 swf2svg 模式下检查）
        """
        # ---- 必需：Java + ffdec ----
        if not self.check_java():
            input_break()
            return False

        should_check_ffdec = (
            self.cfg2.check_update or not os.path.isfile("ffdec/ffdec.jar")
        )
        if should_check_ffdec:
            self.check_ffdec_update()
        if self.cfg2.check_update:
            self.check_update()
        self.upgrade()

        if not self.ffdec_configure():
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
            return False

        # ---- 必需：presse ----
        if not self.check_required_tool("presse"):
            input_break()
            return False

        # ---- 可选：svg2pdf ----
        if self.cfg2.swf2svg:
            print(
                "使用 SVG 转换功能建议同时关闭 font-face 功能，"
                "否则将会导致字体丢失，若只需要 SVG 文件可关闭清理功能，"
                "文件将会生成到对应文档 ID 目录下的 svg 目录"
            )
            svg2pdf_bin = self._tool_binary_name("svg2pdf")
            if not os.path.isfile(svg2pdf_bin):
                if platform.system() in ("Windows", "Linux", "Darwin"):
                    if choose(
                        "检测到 svg2pdf 工具未下载，是否下载？ (Y/n): "
                    ):
                        if not self._download_tool("svg2pdf"):
                            print(
                                "svg2pdf 工具安装失败，"
                                "将继续以 SWF 到 PDF 方式转换。"
                            )
                            self.cfg2.swf2svg = False
                    else:
                        print(
                            "未下载 svg2pdf 工具，无法进行 SVG 转 PDF 操作。"
                        )
                        self.cfg2.swf2svg = False
                else:
                    self.cfg2.swf2svg = False

        return True

    def check_svg2pdf(self) -> bool:
        """检查 svg2pdf 工具是否就绪，必要时触发下载。"""
        if not self.cfg2.swf2svg:
            return True

        svg2pdf_name = self._tool_binary_name("svg2pdf")
        if not os.path.isfile(svg2pdf_name):
            if platform.system() in ("Windows", "Linux", "Darwin"):
                if choose(
                    "检测到 svg2pdf 工具未下载，是否下载？ (Y/n): "
                ):
                    return self._download_tool("svg2pdf")
                print("未下载 svg2pdf 工具，无法进行 SVG 转 PDF 操作。")
                return False
            return False
        return True
