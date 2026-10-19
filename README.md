# 仙剑1 for BBK H1 / Y100

基于 SDLPAL 的原生 H1 BDA，参考 HelloClyde 的 BBK9588-pal1 移植。
适用于 H1 / Y100 V1.41，默认 480×272，应用名称为“仙剑1”。v0.1.4 为首次公开预发布。

## 快速开始

从本项目 Releases 下载 `仙剑1.bda` 或程序安装 ZIP。
ZIP 只包含程序与说明；游戏资源由使用者从自己拥有的原版准备。
已有上一版资源的用户只需替换 BDA，存档兼容。

```text
A:\应用\程序\仙剑1.bda
A:\应用\数据\PAL\PAL9588.PAK
A:\应用\数据\PAL\PALVIDEO.PAK    （可选）
```

将程序与资源放到上述路径，重新进入 H1 桌面后点击“仙剑1”。
缺少视频包时使用 DOS RNG 动画；主资源包必需。
使用 `build/resources/` 中自己准备的资源进行测试与本地打包。

### 从 Steam 安装目录准备资源

需要 Python 和 PATH 中的 FFmpeg。传入自己的 PAL 安装目录：

```powershell
python tools/prepare-steam.py --steam-root "D:/SteamLibrary/steamapps/common/PAL" --output build/resources
```

工具读取 `PAL_DOS` 的 21 项核心数据和 `PAL98` 的六段 AVI，生成两个 PAK。
AVI 保留原始 288×180、15 fps 画面，只规范容器字段，不再次有损编码。
也可通过 `tools/palpak.py pack <数据目录> <输出PAK>` 打包，或复用兼容的旧 PAK。
资源格式与详细来源见 [NOTICE.md](NOTICE.md)。公共仓库和 Release 不包含原版游戏资源、存档或固件。

存档为同目录 `1.rpg`～`5.rpg`，配置为 `sdlpal.cfg`，日志为 `H1PAL.LOG`。

## 截图

以下为本项目实际运行截图；均来自模拟器，没有物理真机截图。

| H1 完整固件：桌面图标 | H1 完整固件：启动菜单 |
| --- | --- |
| ![H1 桌面图标](docs/evidence/desktop-icon.png) | ![启动菜单](docs/evidence/title-icon-revision.png) |

| H1 完整固件：地图 | H1 完整固件：仙术 |
| --- | --- |
| ![地图](docs/evidence/gameplay.png) | ![仙术](docs/evidence/ui-magic-aligned.png) |

![战斗，完整 H1 固件模拟器](docs/evidence/battle-firmware.png)

桌面和启动图对应本次图标修订；地图、仙术与战斗图对应此前的已记录构建，具体哈希与范围见验证文档。

## 操作

| 按键 | 功能 |
| --- | --- |
| 方向键 | 移动、菜单选择 |
| Enter / 确认 / Z / 空格 | 调查、确认、推进对话 |
| Esc / X | 打开菜单、取消、返回 |
| V | 全屏（默认）→ 标准视野等比例 → 320×200 原尺寸 |
| 同时长按 Enter + Esc | 退出应用并返回 H1 桌面 |
| 点击地图目标 | 绕开障碍自动行走；点击可调查对象可走近调查 |

实体方向或确认/取消会中断自动行走。剧情、对话、菜单和战斗期间不启动触摸寻路；
滑动和画面黑边不会当成地图点击。游戏中通过“系统 → 储存进度 / 读取进度”存读档。

## 实现

- 完整地图、脚本、对话、道具、战斗和原生存档核心。
- 地图视口扩为 **360×204**，横纵都按 **4/3** 倍显示到 **480×272**；
  相对原视野左右各多显示 20 个地图像素、上下各多 2 个。人物、地砖和地图上的菜单保持相同比例。
  新区域包含 NPC 与遮挡层，也支持触摸寻路；游戏逻辑坐标、剧情触发、碰撞和存档格式不变。
- 战斗背景单独等比放大到 360×225，再从上下居中裁取 360×204；
  原图上下各约 9 行不显示，左右完整保留。背景在 LCD 上等比放大 1.5 倍，
  人物、敌人、文字和技能保持与地图相同的 4/3 比例，无横向拉伸。
  战斗切换/淡入、调色板闪光、水波、震屏与跨出旧画幅的 RLE 效果使用完整宽度。
  直接沿用原始 FBP 图片，不需要重新打包游戏资源。
- 启动、存读档、状态、装备、仙术、物品、商店和确认菜单均使用完整 480×272 画布。
  启动背景等比铺满；状态和装备背景补齐边缘纹理，保留原有头像、装备格和标签尺寸。
  仙术/物品的选择光标移到文字左侧，不再覆盖字形；装备列表名称对齐背景标签，状态页名称按图标格居中。
  字体、头像和图标横纵都按 4/3 显示，没有单独拉宽。
- AVI 视频保留原画幅等比显示。
  V 可回到原始 320×200 地图视野的等比例或原尺寸显示，不再提供非等比拉伸。
- 480×272、32 位 H1 游戏帧缓冲；调色板游戏和 RGB555 AVI 均保持横屏方向。
- RIX/DBOPL 音乐、VOC/WAV 音效；22050 Hz 单声道混音经整数重采样输出至
  H1 的 32000 Hz PCM 环形缓冲；退出时停止 PCM 并恢复原音量。
