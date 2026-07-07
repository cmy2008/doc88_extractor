# -*- coding: utf-8 -*-
"""通用工具函数模块。

提供路径处理、HTTP 请求、文件读写、下载、解压等基础功能。
"""

import os
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Union

import requests
from curl_cffi import requests as requests_cffi
from retrying import retry

from config import cfg2


def ospath(path: str) -> Union[str, Path]:
    """处理 Windows 长路径（超过 260 字符时添加 \\\\?\\ 前缀）。"""
    if os.name == "nt" and cfg2.path_replace:
        fullpath = Path(path)
        if len(str(fullpath.absolute())) >= 260:
            return "\\\\?\\" + str(fullpath.absolute())
        return fullpath
    return path


def special_path(path: str) -> str:
    """替换文件名中的非法字符为全角字符。"""
    char_list = ["*", "|", ":", "?", "/", "<", ">", '"', "\\"]
    new_char_list = ["＊", "｜", "：", "？", "／", "＜", "＞", "＂", "＼"]
    for i in range(len(char_list)):
        path = path.replace(char_list[i], new_char_list[i])
    return path


def choose(text: str = "") -> bool:
    """询问用户是否继续（Y/n）。

    text 可以是预设键名（'exists', 'down'）或自定义提示文本。
    """
    if text == "exists":
        text = "The directory already exists!\nContinue? (Y/n): "
    elif text == "down":
        text = "是否下载，否则继续提取预览文档？ (Y/n): "
    elif text == "":
        text = "Continue? (Y/n): "
    try:
        user_input = input(text)
    except KeyboardInterrupt:
        exit()
    return user_input.lower() == "y"


def logw(t: str) -> None:
    """写入带时间戳的日志到 logs/ 目录。"""
    log = "[" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "]: " + t + "\n"
    log_dir = "logs/"
    dirc = log_dir + time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    with open(ospath(dirc), "a", encoding="utf-8") as file:
        file.write(log)


def get_request(
    url: str,
    referer: bool = True,
    cffi: bool = False,
    content_type: str = "text/html; charset=utf-8",
    stream: bool = False,
    timeout: int = 30,
) -> requests.Response:
    """发送 GET 请求，可选用 curl_cffi 模拟浏览器指纹。

    Args:
        url: 请求 URL。
        referer: 是否携带 Referer 头。
        cffi: 是否使用 curl_cffi 模拟 Edge 浏览器。
        content_type: Content-Type 头部的值。
        stream: 是否以流模式获取响应。
        timeout: 请求超时时间（秒）。
    Returns:
        requests.Response 或 curl_cffi 的 Response。
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
        ),
        "Content-Type": content_type,
        "Referer": "https://www.doc88.com/",
    }
    if not referer:
        headers.pop("Referer", None)
    if content_type == "":
        headers.pop("Content-Type", None)
    if cffi:
        return requests_cffi.get(
            url, headers=headers, impersonate="edge101", stream=stream, timeout=timeout
        )
    return requests.get(url, headers=headers, stream=stream, timeout=timeout)


def write_file(data: bytes, path: str) -> None:
    """以二进制模式写入文件。"""
    with open(ospath(path), "wb") as f:
        f.write(data)


def writes_file(data: str, path: str) -> None:
    """以文本模式写入文件。"""
    with open(ospath(path), "w", encoding="utf-8") as f:
        f.write(data)


def read_file(path: str) -> str:
    """以文本模式读取文件全部内容。"""
    with open(ospath(path), "r", encoding="utf-8") as file:
        return file.read()


def load_file(path: str) -> bytes:
    """以二进制模式读取文件全部内容。"""
    with open(ospath(path), "rb") as file:
        return file.read()


@retry(stop_max_attempt_number=3, wait_fixed=500)
def download(url: str, filepath: str) -> None:
    """下载文件（含重试机制）。"""
    write_file(get_request(url, referer=False).content, filepath)


def extract(file_path: str, topath: str) -> None:
    """解压 zip 或 tar.gz 文件到指定目录。"""
    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as f:
            f.extractall(topath)
    elif file_path.endswith(".tar.gz") or file_path.endswith(".tgz"):
        with tarfile.open(file_path, "r:*") as tar:
            tar.extractall(path=topath)
    else:
        raise ValueError("Unsupported archive format: " + file_path)


def input_break() -> None:
    """等待用户按回车后退出。"""
    try:
        input("按回车键退出...")
    except KeyboardInterrupt:
        exit()


class GitHubRelease:
    """从 GitHub API 获取最新 release 信息。"""

    def __init__(self, repo: str, n: int = -1) -> None:
        self.releases: dict[str, str] = {}
        version_info = get_request(
            f"https://api.github.com/repos/{repo}/releases/latest",
            referer=False,
        ).json()
        self.latest_version: str = version_info["tag_name"]
        if n != -1:
            self.download_url: str = version_info["assets"][n]["browser_download_url"]
            self.name: str = version_info["assets"][n]["name"]
        else:
            for i in range(len(version_info["assets"])):
                asset = version_info["assets"][i]
                self.releases[asset["name"]] = asset["browser_download_url"]
