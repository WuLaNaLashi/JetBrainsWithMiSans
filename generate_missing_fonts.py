#!/usr/bin/env fontforge --lang=py -script

# -*- coding: utf-8 -*-

# 专门生成缺失的NL字体字重

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
FONT_NAME_BASE = "MiWithJBMonoNL"
JP_FONT_PATH = "MiSans/ttf/MiSans-{style}.ttf"
ENG_FONT_NL_PATH = "JetBrainsNF/NL_NF/JetBrainsMonoNLNerdFont-{style}.ttf"
SOURCE_FONTS_DIR = "."
BUILD_FONTS_DIR = "MiWithJBMonoNL"
VENDER_NAME = "MiJB"
EM_ASCENT = 880
EM_DESCENT = 120
OS2_ASCENT = 880
OS2_DESCENT = 120
HALF_WIDTH_12 = 528
ITALIC_ANGLE = 10

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

def generate_font(jp_style, eng_style, output_style):
    print(f"=== 生成 {output_style} ===")
    
    # 打开字体文件
    jp_font, eng_font = open_fonts(jp_style, eng_style)
    
    # 调整EM尺寸
    adjust_em(eng_font)
    adjust_em(jp_font)
    
    # 删除重复字符
    jp_font = delete_duplicate_glyphs(jp_font, eng_font)
    
    # 调整一些字形
    adjust_some_glyph(jp_font, eng_font, output_style)
    
    # 转换半角宽度
    transform_half_width(jp_font, eng_font)
    
    # 删除GPOS表
    remove_lookups(jp_font, remove_gsub=False, remove_gpos=True)
    
    # 编辑元数据
    cap_height = int(
        Decimal(str(eng_font[0x0048].boundingBox()[3])).quantize(
            Decimal("0"), ROUND_HALF_UP
        )
    )
    x_height = int(
        Decimal(str(eng_font[0x0078].boundingBox()[3])).quantize(
            Decimal("0"), ROUND_HALF_UP
        )
    )
    
    edit_meta_data(eng_font, output_style, FONT_NAME_BASE, cap_height, x_height)
    edit_meta_data(jp_font, output_style, FONT_NAME_BASE, cap_height, x_height)
    
    # 保存TTF文件
    eng_font.generate(f"{BUILD_FONTS_DIR}/{FONT_NAME_BASE}-{output_style}-eng.ttf")
    jp_font.generate(f"{BUILD_FONTS_DIR}/{FONT_NAME_BASE}-{output_style}-jp.ttf")
    
    # 关闭字体
    jp_font.close()
    eng_font.close()
    
    print(f"=== {output_style} 生成完成 ===")

def open_fonts(jp_style: str, eng_style: str):
    """打开字体文件"""
    jp_font_path = JP_FONT_PATH.replace("{style}", jp_style)
    eng_font_full_path = ENG_FONT_NL_PATH.replace("{style}", eng_style)
    
    print(f"加载中文字体: {jp_font_path}")
    print(f"加载英文字体: {eng_font_full_path}")
    
    jp_font = fontforge.open(jp_font_path)
    eng_font = fontforge.open(eng_font_full_path)
    
    # 解除字体引用
    for glyph in jp_font.glyphs():
        if glyph.isWorthOutputting():
            jp_font.selection.select(("more", None), glyph)
    jp_font.unlinkReferences()
    
    for glyph in eng_font.glyphs():
        if glyph.isWorthOutputting():
            eng_font.selection.select(("more", None), glyph)
    eng_font.unlinkReferences()
    
    jp_font.selection.none()
    eng_font.selection.none()
    
    return jp_font, eng_font

def adjust_em(font):
    """调整字体EM尺寸"""
    font.em = EM_ASCENT + EM_DESCENT

def delete_duplicate_glyphs(jp_font, eng_font):
    """删除重复的字形"""
    
    eng_font.selection.none()
    jp_font.selection.none()
    
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
    for glyph in jp_font.glyphs():
        if 0x0000 <= glyph.unicode <= 0x02AF:  # 基本拉丁字母和扩展
            if glyph.isWorthOutputting():
                glyph.clear()
        elif 0x1D00 <= glyph.unicode <= 0x1D7F:  # 音标扩展
            if glyph.isWorthOutputting():
                glyph.clear()
    
    # 删除重复的中文字符
    for glyph in jp_font.glyphs("encoding"):
        if glyph.isWorthOutputting() and glyph.unicode > 0:
            try:
                eng_font.selection.select(("more", "unicode"), glyph.unicode)
            except ValueError:
                continue
    
    # 删除英文字体中的重复字符
    for glyph in eng_font.selection.byGlyphs:
        jp_font.selection.select(("more", "unicode"), glyph.unicode)
    
    for glyph in jp_font.selection.byGlyphs:
        if glyph.isWorthOutputting():
            glyph.clear()
    
    jp_font.selection.none()
    eng_font.selection.none()
    
    return jp_font

