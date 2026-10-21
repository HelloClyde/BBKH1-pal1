# 仙剑1 H1 v0.1.9（预发布）

2026-10-21 补充资源：本 Release 新增含物品介绍的 `PAL9588.PAK`（27.18 MB）。
在原 DOS 资源中加入 Steam 附带的繁体说明文件，保留原文及署名，共 296 条物品及仙术说明。
**补充介绍只需替换 A/B 资源目录里的 `PAL9588.PAK`；已有的 v0.1.9 BDA、视频、配置和存档继续使用。**
两盘都有主资源时优先 A 盘。首次安装的可选视频仍使用
[v0.1.7 的 PALVIDEO.PAK](https://github.com/HelloClyde/BBKH1-pal1/releases/download/v0.1.7/PALVIDEO.PAK)。

主资源 SHA-256：`1cd232c865476a9f4c0fd07eb81a2515cb7a9c4d1ef928e1ebc7f500350f4b6a`。
独立资源清单和校验文件为 `resources-manifest.json`、`RESOURCE-SHA256SUMS.txt`。
实际 MIPS 服务模型验证全部说明可读取、字形齐全，并检查药品、装备和道具的 480×272 物品界面。
原有 21 项游戏数据逐字节不变。详情见
[物品介绍验证](https://github.com/HelloClyde/BBKH1-pal1/blob/main/docs/verification-item-descriptions.md)。

按键映射入口改为 **系统 → 按键映射**，与存档、读档、音乐和音效并列，放在“结束游戏”之前。
去掉原来的“结束游戏 → 系统设置”入口；结束游戏恢复为原来的是否确认框。

沿用原版画风、六个动作的改键、同键交换、恢复默认和 A/B 盘配置保存。
原有 `h1keys.cfg` 继续读取。按键映射入口调整只需升级 BDA；物品介绍使用上述新主资源包。

实际 MIPS 菜单测试验证系统菜单直接打开改键页，并确认退出菜单只有“否/是”。
完整 H1 V1.41 固件模拟器中，从旧存档进入新入口、修改按键、返回与退出检查通过。
尚未进行物理真机测试。

BDA SHA-256：`8bf2d9a7df8c637243e864c733d1a1591c103661fc2da8040f88f50bc41230e2`。
