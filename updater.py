from utils import *
import shutil
import os
import json
import subprocess

class Update:
    def __init__(self, cfg2: Config) -> None:
        self.cfg2 = cfg2
        self.docs_dir = self.cfg2.o_dir_path[0:-1] if self.cfg2.o_dir_path.endswith("/") else self.cfg2.o_dir_path
    
    def download_ffdec(self):
        ffdec_info = github_release("jindrapetrik/jpexs-decompiler",2)
        ffdec_url = cfg2.proxy_url + ffdec_info.download_url
        print("开始下载 ffdec...")
        print(
            "警告: 使用内置下载可能会非常慢，建议手动下载 ffdec 的压缩包，并将文件（确保包含 'ffdec.jar'）解压到 'ffdec' 目录中。"
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
        except:
            print(
                "下载出错! 请检查网络连接或修改配置中的 'proxy_url' 内容。如果仍然无法下载，请手动下载 ffdec 文件并提取到目录 ffdec 中。"
            )
            input()
            return False
        print("下载完成! 开始解压...")
        try:
            extractzip("ffdec/ffdec.zip", "ffdec/")
            os.remove("ffdec/ffdec.zip")
            print("解压完成!")
            return True
        except zipfile.BadZipFile:
            print(
                "解压失败! 链接可能已失效? 请尝试修改函数 'download_ffdec' 中的 'ffdec_url' 内容。"
            )
            input()
            return False

    def check_java(self):
        text="Java 不正常，请尝试重新安装 Java。"
        text2="Java 未找到! 请安装 Java 并将其添加到 PATH 或 JAVA_HOME 中。"
        try:
            output = subprocess.run(['java', '-version'], capture_output=True, text=True)
            if output.returncode != 0:
                print(text)
                return False
            return True
        except FileNotFoundError:
            platform = os.name
            if platform == "nt":
                java_home = os.environ.get("JAVA_HOME", "")
                if java_home:
                    java_path = os.path.join(java_home, "bin", "java.exe")
                    if os.path.isfile(java_path):
                        os.environ["PATH"] = os.pathsep.join([os.path.join(java_home, "bin"), os.environ.get("PATH", "")])
                        try:
                            if subprocess.run(['java', '-version'],capture_output=True).returncode == 0:
                                print("警告: Java 未配置到 PATH 中，但在 JAVA_HOME 中找到了，建议将其添加到 PATH 中。")
                                return True
                            else:
                                print(text)
                                return False
                        except FileNotFoundError:
                            print(text2)
                            return False
                    else:
                        print(text2)
                        return False
            else:
                print(text2)
                return False
    def ffdec_update(self):
        if os.path.isfile("ffdec/ffdec.jar"):
            if choose("是否删除旧版本ffdec，否则创建备份？ (Y: 删除, N: 备份): "):
                try:
                        shutil.rmtree("ffdec")
                except Exception as e:
                    print(f"Error occurred while removing old version: {e}")
            else:
                try:
                    name=self.cfg2.ffdec_version
                    for i in range(1,100):
                        if os.path.isdir(f"ffdec_{name}") or os.path.isdir(f"ffdec_{name}_{i}"):
                            name=f"{name}_{i+1}"
                            break
                    shutil.move("ffdec", f"ffdec_{name}")
                except Exception as e:
                    print(f"Error occurred while updating old version: {e}")
        return self.download_ffdec()

    def upgrade(self):
        if self.cfg2.version < "1.7":
            print("检测到旧版本资源文件，正在更新...")
            self.resource_update()
        self.cfg2.version = self.cfg2.default_config["version"]
        self.cfg2.save()
    
    def resource_update(self):
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
                        shutil.move(os.path.join(subdir, file), os.path.join(new_dir, file))
                    shutil.rmtree(subdir)
                except Exception as e:
                    print(f"资源文件迁移失败: {subdir} -> {e}")
        self.gen_indexs()

    def gen_indexs(self):
        indexs = {}
        for name in os.listdir(self.docs_dir):
            subdir = os.path.join(self.docs_dir, name)
            index_path = os.path.join(subdir, "index.json")
            if os.path.isdir(subdir) and os.path.isfile(index_path):
                try:
                    with open(index_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    indexs[data["p_code"]] = data["p_name"]
                except Exception as e:
                    print(f"资源文件索引生成失败: {subdir} -> {e}")
        with open(os.path.join(self.docs_dir, "indexs.json"), "w", encoding="utf-8") as f:
            json.dump(indexs, f, ensure_ascii=False, indent=2)

    def check_update(self):
        try:
            main_info = github_release("cmy2008/doc88_extractor")
            if main_info.latest_version.lstrip("V") > self.cfg2.default_config["version"]:
                print(f"主程序检测到新版本 {main_info.latest_version}，下载连接：\n{main_info.download_url}")
            return True
        except Exception as e:
            print(f"Error occurred while checking for project updates: {e}")
            return False
    
    def check_ffdec_update(self):
        try:
            ffdec_info = github_release("jindrapetrik/jpexs-decompiler",2)
            if ffdec_info.latest_version != self.cfg2.ffdec_version and os.path.isfile("ffdec/ffdec.jar") and self.cfg2.check_update:
                if not choose(f"当前 ffdec 版本 {self.cfg2.ffdec_version}, 检测到新版本(文件名：{ffdec_info.name})，是否更新？ (Y/n): "):
                    return False
            if ffdec_info.latest_version == self.cfg2.ffdec_version and os.path.isfile("ffdec/ffdec.jar"):
                return False
            if not self.ffdec_update() and not os.path.isfile("ffdec/ffdec.jar"):
                exit()
            self.cfg2.ffdec_version = ffdec_info.latest_version
            self.cfg2.save()
            return True
        except Exception as e:
            print(f"Error occurred while checking ffdec updates: {e}")
            return False