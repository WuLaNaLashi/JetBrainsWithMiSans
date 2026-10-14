#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 准备 iA Writer 英文全源：
# 1. 从原版可变字体实例化 4 字重 x 直/斜（统一单一来源，含 400/700）
# 2. 从 Nerd Fonts patched 版提取图标子集（patched 有而文本源没有的全部码点）
# 3. 注入图标到每个实例 -> IASources/IAWriter-{Mono,Duo,Quattro}-{style}.ttf

import os
import shutil

from fontTools import merge, subset, ttLib
from fontTools.varLib.instancer import instantiateVariableFont

IA_DIR = "/home/hanxiao/ZCodeProject/iA-Fonts-master"
NF_DIR = "/home/hanxiao/ZCodeProject/iA-Writer"
OUT_DIR = "IASources"

ITALIC_ANGLE = -9.5  # iA 原版实测 post.italicAngle

# 家族 -> (原版子目录, patched Regular 文件名)
FAMILIES = {
    "Mono": ("iA Writer Mono", "iMWritingMonoNerdFont-Regular.ttf"),
    "Duo": ("iA Writer Duo", "iMWritingDuoNerdFont-Regular.ttf"),
    "Quattro": ("iA Writer Quattro", "iMWritingQuatNerdFont-Regular.ttf"),
}

# (weight, 样式名)
WEIGHTS = [
    (400, "Regular"),
    (500, "Medium"),
    (600, "SemiBold"),
    (700, "Bold"),
]

ITALIC_STYLE = {
    "Regular": "Italic",
    "Medium": "MediumItalic",
    "SemiBold": "SemiBoldItalic",
    "Bold": "BoldItalic",
}


def instantiate_text(var_path, weight, italic):
    """实例化可变字体并显式修正 instancer 不更新的元数据"""
    font = ttLib.TTFont(var_path)
    instantiateVariableFont(font, {"wght": weight, "SPCG": 0}, inplace=True)
    font["OS/2"].usWeightClass = weight
    if italic:
        font["head"].macStyle |= 0x02
        font["post"].italicAngle = ITALIC_ANGLE
    else:
        font["head"].macStyle &= ~0x02
        font["post"].italicAngle = 0
    if "fvar" in font:
        del font["fvar"]
    return font


def extract_icons(patched_path, base_cmap):
    """提取 patched 中新增于文本源的全部码点（Nerd 图标 + 补齐符号）"""
    pf = ttLib.TTFont(patched_path)
    diff = sorted(set(pf.getBestCmap().keys()) - base_cmap)
    if not diff:
        raise RuntimeError(f"图标差集为空: {patched_path}")
    opts = subset.Options()
    opts.name_IDs = [0, 6]
    opts.name_languages = [0x409]
    ss = subset.Subsetter(opts)
    ss.populate(unicodes=diff)
    ss.subset(pf)
    return pf, len(diff)


def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    for fam, (ia_sub, patched_name) in FAMILIES.items():
        var_upright = f"{IA_DIR}/{ia_sub}/Variable/iAWriter{fam}V.ttf"
        var_italic = f"{IA_DIR}/{ia_sub}/Variable/iAWriter{fam}V-Italic.ttf"

        # 差集基准 = 400 直体实例的 cmap（各字重 cmap 相同）
        base = instantiate_text(var_upright, 400, False)
        base_cmap = set(base.getBestCmap().keys())
        del base

        icons, n_icons = extract_icons(f"{NF_DIR}/{patched_name}", base_cmap)
        icons_path = f"{OUT_DIR}/IAIcons-{fam}.ttf"
        icons.save(icons_path)
        print(f"[{fam}] 图标差集 {n_icons} 码点 -> {icons_path}")
        del icons

        tmp_text = f"{OUT_DIR}/.tmp-text.ttf"
        for weight, wname in WEIGHTS:
            for italic in (False, True):
                style = ITALIC_STYLE[wname] if italic else wname
                var_path = var_italic if italic else var_upright
                text = instantiate_text(var_path, weight, italic)
                text.save(tmp_text)
                del text
                merged = merge.Merger().merge([tmp_text, icons_path])
                out = f"{OUT_DIR}/IAWriter-{fam}-{style}.ttf"
                merged.save(out)
                n_cmap = len(merged.getBestCmap())
                print(f"[{fam}] {style}: {n_cmap} 码点 -> {out}")
        os.remove(tmp_text)

    print("=== 英文全源准备完成 ===")


if __name__ == "__main__":
    main()
