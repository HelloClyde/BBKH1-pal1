# H1 PAL v0.1.7 视频压缩与播放验证

日期：2026-10-21。正式 BDA 2511928 字节，SHA-256：
`876dee798414d7bf4f4962305fbf737ce81d86b588b9b5988e9c2db86dc0021d`。
测试 BDA：`d9c1f34072920ba2858adb504e35fbbda42af4a5c42bf0ccc08dae8d04d2ed2d`。
完整结果见 [发布验证记录](evidence/release-v0.1.7.json)，
此前操作与配乐修复见 [v0.1.6 记录](verification-v0.1.6.md)。

## 编码与资源

参考 H1 飞天影音中的 MPlayer/libavcodec 及其 H.264、MPEG-4 解码器注册记录。
原程序 SHA-256 为 `b964eb9ca0ef7172933d079e7209b7ae6e69cc4cd29c675814fcf348ea1853d0`。
游戏使用独立编译的 [H264BSD](https://github.com/oneam/h264bsd)，
固定提交 `42bcb5d753ad86d84903354bf3c68423c28adb7b`；未复制飞天影音二进制。

六段 AVI 重新编码为 H.264 Constrained Baseline、CRF 18、单参考帧、无 B 帧，
保留 288×180、15 fps、6385 帧及全部原始 PCM 音频样本。
`PALVIDEO.PAK` 从 188810064 字节降至 43815104 字节，缩小 76.79%。
六段视频 SSIM 为 0.979～0.997；这是有损视频编码，音频样本哈希与原文件一致。
主包 `PAL9588.PAK` 与此前版本逐字节相同，存档与配置格式不变。

新版程序兼容旧 MS Video 1 包；新版 H.264 包须配合 v0.1.7 或更高版本程序。
AVI 保持原画幅等比显示，游戏地图和菜单仍为 480×272。

## 解码与回归

主机编译同一份 H264BSD，逐帧核对全部 6385 帧的 YUV 输出，结果与 FFmpeg 逐字节相同。
实际 MIPS 正式 BDA 另用原创测试图形和音频检查：8 帧 RGB555 输出、PCM 非零、
重新打开重置、取消跳过、非 Baseline 输入失败和资源回收，全部通过。
测试 BDA 对六段新版及六段旧版 AVI 分别抽样 8 帧，全部通过。

播放器使用绝对帧截止时间，避免逐帧处理开销累积至长视频时间线。
缓存视频缩放坐标，减少逐像素除法；颜色转换采用整数 BT.601 和共享色度采样。
方向、确定、取消、被移除的快捷键、视频边角与触摸坐标、宽屏菜单与战斗背景、
原创 RIX 配乐合成、七种 A/B 资源选择、缺失资源和 PAK 结构检查均通过。

## 完整 H1 固件

独立私有 H1/Y100 V1.41 NAND，QEMU bbkh1、64 MiB，A 盘装载上述正式 BDA 与新视频包。
两段片头自然播放结束：258 帧耗时 17203 ms，920 帧耗时 61337 ms；
原时间线分别为 17200 ms 和约 61333 ms。
这证明该固件模拟器中的播放与时间线正常，不代表物理 H1 的解码速度。

在第一段 H.264 片头仍播放时，从模拟器实际 AIC/PCM 输出采集约 3 秒音频：
32000 Hz、双声道 96320 帧，峰值 15605、RMS 3497.18，68.86% 样本非零。
主菜单与旧存档地图均为 480×272；长按确定与取消后退出状态 0，恢复原系统音量。
日志中应用音频 dropped/failures/underruns 均为零。本次专用模拟器已停止。

[H.264 片头](evidence/v0.1.7-h264.png) · [主菜单](evidence/v0.1.7-title.png) ·
[旧存档地图](evidence/v0.1.7-map.png)。未进行物理真机测试或全剧情通关。

## 复现

```powershell
python tools/build.py
python tools/verify_release.py
python tests/h264_video.py
python tests/display_controls.py
python tests/music.py
python tests/data_drives.py
python tests/wide_ui.py
python tests/wide_battle.py
python tests/mips_smoke.py --missing
python -m unittest discover -s tests -p "test_*.py"
```

本地自有资源重新打包使用 `tools/prepare-steam.py`，默认生成 H.264 视频；
`--video-codec original` 保留旧视频编码。
自有视频抽样使用 `python tools/build.py --regression`，再运行 `tests/steam_video.py`；
`--resources` 指向包含两个 PAK 的目录，`--report` 可分别保留新旧包检查结果。
公共 CI 使用原创测试素材，不含私有游戏资源或固件。
