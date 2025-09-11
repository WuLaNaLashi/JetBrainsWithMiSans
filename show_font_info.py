#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from fontTools import ttLib

def show_font_info(font_path):
    """显示字体信息"""
    try:
        font = ttLib.TTFont(font_path)
        name_table = font['name']
        
        family_name = ""
        subfamily_name = ""
        full_name = ""
        weight = ""
        
        for name_record in name_table.names:
            if name_record.nameID == 1:  # Font Family name
                family_name = name_record.toUnicode()
            elif name_record.nameID == 2:  # Font Subfamily name
                subfamily_name = name_record.toUnicode()
            elif name_record.nameID == 4:  # Full font name
                full_name = name_record.toUnicode()
        
        if 'OS/2' in font:
            weight = font['OS/2'].usWeightClass
        
        print(f"文件: {os.path.basename(font_path)}")
        print(f"  字体家族: {family_name}")
        print(f"  字体样式: {subfamily_name}")
        print(f"  完整名称: {full_name}")
        print(f"  字重: {weight}")
        print(f"  文件大小: {os.path.getsize(font_path) / 1024:.1f} KB")
        print()
        
        font.close()
    except Exception as e:
        print(f"读取 {font_path} 失败: {e}")

def main():
    font_dir = "MiWithJBMonoNL"
    
    if not os.path.exists(font_dir):
        print("字体目录不存在")
        return
    
    print("=== MiWithJBMono 字体家族信息 ===")
    print()
    
    # 获取NL字体文件
    nl_dir = os.path.join(font_dir, "NL_Fonts")
    nl_fonts = []
    if os.path.exists(nl_dir):
        nl_fonts = [f for f in os.listdir(nl_dir) if f.endswith('.ttf')]
        nl_fonts.sort()
    
    # 获取带连字字体文件
    ligature_dir = os.path.join(font_dir, "Ligature_Fonts")
    ligature_fonts = []
    if os.path.exists(ligature_dir):
        ligature_fonts = [f for f in os.listdir(ligature_dir) if f.endswith('.ttf')]
        ligature_fonts.sort()
    
    print("不带连字的字体 (MiWithJBMonoNL):")
    print("=" * 50)
    for font_file in nl_fonts:
        show_font_info(os.path.join(nl_dir, font_file))
    
    print("带连字的字体 (MiWithJBMono):")
    print("=" * 50)
    for font_file in ligature_fonts:
        show_font_info(os.path.join(ligature_dir, font_file))
    
    print("总计:")
    print(f"- 不带连字字体: {len(nl_fonts)} 个")
    print(f"- 带连字字体: {len(ligature_fonts)} 个")
    print(f"- 总计: {len(nl_fonts) + len(ligature_fonts)} 个字体文件")

if __name__ == "__main__":
    main()