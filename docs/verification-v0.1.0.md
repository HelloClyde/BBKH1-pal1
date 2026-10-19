# H1 PAL v0.1.0 验证

后续 v0.1.1 修复了此版残留的 SDLPAL 上下留边；最新结果见 [当前验证](verification.md)。

日期：2026-10-19。未连接、安装或操作物理 H1。

正式 BDA：`19f3784b3a11068b54100cdda2a4f97aadaeaa8f265ec4038b2c44e319d5fe72`，
2,411,880 字节。测试 BDA：
`63522e5fa50e7a5b7f536a2b0941765a54bfa648d45739ae73c895dd18960d6a`。
测试 BDA 直接进入标记对应的回归任务，正式 BDA 不启用这些任务。

## 完整固件

本机 H1 V1.41 `project.bin` 与私有隔离 NAND，QEMU `bbkh1`，64 MiB。
复用工作区的 H1 模拟器；未修改固件来替代应用接口。沿用模拟器已有的桌面壁纸回退。
原文件 dump、真实设备和其他项目 NAND 均未修改。

- 原生桌面通过固件载入 BDA，显示仙剑图标和标题。
- 实际播放 PAL98 启动 AVI；跳过视频后可停留于“新的故事 / 旧的回忆”。
- 原尺寸 320×200 和 435×272 等比例显示，横屏方向正确，菜单和中文字形正常。最终 BDA 的显示模式实测为 1 → 0，静态菜单切换无黑屏。
- 新游戏进入客栈，显示李逍遥、李大娘对话；自由行动时点击后实际角色坐标变化。
- 系统菜单保存得到 183488 字节 `1.rpg`，首次保存次数头为 `01 00`，最终 BDA 再次保存后增加为 `02 00`。
- 将该存档导入重新构建的私有 NAND，从标题菜单读取后恢复对应的客栈位置。
- Enter+Esc 长按退出，游戏窗口关闭；再次打开可重新进入片头。
- 真实模拟音频流抽样 96198 帧：32000 Hz，16-bit stereo（H1 固件将单声道源混入双声道输出），
  非零比例 66.85%，peak 15869，RMS 3542.59。这不是仅检查 PCM API 被调用。

证据位于 `build/firmware/`，最终轮次文件以 `v010-` 开头；音频 WAV 和统计位于
`build/verification/firmware-audio.*`。其中早期不带该前缀的图片保留了移植迭代过程，
其 BDA 哈希以对应的 JSON 为准，不混作最终包证据。

## MIPS 服务模型

执行实际交叉编译 BDA，使用 Unicorn 模拟 MIPS32，H1 文件、LCD、PCM、按键和时钟接口
由测试模型提供。它验证二进制执行及资源管理，不代表完整固件或真机速度。

| 测试 | 结果 |
| --- | --- |
| 无资源启动 | 提示资源路径，返回且没有残留文件句柄、堆分配或游戏窗口 |
| 主包启动，不安装视频包 | DOS 回退路径送显，运行 8 帧后正常关闭 |
| 两次独立启动存档 | `SAVE PASS`、`RELOAD PASS`，183488 字节原生存档未被二次启动改写 |
| 战斗 | 181 次显示后 `BATTLE WON`，音乐缓冲有非零样本，完整清理 |
| V 键 | 两轮原尺寸/等比例切换；按住不重复；静态画面立即重绘 |
| PAK 工具 | 大小写、随机数据打包展开往返、损坏 CRC 拒绝均通过 |

各 JSON 的 `sha256` 指向本轮实际执行的正式或测试 BDA；退出测试检查宿主栈和寄存器，
并验证文件、内存、窗口和 PCM 的所有权清理。

在本工作区复现：

```powershell
python tools/build.py
python tools/build.py --regression
python tests/mips_smoke.py --missing
python tests/mips_smoke.py --limit 8
python tests/display_controls.py
python tests/save_roundtrip.py
python tests/battle.py
python -m unittest discover -s h1-pal/tests -v
```

服务模型复用工作区 `tests/mips_smoke.py`，需 Unicorn、Pillow 和本地两个 PAK。
`tools/firmware_image.py` 复用工作区镜像工具，在程序停止后创建独立 NAND；固件和镜像不进安装包。

## 资源与打包

用户指定的 9588 v0.1.8 release：

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| PAL9588.PAK | 27168336 | `18af405d5ee7e0f31148a4bc6733bba6d2cf141ba1b7f1e2fb49ec52e4dc3e30` |
| PALVIDEO.PAK | 33134352 | `3bab5afa2fdc1dfb2ca1de3c60a8ecdfe414ed683ac511d034028e50d57e8248` |

发布者 SHA-256 与下载结果一致，27 个资源条目均通过 CRC32。
安装 ZIP 只含正式 BDA、两个 PAK、说明、许可和清单，不含测试标记、用户存档或固件。
打包后再次解压校验每个安装文件的 SHA-256。

## 边界

尚未进行物理 H1 测试、全剧情通关、全部视频完整播放或长时间存储故障测试。
RIX、VOC/WAV 和 AVI 路径已接入；完整固件声音内容验证目前取自开场 AVI，
RIX 战斗音乐的非零内容由 MIPS 服务模型验证。
不根据模拟器帧率推断 H1 真机性能或音画同步。
