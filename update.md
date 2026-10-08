# 更新说明

> 本文件内容取自 git 记录，与提交信息一致。查看原始记录：`git log` / `git tag -n`。

## v0.1

`v0.1 —— 移植到 2.7.7.92380：启动崩溃已修 + 实机可玩 + 产物入库`

【移植范围】
- 目标：Diablo III Eternal Collection (Switch) `2.7.7.92380`（TitleID `01001B300B9BE000`）
- 基线：`god-jester/d3hack` main（v3.1，GPL-2.0），原版只认 `2.7.6.90885`
- 449 条硬编码偏移（258 主表 + 191 patch 表）就地改写为 2.7.7 地址；版本门改为单版本 `2.7.7`
- 不依赖 2.7.6 参照二进制：平移函数由「公开跨版本金手指表 + 上游源码记录的原始指令字节」反推

【实机结果】
- ✅ 能进主菜单 → 选人界面 → 用猎魔人正常游玩
- ✅ 版本门 `client=2.7.7.92380` 通过；10 个 hook 全部安装成功；GUI / romfs / 中文翻译 / overlay 正常

【修掉的崩溃（第一版）】
- 现象：`2168-0002 Data Abort`，`PC = DiabloIIINX64r.nss + 0x362850`，出错地址 `0x51`
- 根因：2.7.7 **重写了** `UIMainMenu::Console::OnUpdate`，我们的 `patch_hideonline_06_bytes`
  把这个地址上的 `bl 0x35c1d0` 覆盖成了 `LDR X8,[X8,#0x50]`；崩溃瞬间 X8=1 → 访存 `0x51`
- 修法：`patch_hideonline_04..07` 全部关闭（2.7.7 原生已 `SetVisible(0)` 隐藏这两个在线标签，无视觉损失）

【顺便修掉的隐患】
- `patch_autosave_string_01_adrl`：`0x335B78 → 0x335B68`。实测 0x335B68 的 ADRP+ADD 解析到
  rodata `0xE6E58C` = `'ConsoleUI:AutosaveWarningScreenText_Switch'`（正是该补丁要换的串），delta 为 **0**，
  原来的 +0x10 会去覆盖 `add x0, sp, #8`
- `patch_ddm_labels_03/04/08/09_adrl` 关闭：2.7.7 把 X3/X4 的 `ADRP+ADD` 对重排，
  `MakeAdrlPatch`（site 写 ADRP、site+4 写 ADD）硬套会覆盖 `adrp x4`；代价仅文字颜色

【工具链（本仓库自研，补齐了既有工具链缺的「XCI 容器层」）】
```
XCI → 根 HFS0 → secure 分区 → 更新 NCA → ExeFS(PFS0) → main(NSO0) → LZ4 → text/rodata/data
```
- `05_Code/tools/xci.py` / `nca_xci.py` / `dump_exefs.py` / `probe_crypto.py`（新）
- `05_Code/tools/audit.py` / `verify2.py`（逐站点指令形状复核，本轮定位崩溃靠它）
- `05_Code/scripts/build.sh` / `fetch-deps.sh`（一键构建 + 固定 commit 拉依赖）

【踩到的三个格式坑（照公开规范写会静默出错）】
- 本 XCI 的 HFS0 条目布局与公开规范不一致（实测 `[offset u64][size u64][name_off u32][hashed_size u32][reserved u64][sha256]`），
  且 XCI 头 `0x110` 是垃圾，真实根分区偏移在 `0x130`
- NCA 区段 CTR 的计数器偏移必须含 `0xC00`（`(media_off + 0xC00) >> 4`），否则任何区段都解不出魔数
- XCI 内附带的**本体 NCA 是 2.6.2.52309**，不是 2.7.6 —— 不能拿它当参照

【已知未解决】
- 平移模型待修正：`0x335B68` 实测 delta=0 而 `0x351CBC` 实测 +0x10 ⇒ `b1 ∈ (0x335B68, 0x351CBC]`，
  非原先使用的 `0x29CBB0`。窗口内条目大多被多加 0x10（但窗口内 `sym_FormatTruncatedNumber` /
  `sym_UI_GfxInit` / `sym_SetUICConversionConstansts` **源码里无调用点**，地址错也无害）
- `data_build_locker_format_rw = 0xE6D9E4` 是全表唯一未验证项（识别不出那 21 字节内容）
- 离线赛季：`season_created=0`（补丁站点与 XVar 槽位地址均已核对正确，属"值没写进去"）
- 功能级验证尚未做完 → 清单见 `03_Documents/reports/TEST-PLAN.md`

【发布前清理（准备公开）】
- **未公开** 5 个内容提取/解密脚本（需 prod.keys 解 NCA/XCI，属易被下架的形态）：
  `tools/xci.py`、`nca_xci.py`、`dump_exefs.py`、`probe_crypto.py`、`scan_all_ncas.py`
  —— 已从索引移除并加入 `.gitignore`，**历史记录里也已清除**（amend + gc --prune=now）
- 个人路径与内部工程名全部换成占位符/env：
  `scripts/build.sh` 改为由脚本位置推导仓库根，机器相关路径移入不入库的 `scripts/local.env`
  （模板 `local.env.example` 入库）；`tools/*.py` 改为从 `__file__` 推导仓库根；
  文档里的绝对路径、内部工程名已清理
- 删除被 `scripts/build.sh` 取代的 `10_Other/backup/build_msys2.sh`（内含个人路径）
- 新增 `05_Code/tools/README.md`（说明工具用途与判据，以及哪 5 个脚本刻意未公开）
- 文档补齐「参考」节：上游 d3hack 仓库与六个被改动文件的直链、exlaunch / ImGui@commit /
  tomlplusplus@commit / devkitPro / libnx / Atmosphère / Arm A64 文档，
  以及地址交叉验证所用公开金手指表的来源

【产物入库】
`04_Outputs/v0.1/` 含 `sdcard/`（铺成 SD 卡结构）+ zip + `config.safemode.toml`
`04_Outputs/tables/` 含 449 条 2.7.7 偏移表 CSV 与可直接粘贴的 C++ 片段
