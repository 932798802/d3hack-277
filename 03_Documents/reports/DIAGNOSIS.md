# 2.7.7 移植版实测日志分析 + 排查方案

分析对象：`D3Debug.txt`（2026-10-08 08:38:32 → 08:39:43，即主机时间 16:38→16:39）
分析所用证据：`work/update277/exefs/main.text.bin`（2.7.7.92380 的 `main`，已解压）
结论级别：日志逐行 + 关键站点反汇编交叉核对

---

## 一、日志读出来的事实

### 1. 启动阶段：全部通过，没有任何一行报错

```
[boot] stage=ExlMainStart → VerifyBuild → ValidateOffsets → EarlyPatches
      → InstallBootHooks → MountSd → LoadConfig → ConfigureLogging
      → InstallHooks → ApplyPatches → InitGui → StartGameLoop
d3hack: ver=D3Hack v3.1 client=2.7.7.92380        ← 版本门通过
hooks installed (10)                               ← 10 个 hook 全挂上
patches applied (5)                                ← 5 组 patch 全应用
```

GUI 链路也全通：

```
[romfs] Mounted romfs:/ (cache=2624 bytes)
[imgui_overlay] ImGui NVN backend initialized
[gui] translations loaded: lang=zh keys=188
[font_loader] Loaded Nintendo shared system font (NintendoExtension)
[imgui_backend] Font tex create: w=512 h=128 ...
[imgui_overlay] overlay visible=1
```

**也就是说：449 条偏移表里那些「启动即触达」的条目是对的，移植在启动层面成立。**

### 2. 最后两行 = 日志在「进入游戏」的瞬间断掉

```
08:39:30  Setting active Season to 37                     ← 第二次调用 PatchDynamicSeasonal（应是从 GUI 里改了设置）
08:39:43  [seasonal_debug] set_game_params_for_hero season_created=0 params=0x66b5874400
<日志到此为止>
```

关键：hook 表里 `boot:sInitializeWorld` 是**成功挂载**的，而它的回调会打印
`NEW sInitializeWorld! (...)`。**这行日志从头到尾没有出现。**

⇒ 游戏在「选完角色 → 设置游戏参数 → 世界初始化」之间就没再往下走。
⇒ 和「进游戏时崩/卡」的现象吻合。

### 3. 两个「看着像报错」的数值，我核对过，不是地址错

`game_is_seasonal=0` 与 `season_created=0`。反汇编 2.7.7 的 `SetGameParamsForHero`（0x1BD030）：

```
1bd07c: ldr  w21, [x8, #144]     ; w21 = 角色赛季（mod 的 patch_dynamic_seasonal_05_movz 在此强制成 37）
1bd088: cbz  w21, 0x1bd160       ; w21==0 → 非赛季分支
1bd08c: bl   0x5ff00             ; IsSeasonsInitialized()（mod 已 patch 成恒返回 1）
1bd094: bl   0x72e090            ; OnlineServiceGetSeasonNum() ← 游戏当前赛季
1bd098: cmp  w0, w21
1bd09c: b.ne 0x1bd160            ; 不等 → 落到下面
1bd160: str  wzr, [x19, #16]
1bd164: mov  w8, wzr
1bd170: str  w8,  [x19, #28]     ; x19+0x1C = season_created ← 就是这里被写成 0
```

对照 2.7.7 实机：

| 项 | 2.7.6 表值 | 2.7.7 实测 | 结论 |
|---|---|---|---|
| `sym_set_game_params_for_hero` | 0x1BD030 | 0x1BD030 是标准序言 `stp x22,x21,[sp,#-48]!` | delta 0 ✓ |
| `patch_dynamic_seasonal_05_movz` | 0x1BD140 | `ldr w21,[x8,#144]`（正是要覆盖的赛季读取） | delta 0 ✓ |
| `season_created` 结构体偏移 | 0x1C | `str w8,[x19,#28]` 在 0x1BD170 | 0x1C ✓ |
| `xvar_season_num_ptr` | 0x114AC60 | 0x72E090 里 `adrp x0,0x114a000; ldr x0,[x0,#3168]` = **0x114AC60** | delta 0 ✓ |

