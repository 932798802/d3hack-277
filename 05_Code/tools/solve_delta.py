#!/usr/bin/env python3
"""Reconstruct the 2.7.6 -> 2.7.7 address delta function WITHOUT the 2.7.6 binary.

Motivation
----------
Public multi-version cheat tables (Chinese Switch community forums) list the SAME cheat
for several game builds, each with its own address. Pairing those with d3hack's
2.7.6 table -- which documents both the 2.7.6 address AND the exact bytes it
writes -- yields exact (2.7.6 -> 2.7.7) anchors, but ONLY when the instruction
value matches, otherwise two unrelated sites get paired.

Anchors confirmed this way (verified value match):
    0x1DCFA4 -> 0x1DCFA4   delta 0
    0x20636C -> 0x20636C   delta 0
    0x236D30 -> 0x236D30   delta 0
    0x349B98 -> 0x349BA8   delta +0x10
    0x4F98DC -> 0x4F99DC   delta +0x100
    0x504C78 -> 0x504D78   delta +0x100
    0x6A255C -> 0x6A265C   delta +0x100
    0x8874D0 -> 0x8875D0   delta +0x100
    0x88DF10 -> 0x88E010   delta +0x100
    0x88DFFC -> 0x88E0FC   delta +0x100
    0x88DFE0 -> 0x88E0E0   delta +0x100
    0x9BC828 -> 0x9BC928   delta +0x100
    0x9E3250 -> 0x9E3350   delta +0x100
plus the bdMemory cluster (0xC30.., delta 0) vs SigmaMemoryNew (0xA36D20 -> 0xA36E20, +0x100).

That brackets a step function: 0 below b1, +0x10 on [b1,b2), +0x100 from b2.
This script searches b1,b2 by requiring d3hack's 213 `sym_*` offsets to land on
AArch64 function entries in the 2.7.7 .text.

Usage:
    python solve_delta.py <exefs_dir> <d3hack_src_dir>
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from probe_prologue import extract_sym_offsets, read_text  # noqa: E402

# Function-entry markers: instructions that establish a frame. Using only
# frame-establishing forms keeps the base rate near 0.6% so hits are meaningful.
ENTRY = [
    ("stp_pre_sp", 0xFFC003E0, 0xA98003E0),   # stp x?,x?,[sp,#-N]!
    ("sub_sp", 0xFFC003FF, 0xD10003FF),       # sub sp,sp,#imm
    ("paciasp", 0xFFFFFFFF, 0xD503233F),
    ("pacibsp", 0xFFFFFFFF, 0xD503237F),
]

B1_LO, B1_HI = 0x00000C80, 0x00349B98
B2_LO, B2_HI = 0x00349B98, 0x004F98DC


def main():
    exefs, src = sys.argv[1], sys.argv[2]
    text = read_text(exefs)
    n = len(text) // 4
    vals = struct.unpack_from("<%dI" % n, text, 0)

    isentry = bytearray(n)
    for i in range(n):
        w = vals[i]
        for _nm, mask, val in ENTRY:
            if (w & mask) == val:
                isentry[i] = 1
                break
    base = sum(isentry) / n
    print("text %d B, %d positions, entry base rate %.3f%%"
          % (len(text), n, 100 * base))

    pairs = extract_sym_offsets(src)
    syms = sorted(o for o, k, _r in pairs if k.startswith("sym_") and o < len(text))
    print("sym_* offsets in .text: %d" % len(syms))

    def hit(o):
        j = o // 4
        return 1 if 0 <= j < n and isentry[j] else 0

    # Precompute per-sym hit for each of the three candidate targets.
    tab = []
    for o in syms:
        tab.append((o, hit(o), hit(o + 0x10), hit(o + 0x100)))

    # The score only changes when a breakpoint crosses a sym offset, so the
    # search space collapses to O(|syms|^2) distinct cases.
    cands_b1 = [B1_LO] + [o for o in syms if B1_LO < o <= B1_HI]
    cands_b2 = [o for o in syms if B2_LO < o <= B2_HI] + [B2_HI + 1]
    print("search space: %d x %d = %d" % (len(cands_b1), len(cands_b2),
                                          len(cands_b1) * len(cands_b2)))

    best = []
    for b1 in cands_b1:
        for b2 in cands_b2:
            if b2 <= b1:
                continue
            s = 0
            for o, h0, h1, h2 in tab:
                s += h0 if o < b1 else (h1 if o < b2 else h2)
            best.append((s, b1, b2))
    best.sort(reverse=True)

    print("\n=== top 10 (score = how many of %d sym_* land on a function entry) ==="
          % len(syms))
    for s, b1, b2 in best[:10]:
        print("   b1=0x%08X  b2=0x%08X   hits=%3d/%d = %.1f%%"
              % (b1, b2, s, len(syms), 100.0 * s / len(syms)))
    print("\nbaselines: delta 0 everywhere = %d/%d ; delta +0x100 everywhere = %d/%d"
          % (sum(h0 for _o, h0, _h1, _h2 in tab), len(syms),
             sum(h2 for _o, _h0, _h1, h2 in tab), len(syms)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
