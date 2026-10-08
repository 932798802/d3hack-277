#!/usr/bin/env bash
# ============================================================================
#  d3hack 2.7.7.92380 port - 一键构建 + 组装 SD 卡交付件
#
#  【必须】在 devkitPro 自带 msys2 的 bash 里跑（从 Git Bash 直接调会因路径
#  口径和环境变量被过滤而失败）：
#
#      "<devkitPro>/msys2/usr/bin/bash.exe" -l \
#          "<仓库根>/05_Code/scripts/build.sh"
#
#  两个踩过的坑（照普通 CMake 工程写会失败）：
#   1) 构建目录**不能含空格**。misc/link.ld 是通过 GCC specs 的 -T 传进去的，
#      而 GCC specs 无法给路径加引号 —— 含空格的工程路径会被截断。
#      所以先 tar 复制到无空格暂存目录再构建。
#   2) git header 生成那一步要调 `python`，必须能在 PATH 里找到它。
#
#  机器相关的路径（Python 解释器、暂存目录等）写在同目录的 local.env 里
#  （该文件不入库），本脚本会自动 source。格式见 local.env.example。
# ============================================================================
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # 05_Code/scripts
ROOT="$(cd "$HERE/../.." && pwd)"                       # 仓库根

# ---- 机器相关覆盖（可选）----
# shellcheck disable=SC1091
[ -f "$HERE/local.env" ] && . "$HERE/local.env"

export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITA64="${DEVKITA64:-$DEVKITPRO/devkitA64}"
export PATH="$DEVKITPRO/msys2/usr/bin:$DEVKITA64/bin:$DEVKITPRO/tools/bin:$PATH"
[ -n "$PYTHON_DIR" ] && export PATH="$PYTHON_DIR:$PATH"

SRC="$ROOT/05_Code/d3hack"
OUT="$ROOT/04_Outputs/v0.1/sdcard"
STAGE="${D3HACK_STAGE:-${TMPDIR:-/tmp}/d3hack-build}"   # 必须无空格

echo "仓库根 : $ROOT"
echo "暂存目录: $STAGE"

echo "=== 1/4 复制源码到无空格暂存目录 ==="
rm -rf "$STAGE"; mkdir -p "$STAGE"
( cd "$SRC" && tar cf - --exclude=./build --exclude=./deploy . ) | ( cd "$STAGE" && tar xf - )

echo "=== 2/4 configure ==="
cd "$STAGE"
cmake --preset switch 2>&1 | tail -3

echo "=== 3/4 build ==="
cmake --build --preset switch -j 8 2>&1 | grep -vE "^\[ *[0-9]+%\]" | tail -15

echo "=== 4/4 组装交付目录 ==="
EXEFS="$OUT/atmosphere/contents/01001b300b9be000/exefs"
ROMFS="$OUT/atmosphere/contents/01001b300b9be000/romfs/d3gui"
mkdir -p "$EXEFS" "$ROMFS" "$OUT/config/d3hack-nx"
cp "$STAGE/build/d3hack-build.nso"  "$EXEFS/subsdk9"
cp "$STAGE/build/d3hack-build.npdm" "$EXEFS/main.npdm"
cp -R "$SRC/data/."                  "$ROMFS/"
cp -R "$SRC/examples/config/d3hack-nx/rift_data/." "$OUT/config/d3hack-nx/rift_data/"
# sdcard/config/d3hack-nx/ 下的 config.toml 由人手维护，本脚本不覆盖它。
# 强约束校验：AllowOnlinePlay 必须为 false（开着联机用属作弊，有封号风险）
if ! grep -qE '^[[:space:]]*AllowOnlinePlay[[:space:]]*=[[:space:]]*false' "$OUT/config/d3hack-nx/config.toml" 2>/dev/null; then
    echo "" >&2
    echo "!! 警告：config.toml 里 AllowOnlinePlay 不是 false，别把这样的包发出去。" >&2
fi

echo
echo "=== 产物 ==="
ls -la "$EXEFS/"
sha256sum "$EXEFS/subsdk9" "$EXEFS/main.npdm"
echo
echo "提示：romfs/d3gui 每版都会重写；config/ 下的 config.toml 不会被覆盖。"
echo "      SD 卡上要跑二分排查就用 04_Outputs/v0.1/config.safemode.toml 覆盖过去。"
