# -*- coding: utf-8 -*-

import time
import os
import requests
import zipfile
import tarfile
import subprocess
from retrying import retry
from pathlib import Path
from config import *


def ospath(path):
    if os.name == "nt" and cfg2.path_replace:
        fullpath = Path(path)
        if len(str(fullpath.absolute())) >= 260:
            return "\\\\?\\" + str(fullpath.absolute())
        else:
            return fullpath
    else:
        return path


def special_path(path):
    char_list = ['*', '|', ':', '?', '/', '<', '>', '"', '\\']
    new_char_list = ['＊', '｜', '：', '？', '／', '＜', '＞', '＂', '＼']
    for i in range(len(char_list)):
        path = path.replace(char_list[i], new_char_list[i])
    return path


def choose(text=""):
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
    if user_input == "Y" or user_input == "y":
        return True
    else:
        return False


def logw(t: str):
    log = "[" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "]: " + t + "\n"
    log_dir = "logs/"
    dirc = log_dir + time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    with open(ospath(dirc), "a") as file:
        file.write(log)


def get_request(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39",
        "Content-Type": "text/html; charset=utf-8",
        "Referer": "https://www.doc88.com/",
    }
    return requests.get(url, headers=headers)


def write_file(data, path):
    with open(ospath(path), "wb") as f:
        f.write(data)


def writes_file(data, path):
    with open(ospath(path), "w") as f:
        f.write(data)


def read_file(path):
    with open(ospath(path), "r") as file:
        read = file.read()
        return read


def load_file(path):
    with open(ospath(path), "rb") as file:
        read = file.read()
        return read


@retry(stop_max_attempt_number=3, wait_fixed=500)
def download(url: str, filepath: str):
    write_file(requests.get(url).content, filepath)


def extract(file_path: str, topath: str):
    if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as f:
            f.extractall(topath)
    elif file_path.endswith(".tar.gz") or file_path.endswith(".tgz"):
        with tarfile.open(file_path, "r:*") as tar:
            tar.extractall(path=topath)
    else:
        raise ValueError("Unsupported archive format: " + file_path)


def input_break():
    try:
        input("按回车键退出...")
    except KeyboardInterrupt:
        exit()
class github_release:
    def __init__(self, repo: str, n: int = -1) -> None:
        self.releases = {}
        version_info = get_request(f"https://api.github.com/repos/{repo}/releases/latest").json()
        self.latest_version = version_info["tag_name"]
        if n != -1:
            self.download_url = version_info['assets'][n]['browser_download_url']
            self.name = version_info['assets'][n]['name']
        else:
            for i in range(len(version_info['assets'])):
                self.releases[version_info['assets'][i]['name']] = version_info['assets'][i]['browser_download_url']