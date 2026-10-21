# H1 PAL v0.1.9 系统菜单验证

日期：2026-10-21。正式 BDA 2516928 字节，SHA-256：
`8bf2d9a7df8c637243e864c733d1a1591c103661fc2da8040f88f50bc41230e2`。
详细结果见 [发布验证记录](evidence/release-v0.1.9.json)。
固定依赖与改键配置格式不变；持久化及恢复默认的此前完整固件记录见 [v0.1.8](verification-v0.1.8.md)。

“按键映射”直接放在系统菜单，位于音效之后、结束游戏之前。
结束游戏恢复原来的否/是确认，移除额外的系统设置页。
菜单值、记忆选中位置、行数和文本位置同时调整；六行均处于完整 480×272 画面内。
现有 `h1keys.cfg`、原画风、六动作改键与 A/B 同盘保存保持不变。

## 实际 MIPS

`tests/settings_ui.py` 使用自有资源，从真实游戏主菜单选择系统，
检查系统菜单恰有六项，直接进入按键映射，修改确定/取消为 X/Z 后返回。
单独调用结束游戏时，检查原来的两项是否菜单，并通过新的取消键返回。
同时核对 480×272、原背景逐字节恢复和页面分配回收。全部通过。

六动作事件/持续按住、重复绑定交换、固定设置页操作、A/B 保存及新实例读取、
配置错误处理和物理紧急退出检查通过。
显示、宽屏 UI/战斗、原创 RIX、原创 H.264、A/B 资源选择、缺资源与 PAK 检查也全部通过。
资源无关检查在公共 CI 执行；真实菜单素材仅用于本地自有资源测试。

## 完整 H1 固件

独立私有 H1/Y100 V1.41 NAND，QEMU bbkh1、64 MiB，A 盘安装上述正式 BDA。
从桌面启动、跳过过场、读取旧存档，在地图打开系统菜单，直接进入按键映射。
修改按键后返回游戏，再检查结束游戏的否/是确认并正常退出。
画面均为 480×272。专用测试模拟器已停止；未进行物理真机测试或全剧情通关。

[系统菜单](evidence/v0.1.9-system-menu.png) · [按键映射](evidence/v0.1.9-keymap-default.png) ·
[退出确认](evidence/v0.1.9-quit-confirmation.png)。

## 复现

```powershell
python tools/build.py
python tools/verify_release.py
python tests/keymap.py
python tests/display_controls.py
python tests/wide_ui.py
python tests/wide_battle.py
python tests/music.py
python tests/h264_video.py
python tests/data_drives.py
python tests/mips_smoke.py --missing
python -m unittest discover -s tests -p "test_*.py"
```

自有资源另执行 `python tests/settings_ui.py --resources build/resources/PAL9588.PAK`。
公共源码与 CI 不含私有游戏资源或固件。
