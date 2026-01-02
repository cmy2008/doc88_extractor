# 这是啥 WHAT IS THIS

## 简介 / Introduction

一个可以完整提取道客巴巴预览文档（非截图）的工具。  
A tool to extract and convert doc88 documents (non-screenshot).


## 特点 / Features

- 利用 [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) (以下简称 ffdec) 工具，几乎完美转换文档，保留原始文本、形状与图片。  
    Powered by [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler), this tool preserves original text, shapes, and images—almost identical to the source.
- 适用文档范围：几乎所有  
    It's available for almost all documents.
    
## 安装 / Installation

### Python

- 需要 Python 3.10 或更高版本。  
    Requires Python 3.10 or newer.

安装依赖：

```bash
pip3 install retrying pypdf requests
```

### Java

- 需要安装 Java 才能进行文档转换（推荐 Java 17）:
    <br>Requires Java (recommended: version 17):
    <br>[Microsoft Build of OpenJDK 17 for Windows x64](https://aka.ms/download-jdk/microsoft-jdk-17.0.14-windows-x64.msi)

### SVG 转换 / SVG Converting
- 若启用 swf2svg，程序将自动下载 swf2svg 以实现 SVG 到 PDF 的转换。若安装失败，可尝试从 [typst/svg2pdf](https://github.com/typst/svg2pdf) 编译。  
    If swf2svg is enabled, the tool will download swf2svg automatically to perform SVG-to-PDF conversion. if installation fails, try building it from [typst/svg2pdf](https://github.com/typst/svg2pdf).

- 支持平台 / support platform:  
    Windows (x86_64) / Linux (x86_64/arm64) / MacOS (x86_64/arm64) / Android (arm64)

## 如何使用 / How to Use

在程序目录下运行：

```bash
python3 main.py
```

- 控制台输入网址并回车。  
    Enter the URL in the console.
- 首次运行会生成配置文件，检测更新并下载 ffdec。  
    On first run, there will be a configuration file `config.json`, then check the updates and download the ffdec.


## 配置 / Configuration
### 说明 / Description
默认情况下配置在 `config.json` 文件中，主要说明如下：

| 键名 / Key         | 说明                                                              | Description                                                                   |
| ------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `proxy_url`        | Github 代理服务的 URL                                             | The URL of Github's proxy service.                                            |
| `check_update`     | 是否在启动时检查更新                                              | Always check updates on startup.                                              |
| `swf2svg`          | 是否先转换到 SVG 再转到 PDF                                       | Convert swf files to svg first.                                               |
| `svgfontface`      | （仅 swf2pdf 为 false 时有效）在 SVG 转换中是否转换字体来呈现文本 | Only works when swf2pdf is false; using font to show texts in SVG converting. |
| `clean`            | 是否保留中间文件                                                  | Keep intermediate files.                                                      |
| `get_more`         | 是否始终通过扫描获取页面                                          | Always via scanning to get pages.                                             |
| `path_replace`     | 是否在 Windows 下替换过长路径                                     | Replace long paths on Windows.                                                |
| `download_workers` | 下载文件的线程数                                                  | Number of threads for downloading files.                                      |
| `convert_workers`  | 转换文件的线程数                                                  | Number of threads for converting files.                                       |

### 注意事项 / Attention
- 使用 `swf2svg` 选项，也许会解决部分文档的字体形状问题（不能解决字体不全的问题，原始文件为了压缩大小，减去了未使用的字）
- 若启用 `svgfontface` 选项，由于 [typst/svg2pdf](https://github.com/typst/svg2pdf) 的缺陷，将无法转换字体，会自动替换为默认字体
- 若启用 `svgfontface` 选项，由于 [ffdec](https://github.com/jindrapetrik/jpexs-decompiler) 的缺陷，某些形状或文本会出现转换错误