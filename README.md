# MiWithJBMono 字体合并项目总结

## 项目概述

成功创建了 **MiWithJBMono** 和 **MiWithJBMonoHalf** 字体家族，将 **JetBrains Mono NF** 与 **MiSans** 字体融合，生成了一套同时支持英文等宽编程显示和中文字体的字体家族。

## MiWithIA 系列（iA Writer NerdFont + MiSans）

在 MiWithJBMono 流水线基础上新增，英文源换成 **iA Writer**（Nerd Fonts v3.5.1 官方 patched 版，基于 iA 2.000），中文仍为 MiSans：

| 家族 | 说明 |
|---|---|
| `MiWithIAMono` | iA Writer Mono（严格等宽 600）+ Nerd 图标 |
| `MiWithIAMonoHalf` | 同上，英文缩至 528/中文放大 1056，中英严格 2:1 对齐 |
| `MiWithIADuo` | iA Writer Duo（双宽 600/900，含希腊语），仅标准版 |
| `MiWithIAQuattro` | iA Writer Quattro（四宽 300/450/600/900），仅标准版 |

- **字重**：Regular(400)/Medium(500)/SemiBold(600)/Bold(700) + 全部斜体（英文斜体为 iA 原生 9.5°，中文 skew 伪造对齐）
- **中间字重**：从 iA 可变字体（wght 轴 400-700）实例化，Nerd 图标从 patched 版差集提取后注入
- **无连字**：iA Writer 本身无任何编程连字（GSUB 无 liga/calt），故无 NL 变体
- **构建**：`./build_ia_fonts.sh`（依赖 `/home/hanxiao/ZCodeProject/iA-Fonts-master` 与 `/home/hanxiao/ZCodeProject/iA-Writer`）
- **验证**：`python verify_ia_fonts.py`（元数据/字形覆盖/2:1 对齐共 32 文件全检）

### 脚本结构（iA 部分）

1. `prepare_ia_sources.py` — 可变字体实例化 + Nerd 图标差集提取注入 → `IASources/`
2. `merge_ia_ff.py` — FontForge 阶段（`fontforge -script merge_ia_ff.py {Mono|Duo|Quattro} [half]`）
3. `post_process_ia.py` — FontTools 合并 + 元数据精控（直接 fontTools API，不走 ttx 往返）
4. `build_ia_fonts.sh` — 串联全流程

## 安装（开箱即用）

```bash
./install_fonts.sh        # 安装 iA 系列（默认）
./install_fonts.sh jb     # 安装 JetBrains 系列
./install_fonts.sh all    # 全部
```

脚本会安装字体到 `~/.local/share/fonts/` 并部署 `fontconfig/66-miwith-mono.conf` 到 `~/.config/fontconfig/conf.d/`。

**为什么必须带 fontconfig 规则**：fontconfig 靠实测字形宽度判定等宽，CJK 合并字体有全角/半角两种宽度，会被判为 dual 而非 mono——GNOME 终端等只列等宽字体的软件因此不显示它们（字体文件里的 `isFixedPitch`/PANOSE 声明对判定无效，已实验证实）。规则在扫描阶段强制声明 `spacing=100`。这是 Sarasa Gothic 等同类字体的标准做法。

### 许可证注意事项（iA 附加条款）

iA Writer 字体除 OFL 外附加：**禁止将字体捆绑进文本编辑器或作为其默认字体分发、禁止改名微改后分发**。本产出为个人自用的合并字体，请勿再分发；产出家族名避开保留名 "iA Writer"（OFL RFN 要求）。

1. 使用脚本参考 [**PlemolJP**](https://github.com/yuru7/PlemolJP) 项目， 针对JetBrains Mono NF 做了特殊处理
2. 按照**中英文比例**分为两类，调整字形（半角字宽528）达到**2：1对齐效果** 以及 不调整字形的版本
3. 按照**是否支持连字** 分为两类， Mono 以及 MonoNL
4. 这个项目生产的字体个人**主要用于某些不支持设置多个字体的软件**
5. 本人不是纯字体作者，只是将 JetBrains Mono NF 与 MiSans 字体进行融合，并针对中文比例进行了调整，没有修改字形，请勿用于商业用途。


## 技术实现

### 参考项目
基于 **PlemolJP** 项目的字体合并方法，该项目成功融合了 IBM Plex Mono 和 IBM Plex Sans JP 字体。

### 主要工具
- **FontForge**: 用于字形处理和基本字体操作
- **FontTools**: 用于字体合并和表格优化
- **ttfautohint**: 用于字体提示优化
- **Python**: 自动化脚本编写

### 合并策略
1. **英文字符**: 使用 JetBrains Mono NF 作为基础
2. **中文字符**: 使用 MiSans 作为补充
3. **特殊符号**: 根据上下文选择合适的字体
4. **重复字符处理**: 避免冲突，确保显示一致性

### 字体特性
- **等宽设计**: 英文字符保持等宽，适合编程使用
- **多字重支持**: 从 Thin 到 Bold 的完整字重系列
- **斜体支持**: 提供斜体和粗斜体变体
- **连字特性**: 分为带连字和不带连字两个版本
- **优化显示**: 使用字体提示技术提高屏幕显示效果


## 注意事项

1. **字体大小**: 每个字体文件约 10MB，请确保有足够的存储空间，按需安装
2. **兼容性**: 字体基于 TrueType 格式，兼容主流操作系统
3. **许可证**: 请遵守原始字体的许可证条款

## 已知问题
1. **Nerd Font icon和其他字符混排问题**，icon + " " + 中文/英文字符，看起来比较协调，但是 icon + 中文/英文字符，看起来不协调，经测试，JetBrains Mono NF 字体本身有这个问题，后续我会想办法处理
