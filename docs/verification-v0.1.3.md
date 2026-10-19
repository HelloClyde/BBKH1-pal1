# H1 PAL v0.1.3 战斗全屏验证

历史记录：v0.1.4 已增加菜单全屏和光标/装备名称对齐；当前菜单图片对应新版。

日期：2026-10-19。未操作物理 H1。

正式 BDA：`cb127f724386f0daed765dd23abebe847b5b3af3546c9f90348516e21cff9d6d`，
2417396 字节；测试 BDA：
`09a786313cbb29f6a4ed6a7ea3b0d6cb8002066091bd8a0018747759730d4737`。

## 背景与人物分别缩放

战斗背景来自原资源 `FBP.MKF` 的 320×200 调色板图片。
背景先横纵统一放大 9/8 为 360×225，再居中裁取 360×204，
上下各省略约 9 行原图，左右完整保留。按原调色板索引采样，没有新增颜色或重新编码资源。
此画布再统一按 4/3 显示到 480×272，背景最终横纵均为 1.5 倍。
人物、敌人、文字、菜单和技能仍按 4/3 显示，保持原来坐标和形状。

这是原画的等比覆盖与轻微上下裁切，没有生成原图之外的新场景。
地图继续采用真实扩展 360×204 的视野；标题、人物状态和视频保留原画幅等比显示。
V 仍可切换全屏、标准视野等比、320×200 原尺寸。

## 渲染流程

战斗背景、场景缓冲、屏幕和备份保存各自的扩展画布，且与地图画布区分。
普通全屏图片替换时清除关联，战斗结束后不会把战斗边缘带入地图。
RLE 普通、阴影、变色、单色四条路径同时绘制扩展区域，技能可越过旧 320 像素边界。
战斗切入、渐变、调色板变色、持久技能印记、背景水波和震屏均使用完整宽度。
没有改变敌我位置、战斗数值、操作逻辑、碰撞或存档格式。

## 实际 MIPS 验证

正式 BDA 的 `tests/wide_battle.py` 使用两种不同的坐标格，逐像素验证：

- 背景 X/Y 使用同一 9/8 比例，中央裁片与引擎缓冲一致；
- 输出四角到达 LCD 边缘，完整画布采用同一 4/3 采样；
- 8×8 RLE 跨出旧视口后仍保持形状，四种 RLE 路径一致；
- 战斗切换、全宽调色板偏移、255 级水波与三模式静态切换；
- 战斗外不显示过期战斗画布，关闭后无残留分配或文件句柄。

测试 BDA 的自动战斗实际获胜，181 帧，退出清理通过。
另通过地图逐像素对照、NPC 边缘绘制、触摸反算、菜单恢复、存档写入后重启读回、
Steam 3～6 号视频各 3 帧解码、主包启动/清理和 V 按下沿检查。
记录在 `build/verification/wide-battle.json`、`battle.json`、`wide-scene.json`、
`display-controls.json`、`save-roundtrip.json`、`steam-video.json`、`mips-smoke.json`。

[实际 MIPS 战斗画面](evidence/battle-model.png)。

## 完整 H1 V1.41 固件

QEMU bbkh1、64 MiB、独立 NAND `build/firmware-v013-battle/`。
使用上列测试 BDA 和交互战斗标记，跳过剧情直接进入正常战斗核心，自动作战关闭。
正式 BDA 不包含这些测试标记行为，安装包也不包含 NAND、标记或存档。

实际确认：

- 战斗画布 360×204、LCD 输出 480×272、显示模式 0；
- 战斗菜单、敌人、角色状态和选择光标正常，背景覆盖 LCD 四边；
- V 实测依次切换 435×272、320×200、480×272；
- Enter + Esc 退出，`opened=0`，返回桌面，日志 `END status=0`；
- PCM 继续输出；本次记录存在 1 次应用音频欠载，不能据模拟器结果保证真机音画性能。

[完整固件战斗截图](evidence/battle-firmware.png)。
尺寸、模式、计数和日志位于同目录 `battle-fullscreen.json`、`battle-mode-*.json`、
`exit-desktop.json`、`H1PAL.LOG`。

## 复现

```powershell
python tools/build.py
python tools/build.py --regression
python tests/wide_battle.py
python tests/battle.py
python tests/wide_scene.py
python tests/display_controls.py
python tests/save_roundtrip.py
python tests/steam_video.py
python tests/mips_smoke.py --limit 8
```

交互固件测试可用 `tools/firmware_image.py --bda build/regression/H1PAL.bda --battle-test`
建立独立 NAND。实际还需要本地用户固件和资源，均不随源码分发。

此前的地图全屏、地图边界黑底和资源来源见 [v0.1.2 验证](verification-v0.1.2.md)、
[v0.1.1 验证](verification-v0.1.1.md)。
尚未进行物理 H1、全剧情通关或长时间稳定性验证。
