#!/bin/bash

# MiWith 系列字体一键安装（含 fontconfig 等宽声明，装完 GNOME 终端等软件立即可选）
# 用法: ./install_fonts.sh [ia|jb|all]   默认 ia

set -e
cd "$(dirname "$0")"

SCOPE="${1:-ia}"
FONTS_DIR="${HOME}/.local/share/fonts"
CONF_DIR="${HOME}/.config/fontconfig/conf.d"
CONF_SRC="fontconfig/66-miwith-mono.conf"

install_family() {
    local src_dir="$1" dst_dir="$2"
    if [ ! -d "$src_dir" ]; then
        echo "跳过（目录不存在）: $src_dir"
        return
    fi
    mkdir -p "${FONTS_DIR}/${dst_dir}"
    cp -f "${src_dir}"/MiWith*.ttf "${FONTS_DIR}/${dst_dir}/"
    echo "已安装: ${src_dir} -> ${FONTS_DIR}/${dst_dir} ($(ls ${src_dir}/MiWith*.ttf | wc -l) 个文件)"
}

case "$SCOPE" in
    ia)
        install_family IAWithMiSans IAWithMiSans
        install_family IAWithMiSansHalf IAWithMiSansHalf
        ;;
    jb)
        install_family MiWithJBMonoNL MiWithJBMono
        install_family MiWithJBMonoHalfNL MiWithJBMonoHalf
        ;;
    all)
        install_family IAWithMiSans IAWithMiSans
        install_family IAWithMiSansHalf IAWithMiSansHalf
        install_family MiWithJBMonoNL MiWithJBMono
        install_family MiWithJBMonoHalfNL MiWithJBMonoHalf
        ;;
    *)
        echo "用法: $0 [ia|jb|all]"
        exit 1
        ;;
esac

# 部署 fontconfig 等宽声明（CJK 合并字体必需，否则 GNOME 终端等软件不显示）
mkdir -p "$CONF_DIR"
cp -f "$CONF_SRC" "$CONF_DIR/"
echo "已部署 fontconfig 规则: ${CONF_DIR}/66-miwith-mono.conf"

fc-cache -f > /dev/null 2>&1
echo "字体缓存已刷新"

echo ""
echo "=== 验证 ==="
ok=0; fail=""
for fam in MiWithIAMono MiWithIAMonoHalf MiWithJBMono MiWithJBMonoNL MiWithJBMonoHalf MiWithJBMonoHalfNL; do
    if fc-list "$fam" spacing 2>/dev/null | grep -q "spacing=100"; then
        ok=$((ok+1))
    elif fc-list "$fam" family 2>/dev/null | grep -q .; then
        # 已安装但未判 mono 才算失败；未安装的家族跳过
        fail="$fail $fam(未判mono)"
    fi
done
echo "等宽判定通过: ${ok} 个家族"
[ -n "$fail" ] && echo "警告:${fail}" || echo "全部通过，GNOME 终端等软件重启后即可选择"
