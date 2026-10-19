# H1 PAL v0.1.4 菜单全屏与对齐验证

本地验证记录。未连接或操作物理 H1。

正式 BDA：`376f81a83a8b9c1c12a2f1c77464eb346e3bd9da717a608fec1f00d058a0d05a`，
2418556 字节；测试 BDA：
`a797dc2889eba5dce628b21ce5834219d6310d583a9d920b6b54a8a527eee5ce`。

## 菜单显示方式

启动主菜单、存读档、人物状态、装备、仙术、物品、商店和确认窗口均采用 360×204 的画布，
横纵统一按 4/3 显示到 480×272，不再退回 435×272 的固定画幅显示。

启动背景按与战斗相同的等比覆盖方式铺满；状态/装备原图包含装备格和文字，
因此完整保留中央 320×200 像素，只把无内容的边缘纹理延伸到新增区域。
头像、装备图、汉字和数字不参与背景的覆盖缩放，保持相同比例与原有格位。
UI 画布独立于地图和战斗分类，备份、局部刷新及界面返回均保存对应边缘。

V 仍可主动切换标准视野等比和原尺寸；默认模式为全屏。
AVI 视频继续保留原片比例，不属于本次菜单排版变更。

## 光标与装备名称

仙术/物品列表的原指针画在汉字下部，覆盖 16 像素字体。
现改为左侧右指三角，按字高垂直居中，不再占用文字区域；任意行列使用相同的文字锚点。

默认装备页的名称坐标对齐原 DOS 背景标签的 y=10+22×行号，名称起点保留标签间距。
状态页装备名称按实际字宽在 50 像素图标格下居中，并限制在画面内。
用户自定义布局保持其配置坐标。

[仙术修正截图](evidence/ui-magic-aligned.png) 来自完整固件正式 BDA。
[装备修正截图](evidence/ui-equipment-aligned.png) 来自实际 MIPS 测试 BDA，带未保存的菜单测试物品。

## 实际 MIPS 验证

`tests/ui_menus.py` 执行真实引擎菜单循环，以原生 H1 按键逐一取消并返回：
启动、状态、装备、读档槽、游戏主菜单、物品子菜单、物品列表、
仙术列表、施术者、道具目标、确认窗口、购买、出售，共 13 类。
每类实际尺寸均为 480×272、逻辑画布均为 360×204；结束无残留句柄、分配或音频/窗口资源。
截图在 `build/verification/ui/`，尺寸与构建哈希在 `ui-menus.json`。

正式 BDA 的 `tests/wide_ui.py` 逐像素检查：
状态/装备中央背景不变、标题等比覆盖、LCD 四角采样、备份恢复、边缘图标和三模式切换。
光标检查覆盖不同行列，确认三角形完全位于文字左侧，没有改变字形区域。
报告为 `wide-ui.json`。

本版还通过地图逐像素对照/边缘 NPC/触摸、战斗全屏与获胜、存档重启读回、
Steam 3～6 号视频抽样解码、主包启动/退出和缺资源退出检查。
报告保留在 `build/verification/`，哈希对应上列正式或测试构建。

## 完整 H1 V1.41 固件

QEMU bbkh1、64 MiB、独立 NAND：`build/firmware-v014/`。
使用正式 BDA，哈希与上列相同，读取既有存档，无菜单测试标记。

实际确认：

- 原视频启动后，标题主菜单和读档槽输出 480×272；
- 旧存档读取后地图、游戏主菜单、人物状态、仙术、系统及存档槽均为 480×272；
- 仙术光标位于名称左侧，状态页装备名称居中；
- 状态页 V 依次切换 435×272、320×200、480×272，立即重绘；
- 返回地图正常，组合键退出后 opened=0，回到桌面；
- 日志 END status=0、951 帧，音频 dropped=0、failures=0、underruns=0，恢复原音量 51。

该旧存档没有背包内可装备物品，正式 BDA 的装备列表为空；装备详情页的内容/名称检查使用上述 MIPS 菜单测试。
没有把空列表截图当作装备详情页的验证。

尺寸记录：同目录 `title.json`、`load-slots.json`、`status.json`、`magic-list.json`、
`system-menu.json`、`save-slots.json`、`status-mode-*.json`、`exit-desktop.json`、`H1PAL.LOG`。
可查看 [主菜单](evidence/title.png)、[状态页](evidence/ui-status-fullscreen.png)。

## 复现

```powershell
python tools/build.py
python tools/build.py --regression
python tests/wide_ui.py
python tests/ui_menus.py
python tests/wide_battle.py
python tests/wide_scene.py
python tests/battle.py
python tests/display_controls.py
python tests/save_roundtrip.py
python tests/steam_video.py
python tests/mips_smoke.py --limit 8
```

菜单流程测试依赖私有 `build/verification/native-1.rpg` 和用户游戏资源，不随源码或安装包分发。
旧记录见 [v0.1.3](verification-v0.1.3.md)、[v0.1.2](verification-v0.1.2.md)。
未进行物理 H1 性能、全剧情或长时间稳定性验证。
