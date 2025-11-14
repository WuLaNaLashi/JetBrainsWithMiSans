#!/usr/bin/env fontforge --lang=py -script

# -*- coding: utf-8 -*-

# 合并JetBrains Mono NF和MiSans字体的FontForge脚本
# 参考PlemolJP项目的方法

import math
import os
import shutil
import sys
import uuid
from decimal import ROUND_HALF_UP, Decimal

import fontforge
import psMat

# 配置参数
VERSION = "1.0.0"
FONT_NAME_BASE = "MiWithJBMono"
ZH_FONT_PATH = "MiSans/ttf/MiSans-{style}.ttf"
ENG_FONT_NL_PATH = "JetBrainsNF/NL_NF/JetBrainsMonoNLNerdFont-{style}.ttf"
ENG_FONT_LIGATURES_PATH = "JetBrainsNF/NF/JetBrainsMonoNerdFont-{style}.ttf"
SOURCE_FONTS_DIR = "."
BUILD_FONTS_DIR = "MiWithJBMonoNL"
VENDER_NAME = "MiJB"
EM_ASCENT = 800
EM_DESCENT = 200
OS2_ASCENT = 1020
OS2_DESCENT = 300
ITALIC_ANGLE = 9

COPYRIGHT = """[JetBrains Mono]
Copyright (c) 2020, JetBrains s.r.o.
https://www.jetbrains.com/lp/mono/

[MiSans]
Copyright (c) 2020, Xiaomi Inc.
https://www.mi.com/global/misans/

[Nerd Fonts]
Copyright (c) 2014, Ryan L McIntyre https://ryanlmcintyre.com

[MiWithJBMono]
Copyright (c) 2025, MiWithJBMono Project
"""

# 支持的字重列表 - 注意MiSans和JetBrains的字重名称差异
WEIGHTS = [
    {"zh": "Thin", "eng": "Thin", "output": "Thin"},
    {"zh": "ExtraLight", "eng": "ExtraLight", "output": "ExtraLight"},
    {"zh": "Light", "eng": "Light", "output": "Light"},
    {"zh": "Regular", "eng": "Regular", "output": "Regular"},
    {"zh": "Medium", "eng": "Medium", "output": "Medium"},
    {"zh": "Semibold", "eng": "SemiBold", "output": "SemiBold"},
    {"zh": "Bold", "eng": "Bold", "output": "Bold"},
]

# 斜体字重 - 只处理有对应斜体的字重
ITALIC_WEIGHTS = [
    {"zh": "Thin", "eng": "ThinItalic", "output": "ThinItalic"},
    {"zh": "ExtraLight", "eng": "ExtraLightItalic", "output": "ExtraLightItalic"},
    {"zh": "Light", "eng": "LightItalic", "output": "LightItalic"},
    {"zh": "Regular", "eng": "Italic", "output": "Italic"},
    {"zh": "Medium", "eng": "MediumItalic", "output": "MediumItalic"},
    {"zh": "Semibold", "eng": "SemiBoldItalic", "output": "SemiBoldItalic"},
    {"zh": "Bold", "eng": "BoldItalic", "output": "BoldItalic"},
]

def main():
    print("=== 开始合并字体 ===")
    
    # 确保构建目录存在
    if os.path.exists(BUILD_FONTS_DIR):
        shutil.rmtree(BUILD_FONTS_DIR)
    os.makedirs(BUILD_FONTS_DIR)
    
    # 生成不带连字的字体
    print("=== 生成不带连字的字体 ===")
    for weight in WEIGHTS:
        generate_font(
            zh_style=weight["zh"],
            eng_style=weight["eng"],
            output_style=weight["output"],
            eng_font_path=ENG_FONT_NL_PATH,
            font_suffix="NL"
        )
    
    # 生成带连字的字体
    print("=== 生成带连字的字体 ===")
    for weight in WEIGHTS:
        generate_font(
            zh_style=weight["zh"],
            eng_style=weight["eng"],
            output_style=weight["output"],
            eng_font_path=ENG_FONT_LIGATURES_PATH,
            font_suffix=""
        )
    
    # 生成斜体字体
    print("=== 生成斜体字体 ===")
    for weight in ITALIC_WEIGHTS:
        generate_font(
            zh_style=weight["zh"],
            eng_style=weight["eng"],
            output_style=weight["output"],
            eng_font_path=ENG_FONT_NL_PATH,
            font_suffix="NL"
        )
    
    for weight in ITALIC_WEIGHTS:
        generate_font(
            zh_style=weight["zh"],
            eng_style=weight["eng"],
            output_style=weight["output"],
            eng_font_path=ENG_FONT_LIGATURES_PATH,
            font_suffix=""
        )
    
    print("=== 字体合并完成 ===")

