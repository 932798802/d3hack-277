# 01_Inputs —— 原始输入

本目录放**外部提供给我的东西**，以及**实机测试的原始数据**。

| 子目录 | 内容 | 是否入库 |
|---|---|---|
| `switch-test/` | 每次实机测试从主机/SD 拷回来的原始数据（`crash_reports/`、`D3Debug.txt`、`user_exception.txt`、出事时的 `config.toml`） | ❌ **不入库**（体积大、含内存转储、属运行期数据） |

## 游戏本体（不入库）

移植所需的原始素材是 **Diablo III: Eternal Collection 的 2.7.7.92380 XCI**
（`01001B300B9BE000`，文件名形如 `Diablo III Eternal Collection V2.7.7.92380 [01001B300B9BE000] [v1441792] (1G+1U+4D).xci`，约 22 GB）。

**它不放在本仓库内**（受版权保护，不入库，已在 `.gitignore` 里兜底）。工具链直接读仓库外的路径：

```
<游戏 XCI 的存放目录>/<那个 XCI 文件>
```

从它解出来的 `main` / ExeFS 等二进制放在 `10_Other/cache/work/`（同样不入库），
`05_Code/tools/` 里的脚本会读那一份。

解析需要的 `prod.keys` 由使用者自备（同样不入库，`.gitignore` 已兜底）。

## 崩溃/测试数据怎么用

`switch-test/` 里最有价值的是 `crash_reports/*.log` —— 里面的
`PC = ... (DiabloIIINX64r.nss + 0xXXXXXX)` 那个模块偏移，直接拿去
`04_Outputs/tables/offsets_277.csv` 或源码表里查，就能定位到是哪条补丁。
详见 `switch-test/README.md`。
