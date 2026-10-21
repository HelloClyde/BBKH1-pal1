# DOS 物品介绍资源验证

2026-10-21，主资源包增加 Steam 安装附带的 `PAL/desc_cht.dat`，容器内命名为 `desc.dat`。
保留原文件的繁体编码、Eric-Chen 署名与来源 URL；不改写为 98 版数据。
原有 21 项 DOS 游戏资源逐字节一致，仅新增一个 16027 字节文件，共 22 项。
该文件包含 296 条物品及仙术说明，最多三行。说明文本只随资源附件提供，不进入源码仓库。

- 新 `PAL9588.PAK`：27184432 字节。
- SHA-256：`1cd232c865476a9f4c0fd07eb81a2515cb7a9c4d1ef928e1ebc7f500350f4b6a`。
- 原始说明 SHA-256：`0d6487d6832488130bc94b1ec5ee71766717b929c249693327089e461460ae40`。
- 原 BDA 未修改，使用 v0.1.9：`8bf2d9a7df8c637243e864c733d1a1591c103661fc2da8040f88f50bc41230e2`。

`tests/item_descriptions.py` 实际执行上述 MIPS BDA，由 H1 服务模型提供文件、显示及其他系统接口。
检查 PAK 目录与每项 CRC，逐项对比旧容器；说明文件与 Steam 原文件字节一致。
引擎读取全部 296 个 ID，检查无空文本、无替换字符，941 个用到的字符都有字形。
在测试内存的背包中放入金创药、木剑和紫金葫芦，实际调用物品菜单，
核对选中 ID、显示文本、换行及底部范围，保存 480×272 截图。退出后无文件或分配泄漏。
测试背包仅存在于内存，不写入使用者的存档。

记录：[item-descriptions.json](evidence/item-descriptions.json)。
截图：[药品](evidence/item-description-medicine.png)、[装备](evidence/item-description-equipment.png)、
[道具](evidence/item-description-quest-item.png)。

此次资源验证使用 MIPS 服务模型；没有把这次结果称为完整固件或物理真机测试。
相同 BDA 之前的完整固件验证见 [v0.1.9](verification.md)。
`PALVIDEO.PAK`、BDA、配置和原生存档格式均不需更换。
替换当前资源盘 `A:\应用\数据\PAL\` 或 `B:\应用\数据\PAL\` 下的 `PAL9588.PAK` 即可；两盘都有时仍优先 A。

```powershell
python tools/prepare-steam.py --steam-root <自己的Steam仙剑目录> --output build/item-description-resources --core-only
python tests/item_descriptions.py --resources build/item-description-resources/PAL9588.PAK --baseline <旧PAL9588.PAK> --descriptions <Steam的PAL/desc_cht.dat>
```
