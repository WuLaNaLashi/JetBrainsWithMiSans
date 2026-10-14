#!/bin/bash

# MiWithIA 字体合并主脚本（iA Writer NerdFont + MiSans）
# 流水线: prepare_ia_sources.py -> merge_ia_ff.py x4 -> post_process_ia.py

set -e

cd "$(dirname "$0")"

PYTHON=/home/hanxiao/Python/HXPython-uv/bin/python

echo "=== MiWithIA 字体合并脚本 ==="
echo "开始时间: $(date)"

# 检查必要的工具
echo "检查必要工具..."
which fontforge > /dev/null || { echo "错误: 未找到fontforge"; exit 1; }
which ttfautohint > /dev/null || { echo "错误: 未找到ttfautohint"; exit 1; }
$PYTHON -c "import fontTools" || { echo "错误: 未安装fontTools"; exit 1; }
[ -d /home/hanxiao/ZCodeProject/iA-Fonts-master ] || { echo "错误: 未找到 iA-Fonts-master"; exit 1; }
[ -d /home/hanxiao/ZCodeProject/iA-Writer ] || { echo "错误: 未找到 Nerd Fonts patched 源 iA-Writer"; exit 1; }

# 步骤1: 准备英文全源（实例化 + 图标注入）
echo "步骤1: 准备英文全源..."
$PYTHON prepare_ia_sources.py

# 步骤2: FontForge 处理（清理中间件目录后统一构建）
echo "步骤2: FontForge 处理..."
rm -rf IAWithMiSans IAWithMiSansHalf
mkdir -p IAWithMiSans IAWithMiSansHalf
fontforge -script merge_ia_ff.py Mono
fontforge -script merge_ia_ff.py Duo
fontforge -script merge_ia_ff.py Quattro
fontforge -script merge_ia_ff.py Mono half

# 步骤3: FontTools 后处理（合并 + 元数据精控）
echo "步骤3: FontTools 后处理..."
$PYTHON post_process_ia.py

# 步骤4: 结果统计
echo "步骤4: 生成的字体文件..."
echo ""
file_count=$(find IAWithMiSans IAWithMiSansHalf -maxdepth 1 -name "MiWithIA*.ttf" ! -name "*-zh.ttf" ! -name "*-eng*" | wc -l)
echo "总共生成了 ${file_count} 个TTF字体文件"
ls -la IAWithMiSans/*.ttf IAWithMiSansHalf/*.ttf 2>/dev/null | grep -v -- "-zh.ttf"

echo ""
echo "=== 字体合并完成 ==="
echo "完成时间: $(date)"
