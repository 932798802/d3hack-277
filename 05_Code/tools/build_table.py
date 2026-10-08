#!/usr/bin/env python3
"""Generate the 2.7.7 offset table by applying the reconstructed delta function.

Delta function (evidence in PORT-FINDINGS.md):
    delta(x) = 0        x <  b1
             = +0x10    b1 <= x < b2
             = +0x70    b2 <= x < b3
             = +0x100   x >= b3

Verified anchors (instruction-value match against public multi-version cheat
tables, or exact original-byte search in 2.7.7):
    0x1DCFA4 -> +0x00   0x20636C -> +0x00   0x236D30 -> +0x00
    0x349B98 -> +0x10
    0x40F9B0 -> +0x70   0x47AD0C -> +0x70   0x4873E4 -> +0x70
    0x4A7BD8 -> +0x100 (also 17/18 structural match of the 0x2C event grid)
    0x4CACB8 -> +0x100  0x4FFFE4 -> +0x100  0x504C78 -> +0x100
    0x6A255C -> +0x100  0x8874D0 -> +0x100  0x88DF10/E0/FC -> +0x100
    0x9BC828 -> +0x100  0x9E3250 -> +0x100

Therefore b1 in (0x29B1E0, 0x349B98], b2 in (0x349B98, 0x40F9B0],
b3 in (0x4873E4, 0x495BC0].

Entries whose address falls inside a bracket window are reported as 待验
because their delta depends on the unresolved breakpoint; everything else is
settled by the anchors.

Usage:
    python build_table.py <d3hack_src_dir> <out_dir> [b1 b2 b3]
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from probe_prologue import extract_sym_offsets  # noqa: E402

TEXT_276 = 0xC72A90          # implied by text_277 = 0xC72B90 and end delta +0x100
B1, B2, B3 = 0x29CBB0, 0x3A73A8, 0x495BC0
# Residual uncertainty windows after the disassembly-based validation pass.
# b1 in {0x29CBB0, 0x333300}   -> only 0x29CBB0's own delta is open
# b2 in (0x369384, 0x3E568]    -> ddm_labels cluster observed at +0x70
# b3 in (0x490F20, 0x4A7BD8]   -> 5/5 ACD/lobby entries observed at +0x70
W1 = (0x29B1E0, 0x335B68)
W2 = (0x369384, 0x3E568)
W3 = (0x490F20, 0x4A7BD8)

# The 4 entries that d3hack parks in the .text->.rodata padding ("code cave").
# They must be re-homed into 2.7.7's padding, NOT shifted.
CAVE = {0xC72F7C, 0xC72F80, 0xC72F84, 0xC72F88}


def delta(x, b1, b2, b3):
    if x < b1:
        return 0
    if x < b2:
        return 0x10
    if x < b3:
        return 0x70
    return 0x100


def main():
    src = sys.argv[1]
    out = sys.argv[2]
    b1, b2, b3 = (int(sys.argv[3], 0), int(sys.argv[4], 0), int(sys.argv[5], 0)) \
        if len(sys.argv) > 5 else (B1, B2, B3)
    os.makedirs(out, exist_ok=True)

    pairs = extract_sym_offsets(src)
    rows = []
    for off, key, rel in pairs:
        in_window = (W1[0] < off < W1[1]) or (W2[0] < off < W2[1]) or (W3[0] < off < W3[1])
        if off in CAVE:
            rows.append((off, key, None, None, "CAVE", rel))
            continue
        d = delta(off, b1, b2, b3)
        conf = "待验" if in_window else "确定"
        rows.append((off, key, d, off + d, conf, rel))
    rows.sort(key=lambda r: (r[0], r[1]))

    csv_path = os.path.join(out, "offsets_277.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["off_276", "key", "delta", "off_277", "confidence", "source"])
        for off, key, d, o277, conf, rel in rows:
            w.writerow(["0x%08X" % off, key,
                        "-" if d is None else "+0x%X" % d,
                        "-" if o277 is None else "0x%08X" % o277, conf, rel])

    n_det = sum(1 for r in rows if r[4] == "确定")
    n_todo = sum(1 for r in rows if r[4] == "待验")
    n_cave = sum(1 for r in rows if r[4] == "CAVE")
    print("delta function: b1=0x%X b2=0x%X b3=0x%X" % (b1, b2, b3))
    print("entries: %d  (确定 %d / 待验 %d / CAVE %d)"
          % (len(rows), n_det, n_todo, n_cave))
    print("wrote %s" % csv_path)

    # also emit a ready-to-paste C++ table fragment
    cpp_path = os.path.join(out, "table_277_fragment.txt")
    with open(cpp_path, "w", encoding="utf-8") as fh:
        fh.write("            /* --- 2.7.7.92380 overrides --- */\n")
        for off, key, d, o277, conf, rel in rows:
            if conf != "确定":
                continue
            fh.write('            { util::ModuleIndex::Main, 0x%X, "%s" },%s\n'
                     % (o277, key,
                        "   // was 0x%X" % off if off != o277 else ""))
    print("wrote %s" % cpp_path)

    print("\n=== 待验条目（其 delta 取决于未定的 b1/b2/b3）===")
    for off, key, d, o277, conf, rel in rows:
        if conf == "待验":
            print("  0x%-8X %-46s 当前假设 delta=+0x%X" % (off, key, d))
    print("\n=== CAVE 条目 ===")
    for off, key, d, o277, conf, rel in rows:
        if conf == "CAVE":
            print("  0x%-8X %s" % (off, key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
