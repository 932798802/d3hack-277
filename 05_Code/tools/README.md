# 05_Code/tools —— 偏移分析与校验工具

这些脚本**不接触密钥、不解密任何内容**，只负责「把 2.7.6 的偏移搬到 2.7.7」以及
「验证搬得对不对」。它们是这次移植能定位到崩溃点的关键。

## 输入从哪来

绝大多数脚本读一份**已解开的 2.7.7 模块镜像**：

```
10_Other/cache/work/update277/exefs/main.text.bin      # .text  13,052,816 B
                         main.rodata.bin               # .rodata
                         main.data.bin                 # .data
```

这份镜像由「内容提取类脚本」产出（见下节），**不随仓库分发**。

## 工具清单

| 脚本 | 作用 |
|---|---|
| `probe_drift.py` | 建一个扁平模块镜像，定位版本串锚点、测量 2.7.6 偏移在 2.7.7 的漂移 |
| `probe_prologue.py` | 用「函数序言命中率」反推平移量：把所有 `sym_*` 偏移按候选 delta 平移后统计命中率与基准率之比 |
| `solve_delta.py` | 用**公开跨版本金手指表**与上游源码里记录的原始指令字节，配对出精确的 (2.7.6 → 2.7.7) 锚点，反推分段平移函数 |
| `build_table.py` | 按反推出的平移函数生成 449 条 2.7.7 偏移表（`.text` 平移；`.data`/`.bss` 不平移；rodata 单独定位），输出 CSV + 可直接粘贴的 C++ 片段 |
| `inject_table.py` | 把生成的表就地写回 `offsets.hpp` / `offsets_patch_only.inl` |
| `audit.py` | **逐站点指令形状复核**：按补丁类型判断原址指令是否合理（见下），列出需改址/无法判定的条目 |
| `verify2.py` / `verify_regs.py` | `audit.py` 的早期版本（判据更窄，保留作为对照） |

### `audit.py` 用到的形状判据

「统一平移量」在被编译器重写过的函数里不成立，所以补丁类偏移必须**逐条按类型判形状**：

| 补丁类型 | 判据 |
|---|---|
| `_movz` / `_movk` / `_movn` | 目标寄存器与补丁声明的寄存器一致（强制返回型除外） |
| `_ret` | 原址应是函数序言（`sub sp` / `stp …, [sp,#-N]!`） |
| `_adrl` | 原址应是 `ADRP`，**且 site+4 是同寄存器 `ADD`/`LDR`**；两个 `ADRP` 连排说明该对被重排 |
| raw `_bytes` | 新旧指令应同形（例如都是 `LDR Xd,[Xn,#imm]`） |

另外：**`HOOK_DEFINE_INLINE` 类 hook 不需要落在函数入口**（它挂在具体指令上，回调读
`ctx->X[n]`），只有 `TRAMPOLINE` / `REPLACE` 类才要求函数入口 —— 用错判据会误报一大批。

## 未随仓库分发的脚本

以下 5 个脚本**刻意不公开**（它们需要 `prod.keys` 去解密 NCA/XCI、从游戏包里抽出可执行文件）：

```
xci.py             XCI 容器层（根 HFS0 → secure 分区 → NCA 列表）
nca_xci.py         NCA 头/区段解密，取出 ExeFS(PFS0)
dump_exefs.py      ExeFS → main(NSO0) → LZ4 解压 → text/rodata/data
probe_crypto.py    暴力确定区段加密参数（crypto_type / key 槽位 / CTR 计数器偏移）
scan_all_ncas.py   枚举 XCI 内全部 NCA 并识别版本
```

原因：这类"用密钥解内容"的工具与被平台下架的工具属同一形态，本仓库只想发布
**偏移分析 + 补丁验证**这部分。它们在本地产出的镜像就是上面那份 `main.text.bin`。
