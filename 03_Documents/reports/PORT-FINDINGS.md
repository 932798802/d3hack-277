# d3hack 移植到 Diablo III 2.7.7.92380 —— 可行性调查结论

日期：2026-10-08　| 工作目录：本仓库根

---

## 0. 一句话结论

**移植的技术障碍已清除 —— 不需要 2.7.6 参照二进制。**

原以为必须有 2.7.6.90885 的 `exefs/main` 才能做差分重定位；该文件确认不存在于 XCI 内、
本地也找不到。改用「公开跨版本金手指表 + 源码记录里的原始指令字节」反推，
已重建出 2.7.6→2.7.7 的地址平移函数，并用 **20 余条互相独立的锚点**交叉验证通过。

平移函数：**0 / +0x10 / +0x70 / +0x100 四段阶梯，总增量仅 256 字节**。
449 条偏移已生成，**442 条确定，3 条残余待定，4 条需重新分配 padding 地址**。
下一步是改源码 + 构建，不再是「能不能做」的问题。

---

## 1. 目标与现状

| 项 | 值 |
|---|---|
| 目标游戏 | Diablo III Eternal Collection (Switch)，TitleID `01001B300B9BE000` |
| 目标版本 | **2.7.7.92380**（更新 NCA，XCI 内 `v1441792`） |
| Mod 锁定版本 | **2.7.6.90885** |
| 2.7.7 发布 | 2024-01-09（全平台含 Switch，**已实测确认**） |
| Mod 最后提交 | 2026-02-22（停更 ≈7.5 个月） |

XCI 内实际包含两个 Program NCA，都不是 2.7.6：

| NCA | 角色 | 版本（实测） | text 大小 |
|---|---|---|---|
| `244b8415…nca` (14.28 GB) | 本体 1G | **2.6.2.52309** | 0xC20000 |
| `ee56073d…nca` (3.35 GB) | 更新 1U | **2.7.7.92380** | 0xC73000 |

---

## 2. 已建成的提取链路（可复用）

既有工具链里的 NCA 解析只到「NCA 文件」层，缺「XCI 容器」层，已补齐：

| 脚本 | 作用 |
|---|---|
| `tools/xci.py` | XCI 解析：根 HFS0 → 分区 → 枚举 NCA（含解密后的 header） |
| `tools/nca_xci.py` | **XCI 内 NCA 免拷贝读取**（3.35 GB 的更新包直接 seek，不复制）+ 区段解密 |
| `tools/probe_crypto.py` | 暴力枚举加密参数并用魔数自校验 |
| `tools/dump_exefs.py` | ExeFS(PFS0) → `main`(NSO0) → LZ4 → `main.text/rodata/data.bin` |
| `tools/probe_drift.py` | 版本串定位 + 2.7.6 锚点在 2.7.7 的落点 |
| `tools/probe_prologue.py` | 函数序言命中率 / delta 直方图分析 |

环境：隔离 venv `<隔离 venv>`
（pycryptodome 3.24.0、lz4 4.4.5，**均取自 PyPI 官方源**）；
反汇编用 devkitPro 自带的 `aarch64-none-elf-objdump`。

产物：`work/update277/exefs/`（2.7.7 全段）、`work/base1G/exefs/`（2.6.2 全段）。

### 踩到的三个坑（均为**实测**，非推导）

1. **这份 XCI 的 HFS0 条目布局不符合公开规范。**
   实测布局为 `[offset u64][size u64][name_off u32][hashed_size u32][reserved u64][sha256 0x20]`（0x40 字节）。
   按规范「name_offset 在 +0x00」解析时，**只有 entry 0 侥幸正确**（因为其 name_offset 恰好也是 0）。
   另外 XCI 头 0x110 字段是垃圾值，真实的根 HFS0 偏移在 **0x130**（本镜像 = 0xF000）。
   → 最终改为「扫描 HFS0 + 用分区名自校验」定位，避免静默错解。

2. **NCA 区段 CTR 的计数器偏移必须含 0xC00。**
   `ctr8` 需字节反转，且 `ofs = (media_off + 0xC00) >> 4`。
   若按常见写法用 `media_off >> 4`，**没有任何一个区段能解出魔数**（输出熵恒为 8.000）。
   同时 FS 头里的 `fs_type/crypto_type` 也不在公开规范的 0x40/0x44，
   实测在 **+0x02/+0x03**；照规范读会得到 0，从而走「明文」分支并**静默返回噪声**。

3. 本体 NCA 是 2.6.2.52309，不是 2.7.6 —— 不要拿它当参照。

---

## 3. 移植规模（实测统计）

| 来源 | 条目数 |
|---|---|
| `source/program/offsets.hpp` 主表 | 258 |
| `source/program/offsets_patch_only.inl`（含 ResHack） | 191 |
| **合计需重定位的偏移** | **449** |
| 其它位置硬编码地址常量（hook/patches 内） | ≈359 |
| 版本门 | 3 处 |