⇒ **所以 `season_created=0` 不是偏移错**，它的含义是「游戏当前赛季 ≠ 37」。
（另外：用**非赛季角色**进游戏时，这个值按设计本来就是 0 —— mod 的离线赛季只作用于赛季角色/赛季局。）

---

## 二、我额外核对过的站点（全部对得上，供你放心）

| 站点 | 2.7.6 | 2.7.7 实测指令 | 与 mod 源码注释是否一致 |
|---|---|---|---|
| `patch_dynamic_seasonal_08_movz` | 0x1BF5F0 | `sub sp,sp,#0x100` | ✓ 注释原文一致 |
| `patch_dynamic_seasonal_09_ret` | 0x1BF5F4 | `str x23,[sp,#192]` | ✓ 注释 `#0xF0+var_30`=192 |
| `patch_dynamic_seasonal_04_movz` | 0x5FF0C | `and w0,w8,#0x1` | ✓ 替换为 `movz w0,#1` |
| `patch_dynamic_seasonal_03_movz` | 0x351CCC | `b.ne` | ✓ 注释「skip B.ne」 |
| `patch_var_res_label_02_movz` | 0x3CC78 | `movz x8,#0x42c8,lsl#16` | ✓ 逐字一致 |
| `patch_var_res_label_03_movk` | 0x3CC7C | `movk x8,#0x4316,lsl#48` | ✓ 逐字一致 |
| `data_release_fps_pos_x/y_ro` | .data+0x658 | `-180.0f / 290.0f` | ✓ 语义正确 |
| `data_release_fps_format_rw` | — | rodata `"%3.1f FPS"` @0xE4612B | ✓ 按内容定位 |
| `patch_dynamic_seasonal_10_nop` | 0x4CADB8 | TBZ 原始字节 `A8 00 90 36` | ✓ 字节搜索命中 |

**仍存疑、但都在未启用的功能里的 4 条**（本次配置里不会被执行，先记着）：

- `sym_ImageTextureFrame_ctor` 0x29CBB0→0x29CBC0：只在 lobby 系列 hook 里被调用，本次 `LobbyHooks=0`。
  旁证：2.7.7 的 0x29CBB0 本身就是个完整 thunk 入口（`mov x8,x0; mov x9,#-1; str x9,[x0]; ...`），**更像 delta 0**，将来启用 lobby 功能时优先复核。
- `sym_dupe_dropped_item` 0x495BC0→0x495CC0：同上，lobby hook，本次未装。
- `sym_UI_GfxInit` 0x333300→0x333310：源码里只有 `SETUP_FUNC_PTR`，没有任何调用点，不影响。
- `data_build_locker_format_rw` 0xE6D9E4：只影响 build-locker 水印，本次 `BuildLockerWatermark=false`。

---

## 三、最可能的原因（按嫌疑排序）

1. **`[resolution_hack]`（本次是开启的，1080p + 贴图 clamp 2048x1152）**
   它是唯一直接 hook 渲染器的功能：hook `NVNTexInfo::CreateNVNTexture`、改贴图尺寸/采样数。
   而「进游戏」正是连续创建大量贴图的时刻。日志里第一个贴图（字体图集）走通了，但大地图/角色贴图的路径不同。
2. **`[loot_modifiers]`（本次 `AncientRank="Primal"`、`DisableTormentCheck=true`）**
   进游戏时会重建角色背包 → 大量物品生成 → 掉落/属性链被改写。若某处改写不合适，就在这一刻炸。
3. **`[rare_cheats]`（本次开了 8 项：无冷却、瞬移传送门、任意插槽宝石、解锁难度、装备多件传奇…）**
   都是直接改游戏逻辑的分支，命中点进游戏后才会执行。
4. 其它（赛季/事件/挑战秘境）——日志显示这几块的偏移我都核对过，嫌疑最低。

---

## 四、请你做的事（两步）

### 第 1 步：抓崩溃现场（最重要）

1. 把 `config.safemode.toml` **改名为 `config.toml`** 覆盖 `SD:/config/d3hack-nx/config.toml`
   （除 GUI 外全关，并**打开自带异常处理器**）。
2. 复现一次「进游戏」。
3. 崩溃后把这两个文件发我：
   - `SD:/config/d3hack-nx/user_exception.txt`
   - `SD:/config/d3hack-nx/error_manager_dump.txt`
   - 以及 `SD:/atmosphere/crash_reports/`（有的话整个目录）

