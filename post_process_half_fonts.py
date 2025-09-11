#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 字体合并后处理脚本
# 使用fonttools进行最终合并和优化

import glob
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools import merge, ttLib, ttx

# 配置参数
FONT_NAME_BASE = "MiWithJBMonoHalf"
BUILD_FONTS_DIR = "MiWithJBMonoHalfNL"
HALF_WIDTH_12 = 528

def main():
    print("=== 开始字体后处理 ===")
    
    # 处理所有字体
    process_all_fonts()
    
    print("=== 字体后处理完成 ===")

def process_all_fonts():
    """处理所有字体"""
    
    # 查找所有-eng.ttf文件
    eng_files = glob.glob(f"{BUILD_FONTS_DIR}/*-eng.ttf")
    
    for eng_file in eng_files:
        print(f"处理 {eng_file}")
        
        # 从文件名提取信息
        basename = os.path.basename(eng_file)
        parts = basename.replace("-eng.ttf", "").split("-")
        
        if len(parts) >= 2:
            font_variant = parts[0]  # MiWithJBMonoHalf 或 MiWithJBMonoHalfNL
            font_style = "-".join(parts[1:])  # 样式，可能包含连字符
            
            # 处理字体
            process_font(font_variant, font_style)

def process_font(font_variant, font_style):
    """处理单个字体"""
    
    # 构建文件名
    eng_font_path = f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}-eng.ttf"
    zh_font_path = f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}-zh.ttf"
    
    # 检查文件是否存在
    if not os.path.exists(eng_font_path) or not os.path.exists(zh_font_path):
        print(f"文件不存在: {eng_font_path} 或 {zh_font_path}")
        return
    
    # 1. 添加字体提示
    hinted_eng_path = eng_font_path.replace("-eng.ttf", "-eng-hinted.ttf")
    add_hinting(eng_font_path, hinted_eng_path, font_style)
    
    # 2. 合并字体
    merged_path = f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}_merged.ttf"
    merge_fonts(hinted_eng_path, zh_font_path, merged_path)
    
    # 3. 修复字体表
    final_path = f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}.ttf"
    fix_font_tables(merged_path, final_path, font_style)
    
    # 4. 清理临时文件
    cleanup_temp_files(font_variant, font_style)
    
    print(f"完成: {final_path}")

def add_hinting(input_path, output_path, style):
    """添加字体提示"""
    try:
        # 基本的ttfautohint参数
        args = [
            "-l", "6",        # 最大ppem
            "-r", "45",       # 最小ppem
            "-D", "latn",     # 默认脚本
            "-f", "none",     # 不增加hinting
            "-S",             # 符号 hinting
            "-W",             # 忽略警告
            "-X", "13-",      # X轴增加
            "-I",             # 忽略权限错误
            input_path,
            output_path
        ]
        
        print(f"添加字体提示: {input_path}")
        os.system(f"ttfautohint {' '.join(args)}")
        
    except Exception as e:
        print(f"字体提示失败: {e}")
        # 如果失败，直接复制原文件
        os.system(f"cp {input_path} {output_path}")

def merge_fonts(eng_path, jp_path, output_path):
    """合并字体"""
    try:
        print(f"合并字体: {eng_path} + {jp_path}")
        
        # 删除中文字体的vhea和vmtx表以避免冲突
        jp_font = ttLib.TTFont(jp_path)
        if "vhea" in jp_font:
            del jp_font["vhea"]
        if "vmtx" in jp_font:
            del jp_font["vmtx"]
        jp_font.save(jp_path)
        
        # 使用fonttools合并字体
        merger = merge.Merger()
        merged_font = merger.merge([eng_path, jp_path])
        merged_font.save(output_path)
        
    except Exception as e:
        print(f"字体合并失败: {e}")

