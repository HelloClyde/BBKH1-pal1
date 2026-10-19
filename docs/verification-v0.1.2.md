# H1 PAL v0.1.2 扩展地图视野验证

历史记录：v0.1.3 已增加战斗全屏；当前 evidence 中的战斗图对应新版。

日期：2026-10-19。未操作物理 H1。

正式 BDA：`ffe57b85f5317769a531f0ab048d9650c746fb64a85e32719382e75670f0fd67`，
2415076 字节；测试 BDA：
`e9e4fc867d497fa0d239c3723f571cae0dba6c839b22e5d1d7fb4becc3f66157`。

## 显示方式

地图实际渲染 360×204，横纵统一按 4/3 倍采样到 480×272。
旧视野 320×200 保留在新画布的 (20, 2) 位置，额外区域绘制真实地图、NPC 和遮挡层。
菜单/对话仍使用旧逻辑坐标，覆盖在地图中央；没有放宽碰撞、调查或剧情触发范围。
渲染后立即还原 viewport 和队员坐标，存档格式不变。

V 切换扩展地图全屏、原视野等比例、原视野原尺寸。标题、人物状态背景、战斗背景及 AVI
只有原有固定画幅，使用等比例显示，允许左右留边。已移除非等比拉伸模式。
本版战斗实际内容为 435×272，左侧 22、右侧 23 像素黑边，尚未扩展战斗背景。

## 实际 MIPS 对照测试

`tests/wide_scene.py` 执行真实测试 BDA，用同一旧存档依次渲染扩展视口和原视口：

- 中央 320×200 地图逐像素一致；整幅 LCD 与横纵同为 4/3 的采样结果逐像素一致；
- 渲染前后 viewport、队员坐标和姿态不变；
- 将 NPC 中心移到旧视口外，新增左侧区域仍能画出该 NPC；
- 固定背景不使用地图边缘；恢复备份后整幅地图一致；
- 16×16 局部 UI 刷新保持地图边缘，防止打开菜单时缩回旧视野；
- 三模式触摸反算通过，扩展画面两角对应旧坐标 (-20, -2) 与 (339, 201)；
- 255 级水波效果、震屏保持扩展地图；战斗不沿用地图边缘；
- 正常关闭，无残留分配或文件句柄。

报告：`build/verification/wide-scene.json`，全通过。
`tests/display_controls.py` 另覆盖 V 按下沿、静态画面即时重绘、固定画幅/AVI 四角和触摸反算。

本版另通过实际 MIPS 存档写入后重新启动读回（183488 字节）、自动战斗获胜（181 帧）、
Steam 3～6 号 AVI 各解码 3 帧、缺资源提示退出及主包启动清理测试。
记录分别为 `save-roundtrip.json`、`battle.json`、`steam-video.json`、`missing.json`、`mips-smoke.json`。
对应上列正式或测试构建；模型不能代替真实硬件时序。
[战斗截图](evidence/battle-model.png) 为实际 MIPS 执行结果，未在完整固件中触发本版战斗。

## 完整 H1 V1.41 固件

64 MiB QEMU bbkh1，独立 NAND：`build/firmware-v012/`。正式 BDA 哈希与上列一致。
保留原 Steam 资源和旧存档，没有修改 Steam 安装目录或其他模拟器实例。

实际结果：

- 原 Steam 视频启动，标题菜单正常；读取旧存档回到客栈；
- 默认逻辑画布 360×204、LCD 输出 480×272、`map_full=1`；
- 打开主菜单后仍为扩展视口，V 切换 1 → 2 → 0；
- 点击新增左侧区域物理坐标 (12, 160)，viewport 从 13632736 变为 14156848，
  partyoffset 保持 7340192，触摸计数加一；
- 组合键退出后 `opened=0`，回到桌面。

起始客栈截图右侧约 26 个黑色像素来自房间外的地图黑底：
移动前 RGB 内容边界为 (0, 0, 454, 272)，移动后为 (48, 0, 480, 272)。
右侧确实能画到第 480 列，黑色区域随地图移动，不是固定显示留边。

证据：同目录 `expanded-map.json`、`menu-expanded.json`、`mode-*.json`、
`before-touch.json`、`after-touch.json`、`exit-desktop.json`、`H1PAL.LOG` 和 PNG。
可查看 [扩展地图](evidence/gameplay.png)、[地图菜单](evidence/menu.png)、
[移动后地图](evidence/touch-walk.png)。

## 复现

```powershell
python tools/build.py
python tools/build.py --regression
python tests/wide_scene.py
python tests/display_controls.py
python tests/save_roundtrip.py
python tests/battle.py
python tests/steam_video.py
python tests/mips_smoke.py --limit 8
python tests/mips_smoke.py --missing
```

扩展地图测试使用私有 `build/verification/native-1.rpg`，不随源码或安装包分发。
资源内容、AVI 解码图像哈希和来源见 [v0.1.1 验证](verification-v0.1.1.md)。
尚未测试物理真机速度、真机音画同步、全剧情或长时间稳定性。
