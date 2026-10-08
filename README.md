# d3hack → Diablo III 2.7.7.92380（Switch 移植）

把 [`god-jester/d3hack`](https://github.com/god-jester/d3hack)（原版锁死 `2.7.6.90885`）移植到
**Diablo III: Eternal Collection（Switch）2.7.7.92380**，TitleID `01001B300B9BE000`。

走 **Atmosphere LayeredFS**：只写 SD 卡、不动 NAND；卸载即删目录。

> **当前状态（2026-10-08）**：实机已验证 **能进主菜单 → 选人界面 → 用猎魔人正常游玩**。
> 启动期崩溃（第一版）已定位并修复；剩下的是功能级验证。

> **说明文档**：本文件（工程全貌）+ `update.md`（版本更新说明，内容取自 git 记录）。
> 技术细节全部落在 `03_Documents/reports/` 下三份报告里。

---

## 工程目录

| 目录 | 内容 | 入库 |
|---|---|---|
| `01_Inputs/` | 原始输入：`switch-test/`（实机测试的崩溃报告与日志）。**游戏本体 XCI 不放仓库内**，路径见该目录 README | ❌ 内容不入库 |
| `02_References/` | `upstream/d3hack-main-upstream.zip`（上游 main 快照，用于 diff 出我们的改动） | ✅ |
| `03_Documents/` | `reports/PORT-FINDINGS.md`（可行性论证 + 平移函数反推过程）<br>`reports/DIAGNOSIS.md`（实机日志与崩溃报告的逐步定位）<br>`reports/TEST-PLAN.md`（按风险排序的功能验证清单） | ✅ |
| `04_Outputs/` | `v0.1/`（SD 卡安装包 `sdcard/` + zip + `config.safemode.toml` + 安装说明）<br>`tables/`（重建出的 2.7.7 偏移表 CSV 与 C++ 片段） | ✅ |
| `05_Code/` | `d3hack/`（改好的 mod 源码，含 `*.orig` 原始 2.7.6 表备份）<br>`tools/`（自研 XCI→NCA→ExeFS→NSO 工具链 + 偏移校验）<br>`scripts/`（`build.sh` / `fetch-deps.sh`） | ✅ |
| `10_Other/` | `cache/work/`（从 XCI 解出的游戏二进制）、`cache/tmp/`（依赖下载缓存）、`backup/`（旧包与归档） | work/tmp ❌ |
| `README.md` | 本文件 | ✅ |
| `VERSION` / `update.md` | 版本号 / 版本更新说明 | ✅ |

---

## 构建

**前提**：devkitPro（devkitA64 + 工具链）、CMake ≥ 3.21、Python（仅用于生成 git header）。

```bash
# 1) 依赖（上游是以 submodule 引的；这里按固定 commit 取，两者均 MIT）
bash 05_Code/scripts/fetch-deps.sh

# 2) 构建 + 组装 SD 交付目录（必须在 devkitPro 自带 msys2 的 bash 里）
"<devkitPro>/msys2/usr/bin/bash.exe" -l \
    "<仓库根>/05_Code/scripts/build.sh"
```

产物：`04_Outputs/v0.1/sdcard/atmosphere/contents/01001b300b9be000/exefs/{subsdk9, main.npdm}`

### 三个必须知道的构建坑（都已在脚本/工具链里处理好）

1. **必须在 devkitPro 自带的 msys2 bash 里构建**。从 Git Bash 直接调 `cmake` 会因路径口径不同 +
   环境变量被过滤而失败。
2. **构建目录不能含空格**。`misc/link.ld` 走 GCC specs 的 `-T` 传入，specs 无法给路径加引号，
   本工程路径里的 `game mod` 会被截断成 `.../game`。脚本会先复制到无空格暂存目录（默认 `${TMPDIR:-/tmp}/d3hack-build`，可用 `D3HACK_STAGE` 覆盖）。
3. **GCC 16 新增的 `-Wnon-c-typedef-for-linkage`** 会让 vendored exlaunch 老代码在 `-Werror` 下失败，
   已在 `05_Code/d3hack/cmake/toolchain.cmake` 单点降级；同文件里 `if(WIN32)` 分支在本机取不到
   `WIN32`/`CMAKE_HOST_WIN32`（MSYS 版 cmake），已改成按文件是否存在判断 `.exe` 后缀。

---

## 我们相对上游改了什么

源码级共 6 个文件（外加上面那处本机构建适配）：

| 文件 | 改动 |
|---|---|
| `source/program/offsets.hpp` | 258 条主表就地改写为 2.7.7 地址 |
| `source/program/offsets_patch_only.inl` | 191 条 patch 表同上；`patch_autosave_string_01_adrl` 单独修正为 `0x335B68`（delta 0） |
| `source/program/build_info.hpp`<br>`version.hpp` / `main.cpp` | 收敛为**纯 2.7.7 单版本**，版本门偏移改为 `0xE4BCDB`（`"C2.7.7.92380"`） |
| `source/program/d3/patches.cpp` | ① `patch_hideonline_04..07` 注释掉 ② `patch_ddm_labels_03/04/08/09_adrl` 注释掉 |

**为什么关掉那两组成员（别以为是漏做）**

- `patch_hideonline_04..07`：2.7.7 **重写了** `UIMainMenu::Console::OnUpdate`，这 4 个地址不再是平移关系。
  其中 `_06_bytes` 落在 `0x362850`，把一条 `bl 0x35c1d0` 覆盖成 `LDR X8,[X8,#0x50]`；游戏渲染主菜单时
  X8=1 → 访存 `0x51` → **Atmosphère data abort（2168-0002）**。而 2.7.7 原生在 `0x3628DC / 0x3628F0`
  就已经 `SetVisible(0)` 隐藏了这两个在线状态标签，所以关掉**无任何视觉损失**。
- `patch_ddm_labels_03/04/08/09_adrl`：2.7.7 把 X3/X4 的 `ADRP+ADD` 对重排成
  `adrp x3; adrp x4; …; ldr x3; ldr x4`，而 `MakeAdrlPatch` 是"site 写 ADRP、site+4 写 ADD"的固定形式，
  硬套会覆盖 `adrp x4`。代价仅：DDM 标签改用游戏自带颜色（水印文字替换照常）。

完整的定位过程（含崩溃报告换算、逐站点二进制核对表）见 `03_Documents/reports/DIAGNOSIS.md`。

---

## 方法论（这套做法本身可复用）

上游锁死旧版、新版二进制在手、**旧版找不到**时，用「公开跨版本金手指表 + 上游源码里记录的原始指令字节」
反推两个版本之间的地址平移函数 —— 不依赖任何盗版渠道。要点：

- 补丁类偏移**不能只靠统一平移量**。要按类型分别判形状：
  `_movz/_movk` → 目标寄存器一致；`_ret` → 原址是函数序言；
  `_adrl` → 原址是 ADRP **且 site+4 是同寄存器 ADD**；raw `_bytes` → 新指令与原指令同形。
  （2.7.7 有若干函数被编译器重写，"阶梯平移"在这些函数里不成立 —— 第一版崩溃就出在这里。）
- **函数入口必须用函数入口的判据**：INLINE hook 只要落在正确的那条指令上，
  不要拿"是否函数入口"去要求它（否则会误报一大批）。
- 实现见 `05_Code/tools/`：`audit.py`（逐站点形状复核）、`probe_prologue.py`（平移量反推）、
  `xci.py`/`nca_xci.py`/`dump_exefs.py`（XCI→ExeFS 全链路）。

---

## 边界（照规矩说清楚）

- **不含任何游戏本体内容**：`10_Other/cache/work/`（从 XCI 解出的 `main`/`exefs`）与 `01_Inputs/switch-test/`
  都在 `.gitignore` 里；仓库只放偏移表、工具、文档与自建产物。
- **不含密钥**：`prod.keys` / `title.keys` 一律排除（`.gitignore` 兜底）。
- **没有 remote，也不打算加**。上游 d3hack 是 **GPL-2.0**，`05_Code/d3hack/` 保留其 `LICENSE` 与 `README.md`；
  `04_Outputs/` 里的 `subsdk9` 是该代码的构建产物，一并发 GPL-2.0 约束。
- `AllowOnlinePlay` 强制 `false`：开启后联机属作弊行为，有封号风险。

## 参考与出处

### 上游与本仓库改动的对应文件

| 项 | 链接 |
|---|---|
| 上游仓库 `god-jester/d3hack`（GPL-2.0） | https://github.com/god-jester/d3hack （快照见 `02_References/upstream/`） |
| `source/program/offsets.hpp` | https://github.com/god-jester/d3hack/blob/main/source/program/offsets.hpp |
| `source/program/offsets_patch_only.inl` | https://github.com/god-jester/d3hack/blob/main/source/program/offsets_patch_only.inl |
| `source/program/d3/patches.cpp` | https://github.com/god-jester/d3hack/blob/main/source/program/d3/patches.cpp |
| `source/program/main.cpp` | https://github.com/god-jester/d3hack/blob/main/source/program/main.cpp |
| `source/program/build_info.hpp` | https://github.com/god-jester/d3hack/blob/main/source/program/build_info.hpp |
| `cmake/toolchain.cmake` | https://github.com/god-jester/d3hack/blob/main/cmake/toolchain.cmake |

### 依赖与工具链

| 项 | 链接 / 版本 |
|---|---|
| exlaunch（注入框架，GPL-2.0） | https://github.com/shadowninja108/exlaunch |
| Dear ImGui（MIT） | https://github.com/ocornut/imgui/commit/f58378711fe17c1988671a34ee4c89022b299edf |
| tomlplusplus（MIT） | https://github.com/marzer/tomlplusplus/commit/7807a314ad1c0c9c227d9dbd68f23f187163372e |
| devkitPro / devkitA64 | https://devkitpro.org/ |
| libnx（Switch 自制程序库） | https://github.com/switchbrew/libnx |
| Atmosphère（崩溃报告格式与错误码判读） | https://github.com/Atmosphere-NX/Atmosphere |
| Arm A64 指令集文档（判补丁形状时的编码依据） | https://developer.arm.com/documentation/ddi0602/latest/ |

### 地址交叉验证来源

`03_Documents/reports/PORT-FINDINGS.md` 里那条 2.7.6→2.7.7 平移函数，锚点来自
**公开的多版本金手指表**（同一份代码给出各版本各自的地址）与上游源码里记录的原始指令字节。
金手指表为社区公开文档，例：https://bbs.3dmgame.com/forum.php?mod=viewthread&tid=6494006
（仅用于交叉验证地址，仓库不包含任何金手指文件。）

### 版本

原版只支持 `2.7.6.90885`；本仓库改为只支持 `2.7.7.92380`，不再兼容 2.7.6。
