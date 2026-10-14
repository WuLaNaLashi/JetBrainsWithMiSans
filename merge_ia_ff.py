#!/usr/bin/env fontforge --lang=py -script

# -*- coding: utf-8 -*-

# 合并 iA Writer NerdFont 英文全源(IASources/)与 MiSans 的 FontForge 脚本
# 用法: fontforge -script merge_ia_ff.py {Mono|Duo|Quattro} [half]
# 产出中间件: {IAWithMiSans,IAWithMiSansHalf}/MiWithIA{Family}[{Half}]-{style}-eng.ttf / -zh.ttf

import math
import os
import sys

import fontforge
import psMat

# 配置参数（与现有 MiWithJBMono 流水线对齐）
VERSION = "1.0.0"
ZH_FONT_PATH = "MiSans/ttf/MiSans-{zh_style}.ttf"
ENG_FONT_DIR = "IASources"
EM_ASCENT = 800
EM_DESCENT = 200
OS2_ASCENT = 1020
OS2_DESCENT = 300
ITALIC_ANGLE = 9.5  # iA 原版 italicAngle 实测 -9.5
VENDER_NAME = "MiIA"

# 英文全源/输出样式名 -> MiSans 文件名字重（注意 Semibold 小写 b）
# (英文源样式, MiSans 文件名, 输出样式)——MiSans 的 SemiBold 文件名是小写 b
WEIGHTS = [
    ("Regular", "Regular", "Regular"),
    ("Medium", "Medium", "Medium"),
    ("SemiBold", "Semibold", "SemiBold"),
    ("Bold", "Bold", "Bold"),
]

ITALIC_WEIGHTS = [
    ("Italic", "Regular", "Italic"),
    ("MediumItalic", "Medium", "MediumItalic"),
    ("SemiBoldItalic", "Semibold", "SemiBoldItalic"),
    ("BoldItalic", "Bold", "BoldItalic"),
]

# Half 版参数（沿用 MiWithJBMonoHalf 的 528/1056 方案）
HALF_WIDTH_12 = 528
HALF_SCALE_BASE = 546  # 字形先缩到此宽度再居中到目标 advance

COPYRIGHT = """[iA Writer]
Copyright (c) 2018 Information Architects Inc.
https://ia.net/topics/ia-writer-font
Based on IBM Plex. Copyright (c) 2017 IBM Corp.

[MiSans]
Copyright (c) 2020, Xiaomi Inc.
https://www.mi.com/global/misans/

[Nerd Fonts]
Copyright (c) 2014, Ryan L McIntyre https://ryanlmcintyre.com

[MiWithIA]
Copyright (c) 2026, MiWithIA Project
"""


def main():
    family = sys.argv[1] if len(sys.argv) > 1 else "Mono"
    if family not in ("Mono", "Duo", "Quattro"):
        print(f"未知家族: {family}")
        sys.exit(1)
    half = len(sys.argv) > 2 and sys.argv[2] == "half"

    font_name = f"MiWithIA{family}{'Half' if half else ''}"
    build_dir = "IAWithMiSansHalf" if half else "IAWithMiSans"

    # 目录由 build 脚本统一清理；多家族共享 IAWithMiSans，这里只确保存在
    os.makedirs(build_dir, exist_ok=True)

    print(f"=== 生成 {font_name}（half={half}）===")
    for eng_style, zh_style, output_style in WEIGHTS + ITALIC_WEIGHTS:
        generate_font(family, font_name, build_dir, eng_style, zh_style, output_style, half)

    print(f"=== {font_name} 中间件生成完成 ===")


def generate_font(family, font_name, build_dir, eng_style, zh_style, output_style, half):
    print(f"=== 生成 {font_name}-{output_style} ===")

    zh_font, eng_font = open_fonts(zh_style, family, eng_style)

    adjust_em(eng_font)
    adjust_em(zh_font)

    zh_font = delete_duplicate_glyphs(zh_font, eng_font)

    if "Italic" in output_style:
        transform_italic_glyphs(zh_font)

    remove_lookups(zh_font, remove_gsub=False, remove_gpos=True)

    if half:
        transform_half_width(zh_font, eng_font)

    cap_height = 730
    x_height = 550
    edit_meta_data(eng_font, output_style, font_name, cap_height, x_height)
    edit_meta_data(zh_font, output_style, font_name, cap_height, x_height)

    eng_font.generate(f"{build_dir}/{font_name}-{output_style}-eng.ttf")
    zh_font.generate(f"{build_dir}/{font_name}-{output_style}-zh.ttf")

    zh_font.close()
    eng_font.close()


def open_fonts(zh_style, family, eng_style):
    """打开 MiSans 与英文全源，解除引用"""
    zh_font_path = ZH_FONT_PATH.replace("{zh_style}", zh_style)
    eng_font_path = f"{ENG_FONT_DIR}/IAWriter-{family}-{eng_style}.ttf"

    print(f"加载中文字体: {zh_font_path}")
    print(f"加载英文字体: {eng_font_path}")

    zh_font = fontforge.open(zh_font_path)
    eng_font = fontforge.open(eng_font_path)

    for font in (zh_font, eng_font):
        for glyph in font.glyphs():
            if glyph.isWorthOutputting():
                font.selection.select(("more", None), glyph)
        font.unlinkReferences()
        font.selection.none()

    return zh_font, eng_font