版本门三处：
- `build_info.hpp` → `#define D3CLIENT_VER "2.7.6.90885"`
- `version.hpp` → `UserVersion` 枚举 + `DetermineUserVersion()`
- `main.cpp:42` → `kBuildVersionFullOffset = 0x0E45863`（rodata 版本串）

**好消息**：`offsets.hpp` 的注释里作者已写明「新增支持版本」的四步流程，
说明这套表**本来就是为多版本设计的** —— 移植走的是作者预留的正路，不需要改架构。

---

## 4. 漂移测量（决定可行性的核心数据）

### 4.1 原位命中率极低

213 个 `sym_*` 偏移中，在 2.7.7 原位命中「严格函数序言」（仅 frame-push 类指令：

`stp x?,x?, [sp,#-N]!` / `paciasp`）的只有 **6 个**；而全 .text 的序言基准率是 0.252%。

→ **2.7.6 的偏移基本不能直接在 2.7.7 上用。**

### 4.2 但存在极强的分段平移结构

delta 直方图（每个偏移 ±0x40000 窗口内的共现统计）：

| delta | 共现数 | 占 213 个 sym 的比例 |
|---|---|---|
| **+0x100** | **32** | **15.0%** |
| +3488 | 10 | 4.7% |
| +1088 | 9 | 4.2% |
| +42848 | 9 | 4.2% |
| +18656 | 9 | 4.2% |

+0x100 这个峰比随机期望高约 **60 倍**（随机期望每个 delta ≈ 0.25%），**这个峰是真实的**。
加上后面一连串次级峰，说明代码是**分段等距平移**。

### 4.3 实证锚点（最硬的一条证据）

`bdMemory` 一族是 6 个 0x10 间距的薄 thunk。2.7.7 反汇编：

```
 c30: orr w1, wzr, #0x4     <- sym_bdMemory_alloc        (2.7.6 表: 0x000C30)
 c40: mov x1, xzr           <- sym_bdMemory_free         (2.7.6 表: 0x000C40)
 c50: mov x2, x1            <- sym_bdMemory_realloc      (2.7.6 表: 0x000C50)
 c60: mov x2, xzr           <- sym_bdMemory_aligned_alloc(2.7.6 表: 0x000C60)
 c70: mov x1, xzr           <- sym_bdMemory_aligned_free (2.7.6 表: 0x000C70)
 c3c: b 0xa36e20            <- 尾调用，指向 SigmaMemoryNew
```

**前 5 个 offset 与 2.7.6 表完全一致（delta = 0）**；
但尾调用目标 `SigmaMemoryNew` 在 2.7.7 位于 0xA36E20，而 2.7.6 表里是 0xA36D20 —— **正好 +0x100**。

→ 结论：**插入点在 0xC80 与 0xA36000 之间，其后整体前移 0x100**。
这一条同时解释了「<0x300000 部分存活」和「≥0x300000 需要 +0x100」。

---

## 5. 阻塞点

**缺少 2.7.6.90885 的 `exefs/main`。** 没有它：

- 449 条偏移只能靠人工语义分析（字符串交叉引用、调用模式）逐个重找，
  对一条 13 MB 的 stripped ARM64 代码，这是研究项目而不是移植；
- 有它的话，这是一个**标准化、几乎可全自动的差分重定位流程**，工作量差一个数量级。

⚠️ 而 d3hack README 给出的获取途径是：从 **Discord** 下载 2.7.6 的
`exefs/main` + `CoreCommon.cpk` + `ServerCommon.cpk`（还附了 MD5）。
这是**受版权保护游戏文件的盗版分发渠道**，按既定规矩**不采用**。

### 生态核查（已遍历全部数据源）

- d3hack 的 **6 个 fork**：只有 `slothic/d3hack` 有后续开发
  （分支 `v3.8` … `v3.18`，最后 push 2026-09-09，4★）。
- 但 `slothic` 的 `build_info.hpp` **仍然锁 2.7.6.90885** → 是功能迭代，不是版本适配。
- **结论：全网没有现成的 2.7.7 移植。**

### 社区现状（相关 issue）

- #3「too low of game version」——用户被 2.6.10 版本锁死卡住（open）
- #9 Atmosphere 1.11.1 / FW 22.1.0 下启动失败（v3.1 早于 AMS 1.11）（open）
- #4 Ryujinx / Eden 卡启动（closed）

---

## 6. 最终结论：不需要 2.7.6，平移函数已重建并钉死

原计划是找一份 2.7.6.90885 作参照。**作者确认找不到**，且已穷尽核实 XCI 里也不存在。
于是改走「跨版本锚点反推」路线，已成功。

### 6.1 答案：2.7.6 不在 XCI 里

`tools/scan_all_ncas.py` 穷尽扫描 XCI 内全部 **18 个 NCA**：