def adjust_some_glyph(jp_font, eng_font, style="Regular"):
    """调整一些字形"""
    try:
        if not eng_font[0x0020].isWorthOutputting():
            return
        eng_glyph_width = eng_font[0x0020].width
    except:
        return
    
    try:
        if not jp_font[0x3042].isWorthOutputting():
            return
        full_width = jp_font[0x3042].width
    except:
        return
    half_width = int(full_width / 2)
    
    # 调整引号
    try:
        eng_font.selection.select(("unicode", None), 0x0060)  # `
        eng_font.selection.select(("unicode", "more"), 0x0027)  # '
        eng_font.selection.select(("unicode", "more"), 0x0022)  # "
        
        for glyph in eng_font.selection.byGlyphs:
            glyph.transform(psMat.scale(1.1, 1.1))
            glyph.transform(psMat.translate((eng_glyph_width - glyph.width) / 2, 0))
            glyph.width = eng_glyph_width
    except:
        pass
    
    # 调整标点符号
    try:
        eng_font.selection.select(("unicode", None), 0x003A)  # :
        eng_font.selection.select(("unicode", "more"), 0x003B)  # ;
        eng_font.selection.select(("unicode", "more"), 0x002C)  # ,
        eng_font.selection.select(("unicode", "more"), 0x002E)  # .
        
        for glyph in eng_font.selection.byGlyphs:
            glyph.transform(psMat.scale(1.08, 1.08))
            glyph.transform(psMat.translate((eng_glyph_width - glyph.width) / 2, 0))
            glyph.width = eng_glyph_width
    except:
        pass
    
    # 调整全角标点
    try:
        for glyph_name in [0xFF08, 0xFF3B, 0xFF5B]:  # （｛［
            glyph = jp_font[glyph_name]
            glyph.transform(psMat.translate(-100, 0))
            glyph.width = full_width
        
        for glyph_name in [0xFF09, 0xFF3D, 0xFF5D]:  # ）｝］
            glyph = jp_font[glyph_name]
            glyph.transform(psMat.translate(100, 0))
            glyph.width = full_width
    except:
        pass
    
    # 调整全角句号和逗号
    try:
        for glyph in jp_font.selection.select(("unicode", None), 0xFF0E).byGlyphs:  # ．
            glyph.transform(psMat.scale(1.2, 1.2))
            glyph.width = full_width
        
        for glyph in jp_font.selection.select(("unicode", None), 0xFF0C).byGlyphs:  # ，
            glyph.transform(psMat.scale(1.15, 1.15))
            glyph.width = full_width
    except:
        pass
    
    jp_font.selection.none()
    eng_font.selection.none()

def transform_half_width(jp_font, eng_font):
    """转换半角宽度"""
    try:
        if not eng_font[0x0030].isWorthOutputting():
            return
        before_width_eng = eng_font[0x0030].width
    except:
        return
    after_width_eng = HALF_WIDTH_12
    x_scale = 546 / before_width_eng
    
    # 调整英文字体
    for glyph in eng_font.glyphs():
        if glyph.width > 0 and glyph.isWorthOutputting():
            after_width_eng_multiply = after_width_eng * round(glyph.width / before_width_eng)
            glyph.transform(psMat.scale(x_scale, 0.97))
            glyph.transform(psMat.translate((after_width_eng_multiply - glyph.width) / 2, 0))
            glyph.width = after_width_eng_multiply
    
    # 调整中文字体
    for glyph in jp_font.glyphs():
        if glyph.isWorthOutputting():
            if glyph.width == 500:  # 半角字符
                glyph.transform(psMat.translate((after_width_eng - glyph.width) / 2, 0))
                glyph.width = after_width_eng
            elif glyph.width == 1000:  # 全角字符
                glyph.transform(psMat.translate((after_width_eng * 2 - glyph.width) / 2, 0))
                glyph.width = after_width_eng * 2

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
    if "Regular" == weight:
        font.os2_weight = 400
    elif "SemiBold" == weight:
        font.os2_weight = 600
    elif "Thin" in weight:
        font.os2_weight = 100
    elif "ExtraLight" in weight:
        font.os2_weight = 200
    elif "Light" in weight:
        font.os2_weight = 300
    elif "Medium" in weight:
        font.os2_weight = 500
    elif "Bold" in weight:
        font.os2_weight = 700
    
    font.os2_vendor = VENDER_NAME
    
    # 设置字体名称
    font_family = font_name
    font_weight = weight
    font.familyname = font_family
    font.appendSFNTName(0x409, 2, font_weight)
    font.fontname = f"{font_family}-{font_weight}".replace(" ", "")
    font.fullname = f"{font_family} {font_weight}"
    font.weight = font_weight.split(" ")[0]
    font.appendSFNTName(0x409, 16, font_family)
    font.appendSFNTName(0x409, 17, font_weight)
    
    # 设置版权信息
    font.sfnt_names = (
        ("English (US)", "License", """This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"""),
        ("English (US)", "License URL", "http://scripts.sil.org/OFL"),
        ("English (US)", "Version", VERSION),
        ("English (US)", "Copyright", COPYRIGHT),
    )

def main():
    print("=== 生成缺失的NL字体 ===")
    
    # 生成缺失的两个字重
    generate_font(
        jp_style="Regular",
        eng_style="Regular",
        output_style="Regular"
    )
    
    generate_font(
        jp_style="Semibold",
        eng_style="SemiBold",
        output_style="SemiBold"
    )
    
    print("=== 缺失字体生成完成 ===")

if __name__ == "__main__":
    main()