def adjust_em(font):
    font.em = EM_ASCENT + EM_DESCENT


def delete_duplicate_glyphs(zh_font, eng_font):
    """去重：¥/全角空格归中文，其余重叠码点清中文侧"""
    eng_font.selection.none()
    zh_font.selection.none()

    # 特殊符号使用中文字体
    for cp in (0x00A5, 0x3000):
        try:
            if eng_font[cp].isWorthOutputting():
                eng_font[cp].clear()
        except Exception:
            pass

    # 拉丁/音标扩展使用英文字体（¥ 除外——上方已决定归中文；其余重叠区由下方通用去重处理）
    for glyph in zh_font.glyphs():
        if glyph.unicode != 0x00A5 and (0x0000 <= glyph.unicode <= 0x02AF or 0x1D00 <= glyph.unicode <= 0x1D7F):
            if glyph.isWorthOutputting():
                glyph.clear()

    # 通用去重：英文侧有的码点，中文侧全部清掉
    for glyph in zh_font.glyphs("encoding"):
        if glyph.isWorthOutputting() and glyph.unicode > 0:
            try:
                eng_font.selection.select(("more", "unicode"), glyph.unicode)
            except ValueError:
                continue

    for glyph in eng_font.selection.byGlyphs:
        zh_font.selection.select(("more", "unicode"), glyph.unicode)

    for glyph in zh_font.selection.byGlyphs:
        if glyph.isWorthOutputting():
            glyph.clear()

    zh_font.selection.none()
    eng_font.selection.none()

    return zh_font


def transform_italic_glyphs(font):
    """MiSans 无原生斜体，skew 伪造（角度对齐 iA 原版 9.5°）"""
    font.italicangle = -ITALIC_ANGLE

    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            orig_width = glyph.width
            glyph.transform(psMat.skew(ITALIC_ANGLE * math.pi / 180))
            glyph.transform(psMat.translate(-32, 0))
            glyph.width = orig_width


def remove_lookups(font, remove_gsub=True, remove_gpos=True):
    if remove_gsub:
        for lookup in font.gsub_lookups:
            font.removeLookup(lookup)
    if remove_gpos:
        for lookup in font.gpos_lookups:
            font.removeLookup(lookup)


def transform_half_width(zh_font, eng_font):
    """英文缩到 528、中文全角放大到 1056，实现严格 2:1"""
    try:
        if not eng_font[0x0030].isWorthOutputting():
            return
        before_width_eng = eng_font[0x0030].width
    except Exception:
        return
    after_width_eng = HALF_WIDTH_12
    x_scale = HALF_SCALE_BASE / before_width_eng

    for glyph in eng_font.glyphs():
        if glyph.width > 0 and glyph.isWorthOutputting():
            after_width_eng_multiply = after_width_eng * round(glyph.width / before_width_eng)
            glyph.transform(psMat.scale(x_scale, 0.97))
            glyph.transform(psMat.translate((after_width_eng_multiply - glyph.width) / 2, 0))
            glyph.width = after_width_eng_multiply

    for glyph in zh_font.glyphs():
        if glyph.isWorthOutputting():
            if glyph.width == 500:  # 半角
                glyph.transform(psMat.translate((after_width_eng - glyph.width) / 2, 0))
                glyph.width = after_width_eng
            elif glyph.width == 1000:  # 全角
                glyph.transform(psMat.translate((after_width_eng * 2 - glyph.width) / 2, 0))
                glyph.width = after_width_eng * 2


def edit_meta_data(font, weight, font_name, cap_height, x_height):
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

    if weight in ("Regular", "Italic"):
        font.os2_weight = 400
    elif "Medium" in weight:
        font.os2_weight = 500
    elif "SemiBold" in weight:
        font.os2_weight = 600
    elif "Bold" in weight:
        font.os2_weight = 700

    font.os2_vendor = VENDER_NAME

    font_family = font_name
    font_weight = weight

    font.familyname = font_family

    if "Italic" in weight:
        font_weight = font_weight.replace("Italic", " Italic").replace("  ", " ").strip()
        if not font_weight.endswith("Italic"):
            font_weight += " Italic"

    font.appendSFNTName(0x409, 2, font_weight)
    font.fontname = f"{font_family}-{font_weight}".replace(" ", "")
    font.fullname = f"{font_family}-{font_weight}".replace(" ", "")
    font.weight = font_weight.split(" ")[0]

    if weight not in ("Regular", "Italic", "Bold", "BoldItalic"):
        font.appendSFNTName(0x409, 16, font_family)
        font.appendSFNTName(0x409, 17, font_weight)

    font.sfnt_names = (
        ("English (US)", "License", "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"),
        ("English (US)", "License URL", "http://scripts.sil.org/OFL"),
        ("English (US)", "Version", VERSION),
        ("English (US)", "Copyright", COPYRIGHT),
    )


if __name__ == "__main__":
    main()
