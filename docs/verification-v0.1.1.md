# H1 PAL v0.1.1 全屏与 Steam 资源验证

历史记录：v0.1.2 已改为扩展地图后等比例全屏；当前 `evidence/` 图片对应新版。

日期：2026-10-19。未连接或操作物理 H1。

正式 BDA：`dc1a6c7e80c906b922cde94a3d448fa530716d22dfd7f8871c09cd3e23148708`，
2411976 字节；测试 BDA：
`3cce8d0f31d615d746b8ae6fd7f32f6a2b51fb06d26f1bf983b4594a5d3d3b52`。

## 全屏显示

v0.1.1 默认将完整 320×200 游戏画面缩放到 480×272，地图、菜单、文字、战斗和 AVI 共用同一显示区域。
已关闭 SDLPAL 的旧 240 行上下留边逻辑：`PAL_SCALE_SCREEN=TRUE`，避免 320×200 画布被再压缩成 320×160。
V 依次切换全屏、435×272 等比例、320×200 原尺寸。没有改变游戏内部的地图尺寸或逻辑坐标。
触摸位置依据当前宽高和偏移反算，原始黑边区域不会触发地图点击。

实际 MIPS 二进制测试 `tests/display_controls.py` 覆盖：

- 默认画面覆盖 LCD 左上角和右下角；
- 从核心 gpScreen 调用 VIDEO_UpdateScreen，整幅白色游戏画布必须覆盖 LCD 四角；此测试能复现并阻止旧上下留边回归；
- 连续两轮三模式切换，按住 V 不重复触发，静态画面立即重绘；
- RGB555 AVI 四角分别保持红、绿、蓝、白；
- 三种模式的触摸边角都映射到对应的游戏坐标；
- 关闭窗口后无残留文件句柄。

报告：`build/verification/display-controls.json`。

## 完整 H1 固件

使用本机 H1 V1.41 固件、QEMU bbkh1、64 MiB 和独立 NAND，路径 `build/firmware-v011/`。
没有修改固件、Steam 安装目录或其他项目 NAND；沿用模拟器既有桌面壁纸回退。

实际结果：

- 启动原始 Steam PAL98 片头，标题菜单稳定停留；
- 读取旧存档，恢复对应客栈位置；
- 游戏模式 0，实际输出宽 480、高 272；地图非黑色内容包围框为 (0, 0, 480, 272)，上下没有统一黑条；
- 点击后 viewport 从 `13632736` 变为 `14681344`，partyoffset 保持 `7340192`；
- 静态菜单 V 切换顺序为 1 → 2 → 0，回到默认全屏；
- PCM 累计非零采样 37242，dropped=0、failures=0、应用 underruns=0；
- 组合键退出，窗口关闭，日志 END status=0，音量恢复为启动前的 51。

证据：`fullscreen-load.json`、`touch-fullscreen.json`、`verification.json`、`H1PAL.LOG` 和同目录 PNG。
可查看 [全屏地图](evidence/gameplay.png)、[全屏菜单](evidence/menu.png)。

## Steam 资源重打包

源目录为用户本机 Steam 的 PAL/PAL_DOS 和 PAL/PAL98。
21 个核心文件逐字节与旧主包一致，重新打包后主包 SHA-256 也保持一致。
原版游戏使用 320×200 逻辑画面；核心资源重打包不会提高地图、人物和文字的固有分辨率。

六段原始 AVI 都是 288×180、15 fps、MS Video 1。没有再次编码视频画面；
仅对容器执行兼容性检查/规范化。每段原片和输出片经过 FFmpeg 完整解码，图像 SHA-256 一致。
嵌套 LIST rec 中的实际流块均检查边界，最大块分别为 57900、56594、58310、54302、58322、58310 字节。

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| PAL9588.PAK | 27168336 | `18af405d5ee7e0f31148a4bc6733bba6d2cf141ba1b7f1e2fb49ec52e4dc3e30` |
| PALVIDEO.PAK 原画质 | 188810064 | `2ed4556a9f71794c0129dc726634fca78fbf7a97ab0dac1f2beb413733b4df73` |

原视频 1、2 在完整固件中实际播放。视频 3～6 在 MIPS 测试中各解码显示 3 帧后跳过，全部 PASS；
这项测试只证明抽样解析和解码，不代表完整播放或结局脚本通关。

完整安装包使用 Steam 原视频；可选精简安装包继续使用先前 12 fps、33134352 字节视频包。
两种安装包的 BDA 相同，都默认全屏。游戏存档不进入安装包。

## 复现

```powershell
python tools/build.py
python tools/build.py --regression
python tests/display_controls.py
python tests/mips_smoke.py --limit 8
python tests/steam_video.py
python -X utf8 h1-pal/tools/prepare-steam.py --steam-root '你的 Steam PAL 目录'
```

主包无视频启动的 MIPS 模型运行 8 帧并正常返回，文件句柄与堆分配均无残留。
既有存档、战斗和音频流程测试见 [v0.1.0 验证](verification-v0.1.0.md)。
未进行真机性能、真机音画同步、全剧情或长时间稳定性验证。
