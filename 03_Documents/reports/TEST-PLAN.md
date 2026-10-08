# d3hack 2.7.7 移植版 —— 功能验证清单

> 当前状态（2026-10-08 17:5x）：**能进选人界面、能用猎魔人正常游戏**。
> 启动期崩溃（`patch_hideonline_06_bytes` 落在 0x362850，覆盖了 `bl 0x35c1d0`）已修复，见 `DIAGNOSIS.md` 第二节。
> 现在剩下的都是**功能级**风险，需要你按组开关逐项确认。

---

## 0. 先确认你在用哪份配置

| 配置 | 全关状态 | 用途 |
|---|---|---|
| `deliver/config.safemode.toml` | 除 GUI 外全关，异常处理器 ON | 你刚才跑通的那份 |
| `deliver/sdcard/config/d3hack-nx/config.toml` | 全功能（示例默认） | 最终要跑的目标 |

**请告诉我你刚才是用哪份跑通的。** 如果是 safemode，那下面的功能都还没验证过，接下来就是逐组打开。

开 overlay：游戏里 **`+` 和 `-` 同时按 0.5 秒**。改完设置建议**重启游戏**再测下一组。

---

## 1. 已核对通过、可以先放心的部分（不用重点测）

这些都是我拿 2.7.7 原始二进制逐条反汇编对过的：

- **「必须落在函数入口」的 hook：27 个里 24 个硬验证通过**，另外 3 个（`ACD_AttributesGetInt/Float`、`LootRollForAncientLegendary`）是无栈帧叶子函数，属于正常形态。
- 已验证的补丁站点：`hideonline_02/03`（0x61620/24，指令与注释逐字一致）、`hideonline_08..11`（暂停菜单组）、`ddm_labels_02/07`、`start_string`（0x3656C8）、`var_res_label_02/03`（0x3CC78/7C 逐字一致）、`release_fps_label_*`、`buildlocker_*`、`dynamic_seasonal_03/04/05/08/09/10`、`autosave_string`（0x335B68，本轮修正）。
- `.data` / `.bss` 不平移：已用 FPS 坐标 `-180.0/290.0` + `xvar_season_num_ptr` 槽位 0x114AC60 两路独立证据确认。
- 本轮**主动关掉**的：`hideonline_04..07`（2.7.7 原生已隐藏在线标签，其中 06 就是崩溃点）、`ddm_labels_03/04/08/09`（2.7.7 把 ADRP/LDR 对重排了，硬套会覆盖 `adrp x4`）。
  → 副作用仅：DDM 标签文字颜色用游戏自带色（文字替换照常）。

---

## 2. 按风险排序的验证清单

每组都给出：**怎么开 → 预期现象 → 出问题时要抓什么**。

### 第 1 组：`[rare_cheats]` —— 风险最高（补丁最多 + 4 个 INLINE hook）

**先单独开这一项**：`FloatingDamageColor = true`（其余保持关闭）→ 打怪。
- 预期：飘出的伤害数字变成红色。
- ⚠️ 风险：`sym_floating_dmg` 的 INLINE 回调读 `ctx->X[3]` 当颜色指针（源码注释写死 `// BB5E8`，与我们的落点 0xBB5E8 一致）。若指令落点差几条，会把颜色写到别的对象上 —— **不会立刻崩，但可能画面错乱**。
- 判定：红色 ✓ / 颜色错乱或没变 → 记下来。

再逐项开（每项单独测，测完关掉再开下一项）：

