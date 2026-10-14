#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MiWithIA 产出验证：元数据 / 字形覆盖 / Half 2:1 对齐 / 字体完整性

import glob
import sys

from fontTools.ttLib import TTFont

WEIGHT_MAP = {"Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700,
              "Italic": 400, "MediumItalic": 500, "SemiBoldItalic": 600, "BoldItalic": 700}

SUBFAMILY_17 = {"Regular": "Regular", "Medium": "Medium", "SemiBold": "SemiBold", "Bold": "Bold",
                "Italic": "Italic", "MediumItalic": "Medium Italic",
                "SemiBoldItalic": "SemiBold Italic", "BoldItalic": "Bold Italic"}

PROBE_CHARS = {
    "中文": 0x4E2D,      # 中
    "英文A": 0x41,
    "英文m": 0x6D,
    "图标E700": 0xE700,
    "图标F48C": 0xF48C,
    "人民币符号": 0xA5,
    "全角空格": 0x3000,
}


def main():
    failures = []
    files = sorted(glob.glob("IAWithMiSans/MiWithIA*.ttf") + glob.glob("IAWithMiSansHalf/MiWithIA*.ttf"))
    files = [f for f in files if "-eng" not in f and "-zh" not in f and "merged" not in f]

    if len(files) != 32:
        failures.append(f"文件数 {len(files)} != 32")

    for path in files:
        name = path.split("/")[-1].replace(".ttf", "")
        variant, style = name.split("-", 1)
        try:
            font = TTFont(path)
        except Exception as e:
            failures.append(f"{name}: 无法打开 {e}")
            continue

        problems = check_font(font, variant, style)
        failures.extend(f"{name}: {p}" for p in problems)

    if failures:
        print(f"=== 验证失败 {len(failures)} 项 ===")
        for f in failures:
            print(" ", f)
        sys.exit(1)
    print(f"=== 全部 {len(files)} 个字体验证通过 ===")


def check_font(font, variant, style):
    problems = []
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    os2 = font["OS/2"]
    name = font["name"]

    def get_name(nid):
        rec = name.getName(nid, 3, 1, 0x409) or name.getName(nid, 1, 0, 0)
        return rec.toUnicode() if rec else None

    # 元数据
    if get_name(16) != variant:
        problems.append(f"nameID16={get_name(16)!r} 应为 {variant!r}")
    if get_name(17) != SUBFAMILY_17[style]:
        problems.append(f"nameID17={get_name(17)!r} 应为 {SUBFAMILY_17[style]!r}")
    if os2.usWeightClass != WEIGHT_MAP[style]:
        problems.append(f"usWeightClass={os2.usWeightClass} 应为 {WEIGHT_MAP[style]}")

    is_italic, is_bold = "Italic" in style, "Bold" in style
    expect_fs = 0x100 | (0x01 if is_italic else 0) | (0x20 if is_bold else 0)
    if not (is_italic or is_bold):
        expect_fs |= 0x40
    if os2.fsSelection != expect_fs:
        problems.append(f"fsSelection={os2.fsSelection:#x} 应为 {expect_fs:#x}")
    if font["head"].macStyle != ((0x02 if is_italic else 0) | (0x01 if is_bold else 0)):
        problems.append(f"macStyle={font['head'].macStyle} 不符")

    # 等宽声明（仅 Mono 系）
    is_mono = variant.startswith("MiWithIAMono")
    if font["post"].isFixedPitch != (1 if is_mono else 0):
        problems.append(f"isFixedPitch={font['post'].isFixedPitch} 应为 {1 if is_mono else 0}")
    if is_mono and os2.panose.bProportion != 9:
        problems.append(f"PANOSE bProportion={os2.panose.bProportion} 应为 9")

    # 字形覆盖
    for label, cp in PROBE_CHARS.items():
        if cp not in cmap:
            problems.append(f"缺字形 {label}(U+{cp:04X})")

    # Half 2:1 对齐：全角 advance 必须等于英文 advance 的两倍
    if variant.endswith("Half"):
        w_zh = hmtx[cmap[0x4E2D]][0]
        w_en = hmtx[cmap[0x41]][0]
        if w_zh != 2 * w_en:
            problems.append(f"2:1 破坏: 全角={w_zh} 英文={w_en}")
    return problems


if __name__ == "__main__":
    main()