def generate_font(zh_style, eng_style, output_style, eng_font_path, font_suffix):
    print(f"=== 生成 {output_style} ===")
    
    # 打开字体文件
    zh_font, eng_font = open_fonts(zh_style, eng_style, eng_font_path)
    
    # 调整EM尺寸
    adjust_em(eng_font)
    adjust_em(zh_font)
    
    # 删除重复字符
    zh_font = delete_duplicate_glyphs(zh_font, eng_font)
    
    # 如果是斜体，转换中文字形
    if "Italic" in output_style:
        transform_italic_glyphs(zh_font)
    
    # 删除GPOS表
    remove_lookups(zh_font, remove_gsub=False, remove_gpos=True)
    
    # 编辑元数据
    cap_height = 730
    x_height =550
    
    font_name = f"{FONT_NAME_BASE}{font_suffix}"
    edit_meta_data(eng_font, output_style, font_name, cap_height, x_height)
    edit_meta_data(zh_font, output_style, font_name, cap_height, x_height)
    
    # 保存TTF文件
    eng_font.generate(f"{BUILD_FONTS_DIR}/{font_name}-{output_style}-eng.ttf")
    zh_font.generate(f"{BUILD_FONTS_DIR}/{font_name}-{output_style}-zh.ttf")
    
    # 关闭字体
    zh_font.close()
    eng_font.close()
    
    print(f"=== {output_style} 生成完成 ===")

def open_fonts(zh_style: str, eng_style: str, eng_font_path: str):
    """打开字体文件"""
    zh_font_path = ZH_FONT_PATH.replace("{style}", zh_style)
    eng_font_full_path = eng_font_path.replace("{style}", eng_style)
    
    print(f"加载中文字体: {zh_font_path}")
    print(f"加载英文字体: {eng_font_full_path}")
    
    zh_font = fontforge.open(zh_font_path)
    eng_font = fontforge.open(eng_font_full_path)
    
    # 解除字体引用
    for glyph in zh_font.glyphs():
        if glyph.isWorthOutputting():
            zh_font.selection.select(("more", None), glyph)
    zh_font.unlinkReferences()
    
    for glyph in eng_font.glyphs():
        if glyph.isWorthOutputting():
            eng_font.selection.select(("more", None), glyph)
    eng_font.unlinkReferences()
    
    zh_font.selection.none()
    eng_font.selection.none()
    
    return zh_font, eng_font

def adjust_em(font):
    """调整字体EM尺寸"""
    font.em = EM_ASCENT + EM_DESCENT

def delete_duplicate_glyphs(zh_font, eng_font):
    """删除重复的字形"""
    
    eng_font.selection.none()
    zh_font.selection.none()
    
    # 特殊符号使用中文字体
    try:
        if eng_font[0x00A5].isWorthOutputting():
            eng_font[0x00A5].clear()  # Yen Sign
    except:
        pass
    
    try:
        if eng_font[0x3000].isWorthOutputting():
            eng_font[0x3000].clear()  # 全角空格
    except:
        pass
    
    # 拉丁字符使用英文字体
    for glyph in zh_font.glyphs():
        if 0x0000 <= glyph.unicode <= 0x02AF:  # 基本拉丁字母和扩展
            if glyph.isWorthOutputting():
                glyph.clear()
        elif 0x1D00 <= glyph.unicode <= 0x1D7F:  # 音标扩展
            if glyph.isWorthOutputting():
                glyph.clear()
    
    # 删除重复的中文字符
    for glyph in zh_font.glyphs("encoding"):
        if glyph.isWorthOutputting() and glyph.unicode > 0:
            try:
                eng_font.selection.select(("more", "unicode"), glyph.unicode)
            except ValueError:
                continue
    
    # 删除英文字体中的重复字符
    for glyph in eng_font.selection.byGlyphs:
        zh_font.selection.select(("more", "unicode"), glyph.unicode)
    
    for glyph in zh_font.selection.byGlyphs:
        if glyph.isWorthOutputting():
            glyph.clear()
    
    zh_font.selection.none()
    eng_font.selection.none()
    
    return zh_font

def transform_italic_glyphs(font):
    """转换中文字体的斜体"""
    font.italicangle = -ITALIC_ANGLE
    
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            orig_width = glyph.width
            glyph.transform(psMat.skew(ITALIC_ANGLE * math.pi / 180))
            glyph.transform(psMat.translate(-30, 0))
            glyph.width = orig_width