| 配置项 | 预期现象 | 备注 |
|---|---|---|
| `MovementSpeedMultiplier = 1.3` | 移动明显变快 | TRAMPOLINE，入口已验证 ✓ |
| `AttackSpeedMultiplier = 1.2` | 攻速变快 | 同上 ✓ |
| `NoCooldowns = true` | 技能无冷却 | 纯 bytes 补丁 |
| `InstantPortalAndBookOfCain = true` | 原地开门 + 秒读回城书 | |
| `InstantCubeAndCraftsAndEnchants = true` | 附魔/打造/鉴定/魔盒秒完成 | 用了 `CmnImmediate`/`AddImmediate` 类型，形状判据没覆盖 → 中等风险 |
| `SocketGemsToAnySlot = true` | 任意插槽插任意宝石 | `ItemHasLabel` INLINE hook |
| `UnlockAllDifficulties = true` | 难度不再需要解锁 | 强制返回型补丁（`movz w0,#1`+`ret`），已验证 |
| `EquipMultipleLegendaries = true` / `EquipAnySlot` | 可穿多件限制装备 / 任意槽位 | `ACDInventoryItemAllowedInSlot` TRAMPOLINE，入口已验证 ✓ |
| `LegendaryGemUpgradeSpeed = true` | 宝石升级流程加速 | 站点 0x349BA8（+0x10）—— 这条在「b1 可能偏低」的窗口边上，**重点看** |
| `GuaranteedLegendaryChance` / `DropAnyItems` / `LegendaryGemLevel150` | 掉落类 | 后者的洞穴地址是 2.7.6 的值（我们没动），本项默认关闭 |

### 第 2 组：`[loot_modifiers]` —— 中高风险

`SectionEnabled = true` + `AncientRank = "Primal"` + `DisableTormentCheck = true` → 打怪看掉落。
- 预期：掉落全是太古（Primal）、不受难度限制。
- ⚠️ 风险：`LootRollForAncientLegendary` 是 **REPLACE** hook（原函数被整体替换），若地址错会同时破坏原函数。
- 另外测：`ForcedILevel`（如 70）、`DisableAncientDrops/DisablePrimalAncientDrops`、`SuppressGiftGeneration`。

### 第 3 组：`[resolution_hack]` —— 中风险（改动面最大的运行时功能）

`SectionEnabled = true`、`OutputTarget = 1080` → 掌机/底座各进一次游戏。
- 预期：1080p 输出；`VariableResLabel = true` 时画面出现分辨率标签。
- ⚠️ 风险：hook `NVNTexInfo::CreateNVNTexture` 并改贴图尺寸/采样；`get_render_target_current_resolution` 是 REPLACE（入口已验证 ✓）。**贴图 clamp（2048x1152）在进游戏加载贴图时最容易出问题** —— 这正好是上一轮崩溃的场景，务必多试几次进出场景。
- 侧重点：贴图错乱 / 黑屏 / 花屏 / 进场景崩。

### 第 4 组：`[seasons]` / `[events]` / `[challenge_rifts]` —— 中风险

1. `[seasons] SectionEnabled = true`、`SeasonNumber = 37` → **必须用「赛季角色」进游戏**才有效。
   ⚠️ 已知但未解决：日志里 `[seasonal_debug] set_game_params_for_hero season_created=0`、
   `[seasonal_gate] game_is_seasonal=0`。这个 0 的含义是「游戏当前赛季 ≠ 37」。
   我核过：补丁站点（0x1BD140）和 `xvar_season_num_ptr`（0x114AC60）地址都对 —— 所以是**值没写进去**，
   不是地址错。**请重点看**：赛季界面显示的赛季号是不是 37？打完一轮有没有赛季进度？
2. `[events]`：`SeasonMapMode = "OverlayConfig"` + 单项开关（`KanaiPowers`、`DarkAlchemy`、`SwarmRifts` 等）。
   预期：赛季主题地图/事件生效。⚠️ 事件 buff 的 XVar 指针槽位是 `.data` 项，**这是我最不放心的一块**。
3. `[challenge_rifts] SectionEnabled = true`、`MakeRiftsRandom = true` → 进挑战秘境，层数应在 0-28 间随机。
   注意 `ChallengeRift*` 系列 TRAMPOLINE 入口全部验证通过 ✓，但 `sOnGetChallengeRiftData`/`ParsePartialFromString` 传的是 `rift_data/*.dat`，看能不能正常读。

