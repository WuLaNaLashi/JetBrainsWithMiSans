#!/bin/bash

# 字体合并主脚本
# 自动化合并JetBrains Mono NF和MiSans字体

set -e

echo "=== MiWithJBMonoHalf 字体合并脚本 ==="
echo "开始时间: $(date)"

# 激活Python虚拟环境
source /home/hanxiao/Python/HXGPyhton/bin/activate

# 检查必要的工具
echo "检查必要工具..."
which fontforge > /dev/null || { echo "错误: 未找到fontforge"; exit 1; }
which ttfautohint > /dev/null || { echo "错误: 未找到ttfautohint"; exit 1; }
python -c "import fontTools" || { echo "错误: 未安装fontTools"; exit 1; }

echo "工具检查完成"

# 清理并创建输出目录
echo "准备输出目录..."
if [ -d "MiWithJBMonoHalfNL" ]; then
    rm -rf "MiWithJBMonoHalfNL"
fi
mkdir -p "MiWithJBMonoHalfNL"

# 步骤1: 使用FontForge处理字体
echo "步骤1: 使用FontForge处理字体..."
fontforge -script merge_half_fonts_ff.py

if [ $? -ne 0 ]; then
    echo "错误: FontForge处理失败"
    exit 1
fi

echo "FontForge处理完成"

# 步骤2: 使用FontTools进行后处理
echo "步骤2: 使用FontTools进行后处理..."
python post_process_half_fonts.py

if [ $? -ne 0 ]; then
    echo "错误: FontTools后处理失败"
    exit 1
fi

echo "FontTools后处理完成"

# 步骤3: 显示结果
echo "步骤3: 显示生成的字体文件..."
echo ""
echo "生成的字体文件:"
ls -la MiWithJBMonoHalfNL/*.ttf
echo ""

# 统计生成的文件数量
file_count=$(find MiWithJBMonoHalfNL -name "*.ttf" | wc -l)
echo "总共生成了 ${file_count} 个TTF字体文件"

echo ""
echo "=== 字体合并完成 ==="
echo "完成时间: $(date)"

# 显示字体文件信息
echo ""
echo "字体文件详情:"
for file in MiWithJBMonoHalfNL/*.ttf; do
    if [ -f "$file" ]; then
        echo "----------------------------------------"
        echo "文件: $(basename "$file")"
        # 使用fonttools显示基本信息
        python3 -c "
from fontTools import ttLib
try:
    font = ttLib.TTFont('$file')
    name_table = font['name']
    for name_record in name_table.names:
        if name_record.nameID == 1:  # Font Family name
            family_name = name_record.toUnicode()
        elif name_record.nameID == 2:  # Font Subfamily name
            subfamily_name = name_record.toUnicode()
        elif name_record.nameID == 4:  # Full font name
            full_name = name_record.toUnicode()
    print(f'  字体家族: {family_name}')
    print(f'  字体样式: {subfamily_name}')
    print(f'  完整名称: {full_name}')
    print(f'  字重: {font[\"OS/2\"].usWeightClass}')
    font.close()
except Exception as e:
    print(f'  读取信息失败: {e}')
"
    fi
done