def remove_lookups(font, remove_gsub=True, remove_gpos=True):
    """删除GSUB和GPOS表"""
    if remove_gsub:
        for lookup in font.gsub_lookups:
            font.removeLookup(lookup)
    if remove_gpos:
        for lookup in font.gpos_lookups:
            font.removeLookup(lookup)

def edit_meta_data(font, weight: str, font_name: str, cap_height: int, x_height: int):
    """编辑字体元数据"""
    font.ascent = EM_ASCENT
    font.descent = EM_DESCENT
    
    font.os2_winascent = OS2_ASCENT
    font.os2_windescent = OS2_DESCENT
    font.os2_typoascent = OS2_ASCENT
    font.os2_typodescent = -OS2_DESCENT
    font.os2_typolinegap = 0
    
    font.hhea_ascent = OS2_ASCENT
    font.hhea_descent = -OS2_DESCENT
    font.hhea_linegap = 0
    
    font.os2_xheight = x_height
    font.os2_capheight = cap_height
    
    # 设置字重
    if "Regular" == weight or "Italic" == weight:
        font.os2_weight = 400
    elif "Thin" in weight:
        font.os2_weight = 100
    elif "ExtraLight" in weight:
        font.os2_weight = 200
    elif "Light" in weight:
        font.os2_weight = 300
    elif "Medium" in weight:
        font.os2_weight = 500
    elif "SemiBold" in weight:
        font.os2_weight = 600
    elif "Bold" in weight:
        font.os2_weight = 700
    
    font.os2_vendor = VENDER_NAME


    # 修改后的设置字体名称逻辑：只使用基础字体名作为familyname
    font_family = font_name  # 这将是 MiWithJBMonoHalf 或 MiWithJBMonoHalfNL
    font_weight = weight
    
    # 统一设置 familyname 为基本字体名
    font.familyname = font_family
    
    # 其他名称设置保持不变
    if "BoldItalic" == weight:
        font_weight = font_weight.replace("Italic", " Italic")
    elif "Italic" in weight and "Bold" not in weight:
        font_weight = font_weight.replace("Italic", " Italic")
        
    font.appendSFNTName(0x409, 2, font_weight)
    font.fontname = f"{font_family}-{font_weight}".replace(" ", "")
    font.fullname = f"{font_family}-{font_weight}".replace(" ", "")
    font.weight = font_weight.split(" ")[0]
    
    # 对于非主要字重，添加Typographic Family和Subfamily名称
    if weight not in ["Regular", "Italic", "Bold", "BoldItalic"]:
        font.appendSFNTName(0x409, 16, font_family)
        font.appendSFNTName(0x409, 17, font_weight)
    
    # 设置字体名称
    # if "Regular" == weight or "Italic" == weight or "Bold" == weight or "BoldItalic" == weight:
    #     font_family = font_name
    #     font_weight = weight
    #     if weight == "BoldItalic":
    #         font_weight = font_weight.replace("Italic", " Italic")
    #     font.familyname = font_family
    #     font.appendSFNTName(0x409, 2, font_weight)
    #     font.fontname = f"{font_family}-{font_weight}".replace(" ", "")
    #     font.fullname = f"{font_family} {font_weight}"
    #     font.weight = font_weight.split(" ")[0]
    # else:
    #     font_family = font_name
    #     font_weight = weight
    #     if "Italic" in weight:
    #         font_weight = font_weight.replace("Italic", " Italic")
    #     font.familyname = f"{font_family} " + font_weight.split(" ")[0]
    #     if "Italic" in weight:
    #         font.appendSFNTName(0x409, 2, "Italic")
    #     else:
    #         font.appendSFNTName(0x409, 2, "Regular")
    #     font.fontname = f"{font_family}-{font_weight}".replace(" ", "")
    #     font.fullname = f"{font_family} {font_weight}"
    #     font.weight = font_weight.split(" ")[0]
    #     font.appendSFNTName(0x409, 16, font_family)
    #     font.appendSFNTName(0x409, 17, font_weight)
    
    # 设置版权信息
    font.sfnt_names = (
        ("English (US)", "License", """This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"""),
        ("English (US)", "License URL", "http://scripts.sil.org/OFL"),
        ("English (US)", "Version", VERSION),
        ("English (US)", "Copyright", COPYRIGHT),
    )

if __name__ == "__main__":
    main()