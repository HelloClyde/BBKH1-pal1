# H1 PAL v0.1.5 A/B 盘验证

日期：2026-10-20。正式 BDA SHA-256：
`9da4c89cdfbe68df8d9e20d570922f5facbf14a718c5f80d2396803e89bca7d7`，2419024 字节。
测试 BDA：`7b5f34f3376cae50bc259ddf1fb3c287c9c08a96f7072556deeb5f99768aa037`。
SDK 和 SDLPAL 固定提交未改变。详细结果见 [发布验证记录](evidence/release-v0.1.5.json)。

## 选择规则

在首次日志、配置和资源读取之前，用原生文件接口查找 A 盘主资源包；不存在时查 B。
以 `应用\数据\PAL\PAL9588.PAK` 为准，目录或视频包单独存在不影响主包选择。
选择后固定整次运行使用的目录，两个 PAK、默认存档、配置和日志都使用同一盘。
A 包存在但损坏时保持 A 并报错，不把 B 盘的游戏进度混入本次运行。
探测句柄立即关闭；缺资源提示同时显示 A/B 两条路径。

## 真实 MIPS 与文件服务模型

`tests/data_drives.py` 在实际正式 BDA 上使用原创微型 PAK，公开 CI 无需原游戏资源。
七种场景：只有 A、只有 B、两盘都有、A 只有目录/配置/视频、B 没有视频而 A 有视频、两盘均缺主包、A 主包损坏而 B 有正常主包。
检查读取的主包内容、视频来源、存档/配置/日志写入与读回，以及句柄回收。
选择 B 时，不覆盖 A 盘现有配置，也不往 A 写入存档和日志。

`tests/save_roundtrip.py --drive A` 与 `--drive B` 使用用户的真实游戏主资源和测试 BDA，
分别执行 SDLPAL 的保存、独立重启、读取与内容核对。两盘均正确读回 183488 字节存档，
日志路径匹配所选盘，文件句柄和分配均无残留。该检查依赖私有资源，不进入公共 CI。

正式 BDA 的 UI、战斗背景、显示模式/触摸和缺资源退出检查继续通过；两个 PAK 容器主机测试通过。
新功能不修改游戏数据或存档格式，不自动搬运原存档。

## 完整 H1 固件

独立私有 NAND，H1/Y100 V1.41，QEMU bbkh1，64 MiB。只操作本次端口和镜像，已结束并停止。
实际正式 BDA 的主菜单、旧存档地图均为 480×272；读取既有存档后正常显示剧情与地图。
日志记录 `DATA_PATH A:\应用\数据\PAL\`，退出 opened=0、END status=0，音频 dropped/failures/underruns 均为 0。

[启动主菜单](evidence/v0.1.5-title.png) · [读取旧存档](evidence/v0.1.5-map.png)。
本次完整固件只提供 A 盘；B 盘检查来自上述 MIPS 原生文件服务模型。
未做物理 H1 真机、B 盘全固件或全剧情验证。

## 复现

```powershell
python tools/build.py
python tools/verify_release.py
python tests/data_drives.py
python tests/wide_ui.py
python tests/wide_battle.py
python tests/display_controls.py
python tests/mips_smoke.py --missing
python -m unittest discover -s tests -p "test_*.py"
```

私有主资源放入 `build/resources/PAL9588.PAK` 后：

```powershell
python tools/build.py --regression
python tests/save_roundtrip.py --drive A
python tests/save_roundtrip.py --drive B
```

历史记录：[v0.1.4 图标/开源验证](verification-icon-v0.1.4.md)、[v0.1.4 菜单验证](verification-v0.1.4.md)。
