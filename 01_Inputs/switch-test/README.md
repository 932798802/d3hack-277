# test/ —— 实机测试的原始数据放这里（不入库）

每次在 Switch 上实测后，把下面这些直接拷进本目录（或按测试批次建子目录）：

| 要拷的东西 | 从哪来 | 用途 |
|---|---|---|
| `crash_reports/` **整个目录** | `SD:/atmosphere/crash_reports/` | 含 `.log`（寄存器/堆栈）+ `.jpg` + `dumps/`。**有 `.log` 就能算出 PC → 模块偏移 → 定位到具体哪条补丁** |
| `D3Debug.txt` | `SD:/config/d3hack-nx/D3Debug.txt` | mod 的启动日志（boot stage / 版本门 / hook 列表 / patch 列表） |
| `user_exception.txt` | `SD:/config/d3hack-nx/` | mod 自带异常处理器抓到的崩溃（需 `[debug] EnableExceptionHandler = true`） |
| `error_manager_dump.txt` | `SD:/config/d3hack-nx/` | 游戏 ErrorManager 的转储 |
| `config.toml` | `SD:/config/d3hack-nx/` | 出事时用的那份配置 |

本目录内容被 `.gitignore` 排除（体积大、含内存转储、且属于运行期数据）。
**排查结论请写进 `DIAGNOSIS.md`**，只把结论入库。

## 怎么算崩溃地址

```bash
# 模块基址 = PC - PC 对应的模块偏移（报告里括号内已给出 "DiabloIIINX64r.nss + 0xXXXXXX"）
# 直接读报告的 PC 行即可：
#   PC: 0000000f23b66850 (DiabloIIINX64r.nss + 0x362850)
#                                          ^^^^^^^^ 这个就是模块偏移，拿它去 offsets 表里查
```
