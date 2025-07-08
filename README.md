# WHAT IS THIS
## Introduction
A tool make you download the doc88 documents.
## Features
NOT JUST IMAGE, IT HAS REAL SHAPES AND TEXTS, ALOMOST SAME AS ORIGINAL DOCUMENT.

# INSTALL

## Python
You need use python 3.10 or newer.
Just run:
```
pip3 install retrying pypdf requests
```

## Java
You need install Java(recommend version 17).

[Microsoft Build of OpenJDK 17 for Windows x64](https://aka.ms/download-jdk/microsoft-jdk-17.0.14-windows-x64.msi)

## SVG converting
If swf2svg is enable, you need install cairosvg:
```
pip3 install cairosvg
```
For Windows, you also need install GTK Runtime:
[GTK Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)

# HOW TO USE
```
python3 main.py
```

# CONFIGURATION
When you first run it, there will be a config.json:
```
swf2svg: If true, then swf files will be converted to svg first.
svgfontface: Only working when swf2pdf is false. If true, then the texts will be converted, but this will impact pdf converting causing a lot errors.
clean: If false, the swf,pdf,svg files wii be kept.
```