def fix_font_tables(input_path, output_path, style):
    """修复字体表"""
    try:
        print(f"修复字体表: {input_path}")
        
        # 生成临时ttx文件
        temp_ttx = input_path.replace(".ttf", ".ttx")
        temp_ttx_os2 = input_path.replace(".ttf", "_os2.ttx")
        
        # 导出OS/2, post, name表
        ttx.main([
            "-t", "OS/2",
            "-t", "post", 
            "-t", "name",
            "-f",
            "-o", temp_ttx,
            input_path
        ])
        
        # 解析XML
        xml = ET.parse(temp_ttx)
        
        # 修复OS/2表
        fix_os2_table(xml, style)
        
        # 修复post表
        fix_post_table(xml)
        
        # 清理name表
        fix_name_table(xml)
        
        # 保存修改后的XML
        xml.write(temp_ttx_os2, encoding="utf-8", xml_declaration=True)
        
        # 应用修改到字体
        ttx.main([
            "-o", output_path,
            "-m", input_path,
            temp_ttx_os2
        ])
        
        # 清理临时文件
        for temp_file in [temp_ttx, temp_txx_os2]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    except Exception as e:
        print(f"修复字体表失败: {e}")
        # 如果失败，直接复制原文件
        os.system(f"cp {input_path} {output_path}")

def fix_os2_table(xml, style):
    """修复OS/2表"""
    try:
        # 设置平均字符宽度
        x_avg_char_width = xml.find("OS_2/xAvgCharWidth")
        if x_avg_char_width is not None:
            x_avg_char_width.set("value", str(HALF_WIDTH_12))
        
        # 设置字体选择
        fs_selection = xml.find("OS_2/fsSelection")
        if fs_selection is not None:
            if style == "Regular":
                fs_selection.set("value", "00000001 01000000")
            elif style == "Italic":
                fs_selection.set("value", "00000001 00000001")
            elif style == "Bold":
                fs_selection.set("value", "00000001 00100000")
            elif style == "BoldItalic":
                fs_selection.set("value", "00000001 00100001")
            else:
                # 其他样式根据字重设置
                if "Bold" in style:
                    if "Italic" in style:
                        fs_selection.set("value", "00000001 00100001")
                    else:
                        fs_selection.set("value", "00000001 00100000")
                elif "Italic" in style:
                    fs_selection.set("value", "00000001 00000001")
                else:
                    fs_selection.set("value", "00000001 01000000")
        
        # 设置PANOSE
        panose = xml.find("OS_2/panose")
        if panose is not None:
            # 根据字重设置
            if "Thin" in style:
                weight = "1"
            elif "ExtraLight" in style:
                weight = "2"
            elif "Light" in style:
                weight = "3"
            elif "Regular" in style or "Text" in style:
                weight = "5"
            elif "Medium" in style:
                weight = "6"
            elif "SemiBold" in style:
                weight = "7"
            elif "Bold" in style:
                weight = "8"
            else:
                weight = "5"
            
            # 设置PANOSE值
            panose.find("bFamilyType").set("value", "2")  # Latin Text
            panose.find("bSerifStyle").set("value", "11")  # Normal Sans
            panose.find("bWeight").set("value", weight)
            panose.find("bProportion").set("value", "9")  # Monospaced
            panose.find("bContrast").set("value", "5")
            panose.find("bStrokeVariation").set("value", "2")
            panose.find("bArmStyle").set("value", "3")
            panose.find("bLetterForm").set("value", "0")
            panose.find("bMidline").set("value", "2")
            panose.find("bXHeight").set("value", "3")
            
    except Exception as e:
        print(f"修复OS/2表失败: {e}")

def fix_post_table(xml):
    """修复post表"""
    try:
        # 设置等宽字体标志
        is_fixed_pitch = xml.find("post/isFixedPitch")
        if is_fixed_pitch is not None:
            is_fixed_pitch.set("value", "1")  # 等宽字体
            
    except Exception as e:
        print(f"修复post表失败: {e}")

def fix_name_table(xml):
    """清理name表"""
    try:
        # 清理无效的版权信息
        name_table = xml.find("name")
        if name_table is not None:
            for namerecord in name_table.findall("namerecord[@nameID='0']"):
                if namerecord.text and "PlemolJP" in namerecord.text:
                    name_table.remove(namerecord)
                    
    except Exception as e:
        print(f"清理name表失败: {e}")

def cleanup_temp_files(font_variant, font_style):
    """清理临时文件"""
    patterns = [
        f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}-eng.ttf",
        f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}-eng-hinted.ttf",
        f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}-zh.ttf",
        f"{BUILD_FONTS_DIR}/{font_variant}-{font_style}_merged.ttf",
        f"{BUILD_FONTS_DIR}/*.ttx"
    ]
    
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    main()