有这几个文件，我就能直接定位到出错指令，不用再猜。

### 第 2 步：二分定位（如果安全模式能进游戏）

在游戏里按住 **`+` 和 `-` 同时 0.5 秒**打开 overlay，用 GUI 一组一组往回开，每次开一组就重启一次、
试着进一次游戏。顺序建议：先 `seasons` + `events` → 再 `rare_cheats` → 再 `loot_modifiers` → 最后 `resolution_hack`。

哪一组开回来就复现，问题就锁定在那组里了；把那组单独开着再试一次，我按这组去逐条比对。

---

## 五、另外两个小问题（不影响启动，看到可以顺手告诉我）

1. 字体图集是 **512x128**，对 188 条中文翻译来说偏小 —— 如果 overlay 里中文显示成方块/问号，说明 `font_loader` 加载共享字体那条链在 2.7.7 上有问题。
2. 日志里 `overlay visible=1`（配置写的是 `Visible=false`）—— 确认一下是不是你自己按开的。

---

# 第二轮（2026-10-08 17:0x）：崩溃已定位并修好

输入：`test/crash_reports/01791450279_01001b300b9be000.{log,jpg}` + 新 `test/D3Debug.txt`
（用了 safemode 配置仍崩，**进不到选人界面**）

## 1. 崩溃现场（Atmosphère 报告 + 反汇编完全对上）

```
Result 0x4A8 (2168-0002)   Type: Data Abort
Fault Address 0x0          Address 0x51            ← 报告里的 "Address" 就是出错地址
PC = 0x0f23b66850  → 模块偏移 0x362850              （模块基址 0x0F23804000）
LR = 0x0f23b665a4  → 模块偏移 0x3625A4
X[08] = 1     X[01] = 0     X[20] = 栈地址(0x7dc51a173c)
```

模块偏移 **0x362850** 正是我们表里 `patch_hideonline_06_bytes` 的落点，而这条补丁写入的是
`08 29 40 F9` = `LDR X8, [X8, #0x50]`。崩溃瞬间 **X8 = 1** ⇒ 访存 `1 + 0x50 = 0x51`
⇒ **和报告里的 `Address: 0x51` 一字不差**。

2.7.7 原始二进制在 0x362850 是 **`bl 0x35c1d0`** —— 被我们覆盖成 LDR 后就必然炸。

## 2. 根因：2.7.7 **重写了这个函数**，"统一平移量"在局部失效

`UIMainMenu::Console::OnUpdate`（0x362500–0x362B00）在 2.7.7 里被编译器重排：

