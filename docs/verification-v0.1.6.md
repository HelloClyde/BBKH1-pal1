# H1 PAL v0.1.6 操作与背景音乐验证

日期：2026-10-20。正式 BDA 2420112 字节，SHA-256：
`1370d668f617334fb2f09a1b1f74c45f6eb9e54ea5721991b16f600df7283a2a`。
测试 BDA：`42849acfc3af45b57728ce10083b1bfb4b5b48198d4648a5ddaf1bc566d88436`。
SDK 和引擎提交不变；详细结果见 [发布验证记录](evidence/release-v0.1.6.json)。

## 操作与显示

只保留方向、输入/确定、跳出/取消。Z、X、V、空格的事件与轮询路径均不触发游戏操作，
也不能切换画面尺寸。移除三种显示模式；地图、战斗与已适配菜单固定 480×272，
原有 4/3 等比绘制、地图扩展、触摸坐标、AVI 原画幅策略继续保留。
同时长按确定与取消仍可退出应用。

`tests/display_controls.py` 独立输入原生扫描码，检查六键按住、松开、被移除快捷键、
固定画面和视频边角/触摸坐标。UI 与战斗背景测试另外检查多次按字母键后仍全屏。
真实引擎地图测试通过扩展边缘、图层、水波、触摸与菜单恢复检查；13 类真实菜单均为 480×272；
自动战斗执行至胜利。后面三项使用独立测试 BDA 和用户自有游戏资源。

## 音乐修复与隔离检查

裸机 MIPS GCC 将 C++ 静态构造函数放入 `.ctors`；旧链接脚本只保留 `.init_array`，
导致 DBOPL 波形表和二进制流的初始化未执行。链接脚本现将两类入口放入对齐的初始化区，
由既有启动流程执行。

`tests/music.py` 默认生成原创单音 RIX，经过实际 MIPS 初始化、RIX 解析、DBOPL 合成和
SDLPAL 混音，且不播放任何音效。检查初始静音、配乐非零、音乐开关与停止、退出回收；可在公共 CI 运行。
该检查在修复前输出全零，修复后峰值 4072、RMS 2955.13。

使用自有主包另行检查曲目 4、31、37，峰值分别为 3559、8428、24727，均通过静音/恢复/停止检查。
不把视频音轨或音效的非零输出当作背景音乐通过。

## 完整 H1 固件

独立私有 H1/Y100 V1.41 NAND，QEMU bbkh1、64 MiB。正式 BDA 的主菜单、旧存档地图均为 480×272。
逐一验证六个物理矩阵按键对应的采样位；按住 Z、X、V、空格时采样为零，画面尺寸不变。

在地图曲目 31 播放且活动音效数为零时，从模拟器实际 AIC/PCM 输出采集约 3 秒音频：
32000 Hz、双声道 96256 帧，峰值 3905、RMS 813.41，99.83% 样本非零。
单声道游戏混音由固件音频输出为双声道。日志记录 4028 批混音、5502451 个非零样本，
应用音频 dropped/failures/underruns 均为零，退出状态 0、恢复原系统音量。
本次专用模拟器已经停止。

[主菜单](evidence/v0.1.6-title.png) · [地图](evidence/v0.1.6-map.png)。
本次完整固件只检查 A 盘；七种 A/B 主包选择与同盘读写检查在 MIPS 文件服务模型中通过。
此前 A/B 引擎存档重启读回见 [v0.1.5 记录](verification-v0.1.5.md)。
未进行物理真机测试或全剧情通关。

## 复现

```powershell
python tools/build.py
python tools/verify_release.py
python tests/display_controls.py
python tests/music.py
python tests/data_drives.py
python tests/wide_ui.py
python tests/wide_battle.py
python tests/mips_smoke.py --missing
python -m unittest discover -s tests -p "test_*.py"
```

本地自有资源可通过 `python tests/music.py --resources build/resources/PAL9588.PAK` 检查。
公共 CI 不含私有游戏资源或固件。