- SDLPAL Microsoft Video 1 解码器播放六段可选 AVI，不调用 9588 或 H1 私有播放器。
- H1 文件、内存、游戏窗口、校准触摸和同时按键接口；没有链接 9588 SDK。
- 独立 512 KiB 栈，退出统一关闭容器句柄并回收本应用分配的内存。

## 依赖

| 用途 | 依赖与固定版本 |
| --- | --- |
| 运行 | BBK H1 / Y100 V1.41；使用者自己的仙剑 DOS 核心资源，PAL98 视频可选 |
| 引擎子模块 | [SDLPAL](https://github.com/sdlpal/sdlpal)，`224cb0a0cc839e0e8ecaa299cd480b02b372b9f7` |
| SDK 子模块 | [H1 BDA SDK](https://github.com/MrDefinition1999/bbk-h1-bda-sdk)，`067fe072477861dfc8949d7b1a55279fb92d2548`，目录 `sdk/` |
| 已验证开发环境 | Windows x64，Python 3.11.5；GNU MIPS little-endian soft-float GCC 15.2.0；Actions 配置为 Python 3.12 |
| Python | Pillow 12.3.0（图标打包），Unicorn 2.1.4（主机 MIPS 服务模型测试） |
| 可选资源生成 | FFmpeg（需放入 PATH）；原版游戏安装文件 |

依赖固定信息见 [UPSTREAM.json](UPSTREAM.json)，工具链压缩包 URL 与 SHA-256 见 `tools/install_toolchain.py`。
正常编译无需下载游戏资源，也无需系统字体；图标 PNG 已保存于 `assets/`。
核心子模块的 SDL、GoogleTest 等嵌套依赖不参与此原生移植，不必递归初始化。

## 开发构建

在 Windows PowerShell 中执行；每步失败应停止：

```powershell
git submodule update --init sdk third_party/sdlpal
python -m pip install -r requirements.txt
python tools/install_toolchain.py
python tools/build.py
python tools/verify_release.py
```

输出为 `dist/仙剑1.bda`，`H1PAL.bda` 为内容相同的兼容副本。
已有工具链可使用 `python tools/build.py --toolchain C:/tools/mipsel-none-elf/bin`，或设置 `H1_GNU_BIN`。
构建器校验子模块提交及干净状态；固定 `SOURCE_DATE_EPOCH=1792368000`，避免 SDLPAL 的编译日期破坏可复现性。
入口固定 `0x83C00020`，镜像、BSS 和独立 512 KiB 栈不超过 H1 的 4 MiB 加载窗口。
`tools/core_overrides.py` 从未修改的核心生成带上下文校验的 H1 场景、战斗及菜单适配副本。

资源无关测试（Actions 中也执行）：

```powershell
python -m unittest discover -s tests -p "test_*.py"
python tests/wide_ui.py
python tests/wide_battle.py
python tests/display_controls.py
python tests/mips_smoke.py --missing
```

本地真实游戏资源测试使用 `build/resources/PAL9588.PAK`；菜单与地图测试还需要使用者自己的
`build/verification/native-1.rpg`。可用 `python tools/build.py --regression` 构建独立测试 BDA；
正式 BDA 不执行测试标记。视频抽样测试使用 `build/steam-resources/`。上述数据不随仓库分发。

提交源码后执行 `python tools/package_release.py` 可生成程序安装 ZIP、含两项固定依赖的完整源码 ZIP、
BDA、构建信息、验证清单及 SHA256SUMS；此公开打包入口不读取游戏资源。
`tools/package.py --resources build/resources` 只用于个人本地生成含自有资源的完整安装包，请勿作为公共 Release 上传。
源码 ZIP 已展开构建必需子模块，可跳过子模块初始化直接执行安装依赖、安装工具链和构建命令；
构建器按 `SOURCE-MANIFEST.json` 校验依赖文件哈希。开发与更新请优先使用 Git 克隆。

## 验证范围

当前 BDA SHA-256：`0d95916daebcec5f70cac0bca37d9c5804dafac7fe8512aea566f877955ac20b`。
2026-10-20 的独立构建与完整 H1 固件中已检查图标、名称、启动和退出的程序逐字节相同。
主机模型实际执行编译后的 MIPS 代码，检查 UI、战斗背景、模式/触摸和缺资源退出；它不能代替完整固件测试。
此前地图、战斗、存档、视频与 13 类菜单的检查及不同构建哈希均保留在
[当前验证](docs/verification.md) 和 [菜单验证](docs/verification-v0.1.4.md)。

Actions 在 main、PR 和手动运行时编译、校验并保存临时产物；`v*` 标签触发预发布，
Release 使用同一构建产物。CI 不执行私有固件，也不宣称物理真机测试通过。
**尚未进行物理 H1 测试或全剧情通关。**

## 许可与感谢

本移植源码按 GPL-3.0-or-later 提供，第三方文件保留原许可；详见 [LICENSE](LICENSE)、[NOTICE.md](NOTICE.md)。
游戏素材、名称和商标的权利归原权利人，文档截图不改变这些权利。

感谢 [HelloClyde/BBK9588-pal1](https://github.com/HelloClyde/BBK9588-pal1) 提供 9588 参考移植与兼容层、PAK、AVI 和寻路实现；
感谢 SDLPAL 及 AdPlug/OPL、FFmpeg 相关贡献者；感谢 MrDefinition1999 的 H1 BDA SDK。
图标通过内置 GPT Image 重新设计，保留原红色“仙”字主体，参考 H1 桌面图标；提示词、参考图和来源记录在 `assets/`。