### 第 5 组：`[overlays]` + GUI —— 低风险，但有已知疑点

- `DDMLabels` / `FPSLabel` / `VariableResLabel` / `BuildLockerWatermark` 逐个开。
- ⚠️ **已知疑点**：字体图集是 **512x128**，对 188 条中文翻译偏小。如果 overlay 里**中文显示成方块/问号**，
  就是 `font_loader` 加载共享字体的那条链在 2.7.7 上有问题 —— 这是我最想确认的一条。
- 另测：overlay 开关（`+`/`-`）、改设置后保存是否写回 `config.toml`、`Language` 切 en/zh 是否热切换。
- `BuildLockerWatermark` 依赖 `data_build_locker_format_rw = 0xE6D9E4`，**这条是整个表里唯一没验证的项**（我识别不出那 21 字节的内容）。如果开了它水印异常，就是这条。

### 第 6 组：`AllowOnlinePlay = false` 的隐藏逻辑 —— 低风险

- 主菜单不应该出现 "Connect to Diablo Servers"（靠 `hideonline_02/03`，已验证）。
- **暂停菜单**的网络状态标签应该隐藏（`hideonline_08..11`）。
- 如果这两处正常，说明 `AllowOnlinePlay=false` 这条链路是干净的。

---

## 3. 出问题时的取证清单（照抄给我就行）

1. `SD:/atmosphere/crash_reports/`（**整个目录**，含 `.log` + `.jpg` + `dumps/`）
2. `SD:/config/d3hack-nx/D3Debug.txt`
3. `SD:/config/d3hack-nx/user_exception.txt`（有的话）
4. 你当时的 `config.toml`

**有崩溃报告的 `.log` 我就能像这次一样直接算出 PC → 模块偏移 → 定位到具体是哪条补丁。**

---

## 4. 已知未解决、不影响你现在测试的三件事

1. **平移模型要重做**：`0x335B68` 实测 delta=0、`0x351CBC` 实测 +0x10 ⇒
   `b1 ∈ (0x335B68, 0x351CBC]`，不是我原先用的 `0x29CBB0`。窗口内条目大多被多加 0x10。
   好消息：窗口内 `sym_FormatTruncatedNumber` / `sym_UI_GfxInit` / `sym_SetUICConversionConstansts`
   **源码里没有任何调用点**，地址错也无害；`sym_UI_GfxInit` 实为 thunk（delta 应为 0）。
2. `sym_ImageTextureFrame_ctor` / `sym_dupe_dropped_item` 落点存疑，但都**只在 lobby 系列 hook 里用**，
   而 lobby 由 `debug.enable_crashes` 控制（当前关闭）。要测那一块时再说。
3. `patch_hideonline_04..07` 和 `ddm_labels_03/04/08/09` 是**为了保命主动关掉的**，
   不是"没做"。等基础功能都验证过了，可以回头按 2.7.7 的真实指令布局重新写这几条（`_03/_04` 需要
   把 ADRP 与 ADD 拆到两个不同地址，现成的 `MakeAdrlPatch` 写 site+4 的做法不适用）。

---

## 参考

- 上游 d3hack（GPL-2.0）：https://github.com/god-jester/d3hack
  - 偏移表：`source/program/offsets.hpp`、`source/program/offsets_patch_only.inl`
  - 补丁实现：`source/program/d3/patches.cpp`
  - 版本门：`source/program/main.cpp`
- 注入框架 exlaunch：https://github.com/shadowninja108/exlaunch
- 崩溃报告的判读依据：Atmosphère 的 crash report 格式与错误码
  （`2168-0002` = Data Abort）https://github.com/Atmosphere-NX/Atmosphere
- Arm A64 指令编码（判断补丁形状时用）：https://developer.arm.com/documentation/ddi0602/latest/
- 跨版本地址交叉验证用的公开金手指表（社区文档，例：
  https://bbs.3dmgame.com/forum.php?mod=viewthread&tid=6494006 ）—— 仓库不含金手指文件