| 我们的落点 | 2.7.7 实际指令 | 补丁期望的形态 |
|---|---|---|
| 0x3627FC (`_04_movz`) | `add x8, sp, #0x38` | MOVZ W1 |
| 0x362810 (`_05_movz`) | `mov w1, #5` | MOVZ W1 |
| **0x362850 (`_06_bytes`)** | **`bl 0x35c1d0`** | LDR X8,[X8,#0x50] ← **崩溃点** |
| 0x362854 (`_07_movz`) | `adrp x0, 0x1151000` | MOVZ W1 |

而 2.7.7 **原生**在 0x3628DC / 0x3628F0 就已经是
`ldr x8,[x8,#0x50]; mov w1,#0; blr x8`（= `SetVisible(0)`），
两处正好夹在字符串 `Console:ConnectedDiabloNetworkNX64`(0x3628E4) 与
`Console:DisconnectedDiabloNetworkNX64`(0x362914) 两侧 —— 即"连接/未连接状态标签"两条路径。
⇒ **2.7.7 自己就把这两个标签隐藏了**，mod 那 4 条补丁不但多余，第 3 条还是致命的。

## 3. 已修（改的是 `d3hack-port/05_Code/d3hack` 源码，不是运行期配置）

| 改动 | 文件 | 理由 |
|---|---|---|
| `patch_hideonline_04/05/06/07` 注释掉 | `d3/patches.cpp` | 函数被重写；2.7.7 原生已隐藏标签；`_06` 就是崩溃点 |
| `patch_ddm_labels_03/04/08/09_adrl` 注释掉 | `d3/patches.cpp` | 2.7.7 把 X3/X4 的 ADRP/LDR 对重排成 `adrp x3; adrp x4; …; ldr x3; ldr x4`，`MakeAdrlPatch` 写 site+4 会覆盖 `adrp x4` |
| `patch_autosave_string_01_adrl`：`0x335B78 → **0x335B68**` | `offsets_patch_only.inl` | 0x335B68 的 ADRP+ADD 解析到 rodata `0xE6E58C` = `'ConsoleUI:AutosaveWarningScreenText_Switch'`（正是该补丁要换的串）；+0x10 处是 `add x0, sp, #8`，delta 应为 **0** |

保留未动的：`patch_hideonline_02/03`（0x61620/0x61624，指令与注释逐字一致）、
`patch_hideonline_08..11`（暂停菜单组，0x221324/0x221338/0x221378/0x22137C 全部核对通过）、
`patch_ddm_labels_02/07_adrl`（0x3E568/0x3FE3C —— 2.7.7 那里是 `bl …; mov x1,x0`，两指令槽位不变，补丁仍成立）、
`patch_start_string_01_adrl`（0x3656C8）、`patch_var_res_label_*`、`patch_release_fps_label_*`、`patch_buildlocker_*`。

**副作用**：DDM 标签里的颜色（X3/X4）改用游戏自带颜色，**水印文字本身照常替换**（X1/X23 那条还在）。
视觉效果与原来几乎一致。

## 4. 新产物

```
deliver/sdcard/atmosphere/contents/01001b300b9be000/exefs/subsdk9     1 280 333 B
    sha256 950e7ec359f04a9a8dcb466f20c5860330dcf3a44d9f5c8e556dad0bec987808
    （上一版 1 281 051 B / 1c586acb…，小掉的 718 B 就是删掉的坏补丁字节）
deliver/sdcard/atmosphere/contents/01001b300b9be000/exefs/main.npdm   1 516 B（未变）
deliver/d3hack-2.7.7.92380-sdcard-v2.zip                              1 126 890 B
    sha256 81159e635b3f3d468f9ac7bcd812feb07d4893c2831974d51b5ec13a0a33d612
```
日志里 `Compiled at Oct 8 2026 17:1x` 可作为"确实换成了新版"的判据。

## 5. 已暴露、本轮未处理的风险（下一轮目标）

1. **平移模型要重做**：`0x335B68` 实测 delta=0 而 `0x351CBC` 实测 +0x10 ⇒
   **b1 ∈ (0x335B68, 0x351CBC]**，不是我们原先用的 `0x29CBB0`。
   窗口 `(0x29CBB0, 0x335B68]` 内的条目大多被多加了 0x10（如 `sym_UI_GfxInit` 0x333300 其实是 thunk）。
   好消息：窗口内 `sym_FormatTruncatedNumber` / `sym_UI_GfxInit` / `sym_SetUICConversionConstansts`
   **源码里没有任何调用点**，地址错也无害。
2. **13 个被 hook 的 `sym_*` 在 2.7.7 落点不像函数入口**：
   `sym_floating_dmg`（！由 UtilityHooks 安装，safemode 下也会装，且配置 `FloatingDamageColor=true`）、
   `sym_eval_mod`、`sym_font_*`(4)、`sym_dupe_dropped_item`、`sym_print_error_display`、
   `sym_ItemHasLabel`、`sym_LootRollForAncientLegendary`、`sym_ACD_AttributesGet*`。
   其中 `ACD_AttributesGet*` 实为**叶子 getter**（首条就是 `ldr x0,[x0,#0x168]`），是合法的；
   `dupe_dropped_item`/`font_*` 只在 lobby / 字体功能里用。
   **未改**：向上找"最近帧指令"的启发式给出多个候选，不可靠，需按函数签名或引用字符串交叉定位。
3. 方法论教训已记入 memory：**补丁类偏移必须按类型分别判形状**
   （`_movz/_movk` → 目标寄存器一致；`_ret` → 原址是序言；`_adrl` → 原址是 ADRP 且 site+4 是同寄存器 ADD，
   两个 ADRP 连排即说明该对被重排；raw `_bytes` → 新指令与原指令同形）。
   `tools/audit.py` 即该判据的实现。

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
