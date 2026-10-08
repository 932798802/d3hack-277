#!/usr/bin/env bash
# ============================================================================
#  拉取 d3hack 的两个依赖（上游是以 submodule 引的，我们按**固定 commit** 取，
#  避免默认分支漂移）。两者都是 MIT 许可。
#
#    include/tomlplusplus        marzer/tomlplusplus
#    source/third_party/imgui    ocornut/imgui
#
#  用法（Git Bash 或 msys2 bash 均可）：
#      bash scripts/fetch-deps.sh
#
#  注意：本机有 MITM 代理，curl 需要 -k（证书是代理自签的）。
#        如果换了网络环境且没有代理，把 -k 去掉更稳妥。
# ============================================================================
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # -> 05_Code/
SRC="$HERE/d3hack"                                        # mod 源码
TMP="$HERE/../10_Other/cache/tmp"                          # 下载缓存（不入库）

TOML_REPO="marzer/tomlplusplus"
TOML_SHA="7807a314ad1c0c9c227d9dbd68f23f187163372e"
TOML_DEST="$SRC/include/tomlplusplus"

IMGUI_REPO="ocornut/imgui"
IMGUI_SHA="f58378711fe17c1988671a34ee4c89022b299edf"
IMGUI_DEST="$SRC/source/third_party/imgui"

mkdir -p "$TMP"

fetch_one() {
    local repo="$1" sha="$2" dest="$3" tag="$4"
    local zip="$TMP/$tag.zip"
    echo "--- $repo @ $sha -> ${dest#$HERE/} ---"
    curl -k -sSL -o "$zip" "https://codeload.github.com/$repo/zip/$sha"
    [ -s "$zip" ] || { echo "下载失败：$zip"; exit 1; }
    echo "    sha256(zip) = $(sha256sum "$zip" | cut -d' ' -f1)"
    rm -rf "$dest"; mkdir -p "$dest"
    python - "$zip" "$dest" <<'PY'
import sys, zipfile, os, shutil
z, dest = sys.argv[1], sys.argv[2]
zf = zipfile.ZipFile(z)
top = zf.namelist()[0].split('/')[0]
n = 0
for name in zf.namelist():
    if name.endswith('/'):
        continue
    rel = name[len(top) + 1:]
    if not rel:
        continue
    t = os.path.join(dest, rel)
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with zf.open(name) as s, open(t, 'wb') as o:
        shutil.copyfileobj(s, o)
    n += 1
print('    %d files extracted' % n)
PY
}

fetch_one "$TOML_REPO"  "$TOML_SHA"  "$TOML_DEST"  "tomlplusplus"
fetch_one "$IMGUI_REPO" "$IMGUI_SHA" "$IMGUI_DEST" "imgui"

echo
echo "完成。现在可以跑 scripts/build.sh 构建。"
