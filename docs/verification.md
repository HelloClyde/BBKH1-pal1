# H1 PAL v0.1.8 按键映射验证

日期：2026-10-21。正式 BDA 2518032 字节，SHA-256：
`881cb875ad2cc0d63bf8536fe8127ea8e14d63b8575a83568aaecf5271bd2a10`。
详细结果见 [发布验证记录](evidence/release-v0.1.8.json)。
SDK、引擎和 H264BSD 仍使用原来的固定提交；视频验证见 [v0.1.7 记录](verification-v0.1.7.md)。

## 菜单与操作

从“系统 → 结束游戏 → 系统设置 → 按键映射”进入，设置六个动作：上、下、左、右、确定、取消。
改键等待输入时，跳出会取消；重复绑定交换两个动作的按键，支持恢复默认。
页面直接使用原版边框精灵、像素字体、选中颜色动画和当前调色板。
面板、文字与光标在 480×272 下等比显示，关闭后完整恢复原来的游戏背景。

设置页固定使用 H1 的原方向、输入和跳出；离开设置页后恢复玩家映射。
长按物理输入+跳出的紧急退出组合不受映射影响，默认无操作的字母键只有主动绑定后才生效。
捕获新键同时支持事件与持续按住查询，归一化共享扫描码的按键别名。
映射切换前等待物理按键松开并清理输入状态，避免按键残留到下一层菜单。

## 存储与错误处理

`h1keys.cfg` 保存到选定 A/B 资源盘，启动时读取，独立于 `sdlpal.cfg` 和游戏存档。
配置版本、键值或唯一性检查失败时使用默认映射。
写入失败会提示重试，运行中的映射保持原值。
主资源、视频包及存档格式没有变化，本版只需更新 BDA。

## 实际 MIPS 检查

`tests/keymap.py` 执行正式 BDA 的以下路径：六动作改键；事件与持续按住；重复绑定交换；
设置页固定操作；原始捕获和别名；A/B 同盘保存；新实例读取；恢复默认；
损坏配置回退；写入失败；物理紧急退出与无泄漏回收。全部通过，可在公共 CI 中运行。

`tests/settings_ui.py` 使用本地自有主资源执行真实菜单循环，
从三选退出菜单进入设置，改用 X/Z 确定/取消，再返回原退出菜单。
核对实际映射值、480×272、背景逐字节恢复及页面分配回收，全部通过。
该检查需要使用者自己的资源，不在公共 CI 中执行。
原有显示、宽屏 UI/战斗、原创 RIX 配乐、原创 H.264 视频、A/B 选择、缺资源与 PAK 检查也全部通过。

## 完整 H1 固件

独立私有 H1/Y100 V1.41 NAND，QEMU bbkh1、64 MiB，A 盘安装上述正式 BDA。
通过桌面启动、跳过过场、读取旧存档，在地图上进入退出菜单、系统设置和按键映射。
把确定和取消改为 X/Z，以 X 确认退出，重新从桌面启动程序后读取到相同映射。
再次进入设置检查显示，再恢复默认并从退出菜单关闭，窗口正常关闭。
上述画面均为 480×272；测试模拟器已经停止。
本次没有物理真机测试，没有重新执行全剧情或全部视频的完整播放。

[退出菜单](evidence/v0.1.8-quit-menu.png) · [系统设置](evidence/v0.1.8-system-settings.png) ·
[默认映射](evidence/v0.1.8-keymap-default.png) · [自定义映射](evidence/v0.1.8-keymap-custom.png) ·
[重启读取](evidence/v0.1.8-keymap-reloaded.png)。

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

有自有主资源时，可另执行 `python tests/settings_ui.py --resources build/resources/PAL9588.PAK`。
公共源码与 CI 不含私有游戏资源或固件。