| NCA | 类型 | 实测版本标记 |
|---|---|---|
| `244b8415…` | Program 14.28 GB | **2.6.2.52309** |
| `ee56073d…` | Program 3.35 GB | **2.7.7.92380** |
| 其余 16 个 | Control / Meta / Manual / PublicData | 全 ≤ 1.4 MB，装不下 9.7 MB 的 exefs/main |

18 个 NCA 的大小之和 ≈ XCI 文件大小（差额仅 65 024 B，是 HFS0 头与对齐）。
能装下游戏二进制的只有那 2 个 Program NCA。**XCI 里不存在 2.7.6。**
（游戏更新包是**完整替换**而非增量补丁，所以「新版里藏着旧版」这个前提本身也不成立。）

### 6.2 方法：公开跨版本金手指表 = 现成的跨版本锚点

中文 Switch 圈子发布的金手指帖**同一条代码给出多个版本各自的地址**，且 **2.7.6 表里的地址与
d3hack 的 2.7.6 表逐条吻合**（`0040F9B0`、`008874D0`、`0088DF10/DFE0/DFFC` …），
说明两边都是准确的 2.7.6 映射。

配对规则：**必须校验指令值**——mod 表注明它写入的字节，金手指表给出该地址的字节，
两者相等才认作同一位置（否则会把两个无关站点配成一对）。

此外还有两条独立于金手指的硬证据：`patches.cpp` 里记录的**原始指令字节**
（`A8 00 90 36` = TBZ、`41 FF FF 97` = BL）可直接在 2.7.7 里搜到对应位置。

### 6.3 重建出的平移函数（已钉死）

```
delta(x) = 0        x <  0x29CBB0
         = +0x10    0x29CBB0 <= x < 0x3A73A8
         = +0x70    0x3A73A8 <= x < 0x495BC0
         = +0x100   x >= 0x495BC0
```

**总增量仅 +0x100 = 256 字节**，与「2.7.7 是平衡性 / 祭坛数值调整、代码几乎未动」的定位吻合。
推论 `2.7.6 text ≈ 0xC72A90 / 2.7.7 text = 0xC72B90` 与金手指界的 code cave 用法互相印证。

验证锚点（互相独立，全部指向同一函数）：

| 2.7.6 | delta | 依据 |
|---|---|---|
| 0x1DCFA4 / 0x20636C / 0x236D30 | 0 | 金手指值匹配 ×3 |
| 0x349B98 / 0x351CBC / 0x358A7C / 0x362800 / 0x3656B8 / 0x335B68 | +0x10 | 金手指值 + 原始指令形态（B.NE / MOVZ W1 / ADRP） |
| 0x40F9B0 / 0x47AD0C / 0x4873E4 | +0x70 | 金手指值 ×2 + 原始 BL 字节搜索 |
| 0x488BA0 / 0x488EC0 / 0x489210 / 0x48E910 / 0x490F20 | +0x70 | **5/5** 在 +0x70 是栈帧建立指令，+0x10 全是函数体中部 |
| 0x4A7BD8 | +0x100 | **17/18** 的 `mov w3, wzr` 严格 0x2C 等距重复 |
| 0x4CACB8 / 0x4FFFE4 / 0x504C78 / 0x6A255C | +0x100 | 原始 TBZ 字节 + 金手指值 ×3 |
| 0x8874D0 / 0x88DF10 / 0x88DFE0 / 0x88DFFC | +0x100 | 金手指值 ×4 |
| 0x9BC828 / 0x9E3250 | +0x100 | 金手指值 ×2 |

### 6.4 产物

`out/offsets_277.csv` —— 449 条全表：
**442 条确定，3 条残余待定（0x29CBB0、0x333300、0x495BC0），4 条 CAVE。**

`out/table_277_fragment.txt` —— 可直接粘进 `offsets.hpp` 的 C++ 表片段。

### 6.5 剩余工作

1. `nvn.hpp` 的 `kSwapchainTexCreateLrOffsets[]` 逐条核对；
2. 改源码：`version.hpp` 加 `UserVersion::V277` + `DetermineUserVersion` 分支；
   `build_info.hpp` 加 2.7.7 版本串；`main.cpp` 版本门按版本取值（2.7.7 的
   `kBuildVersionFullOffset` = **0xE4BCDB**）；`offsets.hpp` 追加第二张表；
3. **CAVE 4 条**（`patch_cheat_gem_lvl150_*`，2.7.6 占用 0xC72F7C–0xC72F88）
   必须重新分配到 2.7.7 的 padding（0xC72B90–0xC73000），不能平移；
4. 拉 exlaunch / imgui submodule → devkitPro 构建 → 交付 SD 目录结构；
5. `AllowOnlinePlay` 保持 `false`。

### 6.6 风险

偏移错一条即崩溃或静默损坏。当前残余不确定仅 3 条（占 0.7%），
但这 3 条在落地前需单独用反汇编确认。

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
