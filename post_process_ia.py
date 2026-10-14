#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# iA Writer + MiSans 合并后处理（fontTools 直接精控元数据，不走 ttx 往返）
# 输入: IAWithMiSans{,Half}/MiWithIA*-eng.ttf + -zh.ttf 中间件
# 输出: 最终 MiWithIA{Mono,MonoHalf,Duo,Quattro}-{style}.ttf

import glob
import os
import subprocess
import sys

from fontTools import merge, ttLib

BUILD_DIRS = ["IAWithMiSans", "IAWithMiSansHalf"]
VENDER_NAME = "MiIA"

# 等宽家族（Mono 系）设 isFixedPitch + PANOSE bProportion=9
MONOSPACED_PREFIXES = ("MiWithIAMono",)

PANOSE_WEIGHT = {"Thin": 1, "ExtraLight": 2, "Light": 3, "Regular": 5,
                 "Medium": 6, "SemiBold": 7, "Bold": 8}


def main():
    for build_dir in BUILD_DIRS:
        eng_files = sorted(glob.glob(f"{build_dir}/*-eng.ttf"))
        if not eng_files:
            continue
        for eng_file in eng_files:
            basename = os.path.basename(eng_file).replace("-eng.ttf", "")
            font_variant, font_style = basename.split("-", 1)
            process_font(build_dir, font_variant, font_style)
    print("=== 后处理完成 ===")


def process_font(build_dir, font_variant, font_style):
    eng_path = f"{build_dir}/{font_variant}-{font_style}-eng.ttf"
    zh_path = f"{build_dir}/{font_variant}-{font_style}-zh.ttf"
    if not (os.path.exists(eng_path) and os.path.exists(zh_path)):
        print(f"跳过（缺中间件）: {font_variant}-{font_style}")
        return

    hinted_path = eng_path.replace("-eng.ttf", "-eng-hinted.ttf")
    add_hinting(eng_path, hinted_path)

    merged_path = f"{build_dir}/{font_variant}-{font_style}_merged.ttf"
    merge_fonts(hinted_path, zh_path, merged_path)

    final_path = f"{build_dir}/{font_variant}-{font_style}.ttf"
    fix_metadata(merged_path, final_path, font_variant, font_style)

    for tmp in (eng_path, hinted_path, zh_path, merged_path):
        if os.path.exists(tmp):
            os.remove(tmp)

    print(f"完成: {final_path}")


def add_hinting(input_path, output_path):
    """英文侧 ttfautohint 提示（参数沿用现有流水线）"""
    args = ["ttfautohint", "-l", "6", "-r", "45", "-D", "latn", "-f", "none",
            "-S", "-W", "-X", "13-", "-I", input_path, output_path]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0 and not os.path.exists(output_path):
        print(f"  hinting 失败，复制原文件: {result.stderr.strip()[:200]}")
        subprocess.run(["cp", input_path, output_path], check=True)


def merge_fonts(eng_path, zh_path, output_path):
    zh_font = ttLib.TTFont(zh_path)
    for tbl in ("vhea", "vmtx"):
        if tbl in zh_font:
            del zh_font[tbl]
    zh_font.save(zh_path)
    del zh_font

    merged = merge.Merger().merge([eng_path, zh_path])
    merged.save(output_path)


def fix_metadata(input_path, output_path, font_variant, font_style):
    """fontTools 直接精控 name/head/OS2/post，规避 ttx 往返丢 nameID 16/17 的旧坑"""
    font = ttLib.TTFont(input_path)

    # ---- 名称 ----
    # 规范：nameID 16/17 全覆盖（首选族名 + 完整子族）；
    # nameID 1/2 走兼容四样式拆分——中间字重 nameID1=「族名 Medium」、nameID2=Regular/Italic
    is_italic = "Italic" in font_style
    is_bold = "Bold" in font_style

    if font_style in ("Regular", "Italic", "Bold", "BoldItalic"):
        family_compat = font_variant
    else:
        family_compat = f"{font_variant} {font_style.split('Italic')[0]}"
    subfamily_compat = ("Bold Italic" if is_italic else "Bold") if is_bold else ("Italic" if is_italic else "Regular")

    if font_style == "Regular":
        full_subfamily = "Regular"
    elif is_italic:
        full_subfamily = font_style.replace("Italic", "Italic").replace("MediumItalic", "Medium Italic").replace("SemiBoldItalic", "SemiBold Italic").replace("BoldItalic", "Bold Italic")
    else:
        full_subfamily = font_style

    name = font["name"]
    for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
        name.setName(family_compat, 1, pid, eid, lid)
        name.setName(subfamily_compat, 2, pid, eid, lid)
        name.setName(f"{font_variant} {full_subfamily}".replace(f"{font_variant} Regular", font_variant), 4, pid, eid, lid)
        name.setName(f"{font_variant}-{font_style}", 6, pid, eid, lid)
        name.setName(font_variant, 16, pid, eid, lid)
        name.setName(full_subfamily, 17, pid, eid, lid)

    # ---- 字重/样式位 ----
    weight = 400
    for key, w in (("SemiBold", 600), ("Medium", 500), ("Bold", 700)):
        if key in font_style:
            weight = w
            break

    os2 = font["OS/2"]
    os2.usWeightClass = weight
    # fsSelection: WWS(bit8=0x100)；非粗非斜才置 REGULAR(bit6=0x40)
    fs = 0x100
    if is_italic:
        fs |= 0x01
    if is_bold:
        fs |= 0x20
    if not (is_italic or is_bold):
        fs |= 0x40
    os2.fsSelection = fs
    os2.panose.bFamilyType = 2
    os2.panose.bSerifStyle = 11
    os2.panose.bWeight = {400: 5, 500: 6, 600: 7, 700: 8}[weight]
    os2.panose.bProportion = 9 if is_monospaced(font_variant) else 0
    os2.panose.bContrast = 5
    os2.panose.bStrokeVariation = 2
    os2.panose.bArmStyle = 3
    os2.panose.bLetterForm = 0
    os2.panose.bMidline = 2
    os2.panose.bXHeight = 3

    head = font["head"]
    head.macStyle = (0x02 if is_italic else 0) | (0x01 if is_bold else 0)

    post = font["post"]
    post.isFixedPitch = 1 if is_monospaced(font_variant) else 0

    font.save(output_path)


def is_monospaced(font_variant):
    return any(font_variant.startswith(p) for p in MONOSPACED_PREFIXES)


if __name__ == "__main__":
    main()
