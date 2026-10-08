# 04_Outputs/v0.1 —— SD 卡安装包（实机已验证可玩）

构建日期：2026-10-08（Asia/Shanghai）
目标：Diablo III Eternal Collection (Switch)，TitleID `01001B300B9BE000`，游戏版本 **2.7.7.92380**
基线：`god-jester/d3hack` main（v3.1，GPL-2.0）

把 `sdcard/` 的内容**覆盖到 SD 卡根目录**即可（`sdcard/` 就是那个 zip 解开的树，两者内容一致）。

```
SD:/atmosphere/contents/01001B300B9BE000/exefs/{subsdk9, main.npdm}
SD:/atmosphere/contents/01001B300B9BE000/romfs/d3gui/*
SD:/config/d3hack-nx/config.toml          ← 全功能示例（已强制 AllowOnlinePlay = false）
SD:/config/d3hack-nx/rift_data/*
```

| 文件 | 大小 | SHA-256 |
|---|---|---|
| `atmosphere/.../exefs/subsdk9` | 1 280 333 B | `950e7ec359f04a9a8dcb466f20c5860330dcf3a44d9f5c8e556dad0bec987808` |
| `atmosphere/.../exefs/main.npdm` | 1 516 B | `cb47d2bc9af6fcd8e63cb9bdad099bbd71b3a8743ea759d69445711a78939799` |
| `d3hack-2.7.7.92380-sdcard-v2.zip`（44 个文件） | 1 123 785 B | `7f5fdfb65ad595c9de3fa623e294ea4abd5ab8134531c14ee5fa14aaa5a7ccab` |

> ⚠️ **产物不可复现**：`source/program/main.cpp` 里有
> `PRINT_LINE("Compiled at " __DATE__ " " __TIME__)`，编译期把日期时间嵌进了二进制，
> 所以**每次重新构建 `subsdk9` 的哈希都不同**（大小不变）。上表的哈希对应
> **实机验证过的那一份**；自己重建得到的哈希对不上是正常的，看日志里的
> `Compiled at …` 来确认跑的是哪一次构建即可。

**怎么确认装的是这一版**：日志里 `Compiled at Oct  8 2026 17:1x`（第一版是 16:05，那一版会崩）。

## 判定顺序（越靠前越能暴露偏移错误）

1. **能进主菜单不崩** ← 第一版就死在这里（`patch_hideonline_06_bytes` 落点错，覆盖了一条 `bl`）
2. 能进**选人界面** ← 本版已通过
3. 进游戏后**正常游玩** ← 本版已通过（猎魔人）
4. 看启动水印：标题/自动存档画面显示 `[v2.7.7.92380]`
5. 逐组开功能：赛季 → 事件 → 挑战秘境 → rare_cheats → loot_modifiers → resolution_hack → overlays
   （清单见 `03_Documents/reports/TEST-PLAN.md`）

## 二分排查（出问题时）

用 `config.safemode.toml` 覆盖 SD 上的 `config.toml`：除 GUI 外全关 + **打开 mod 自带异常处理器**。

> ⚠️ 注意：你上一份自用的 `config1.toml` 里是 `EnableExceptionHandler = false`。
> 排查期请把它打开，否则崩溃时不会有 `user_exception.txt`。

能进游戏就说明问题在某个功能组里，再按 `TEST-PLAN.md` 一组组开回来。

## 回滚

删 `SD:/atmosphere/contents/01001B300B9BE000/` 与 `SD:/config/d3hack-nx/` 即可，**不动游戏本体**。

## 离线赛季的已知现象（不是崩溃）

日志里 `[seasonal_debug] set_game_params_for_hero season_created=0` 与
`[seasonal_gate] game_is_seasonal=0`：含义是「游戏当前赛季 ≠ 37」。
已核对补丁站点（`0x1BD140`）与 XVar 槽位（`xvar_season_num_ptr` = `0x114AC60`）**地址都是对的** ⇒
问题在"值没写进去"这一层。另外用**非赛季角色**进游戏时这两个值按设计就是 0。

## 已知取舍（不是漏做）

| 项 | 状态 | 原因 |
|---|---|---|
| `patch_hideonline_04..07` | 关闭 | 2.7.7 重写了 `UIMainMenu::Console::OnUpdate`，落点是错的（其中 `_06` 就是崩溃元凶）。2.7.7 **原生**已把在线状态标签隐藏，关闭无视觉损失 |
| `patch_ddm_labels_03/04/08/09_adrl` | 关闭 | 2.7.7 把 X3/X4 的 `ADRP+ADD` 对重排，硬套会覆盖 `adrp x4`。代价仅：DDM 标签文字用游戏自带颜色 |
| `AllowOnlinePlay` | 强制 false | 开启后联机属作弊行为，有封号风险 |
| 兼容 2.7.6 | 不再支持 | 本版改成"纯 2.7.7 单版本"，偏移表已就地改写（原始 2.7.6 表备份在 `05_Code/d3hack/source/program/*.orig`） |

## 旧版归档

`10_Other/backup/` 下：`...-sdcard-v1(崩溃版).zip` —— 最早那版（会崩，仅作对照）。
（实测期间的原始数据，如当时的 `config.toml`、`D3Debug.txt`，放在**不入库**的 `01_Inputs/switch-test/`。）
