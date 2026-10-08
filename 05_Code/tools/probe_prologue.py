#!/usr/bin/env python3
"""Decide whether 2.7.6 function offsets still point at function entries in 2.7.7.

A stripped AArch64 binary gives no symbol table, so we use the one structural
signal a function entry always has: a stack-frame prologue. We measure the rate
at which d3hack's hardcoded 2.7.6 `sym_*` offsets land on a prologue-shaped
instruction in the 2.7.7 .text, and compare it against the base rate over every
aligned position in .text.

Interpretation:
  * rate >> base rate  -> the layout largely survived; the port reduces to
    installing the same offsets (plus a version bump).
  * rate ~= base rate  -> the layout moved; every offset needs re derivation.

Usage:
    python probe_prologue.py <exefs_dir> <d3hack_src_dir>
"""
import os
import re
import sys

SEGS = ("text", "rodata", "data")

# Canonical AArch64 prologue shapes (Rn == SP == 31).
PATTERNS = [
    # STP <Rt>, <Rt2>, [sp, #-imm]!   (pre-index, 64-bit, Rn=31)
    ("stp_pre_sp", 0xFFC003E0, 0xA98003E0),
    ("stp_off_sp", 0xFFC003E0, 0xA90003E0),
    # SUB sp, sp, #imm
    ("sub_sp", 0xFFC003FF, 0xD10003FF),
    # ADD sp, sp, #imm  (some entries)
    ("add_sp", 0xFFC003FF, 0x910003FF),
    # STP x29,x30 pair specifically
    ("stp_29_30", 0xFFE07FFF, 0xA9807BFD),
    # PACIASP / PACIBSP (ARMv8.3 PA prologue, common on Switch)
    ("paciasp", 0xFFFFFFFF, 0xD503233F),
    ("pacibsp", 0xFFFFFFFF, 0xD503237F),
]


def read_text(exefs):
    return open(os.path.join(exefs, "main.text.bin"), "rb").read()


def prologue_kind(w):
    for name, mask, val in PATTERNS:
        if (w & mask) == val:
            return name
    return None


def extract_sym_offsets(src_dir):
    """Pull (offset, key) pairs out of the mod's offset tables."""
    out = []
    for rel in ("source/program/offsets.hpp",
                "source/program/offsets_patch_only.inl"):
        p = os.path.join(src_dir, rel)
        if not os.path.exists(p):
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(
                r"\{\s*util::ModuleIndex::Main\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*\"([^\"]+)\"",
                txt):
            out.append((int(m.group(1), 16), m.group(2), rel))
    return out


def main():
    exefs, src = sys.argv[1], sys.argv[2]
    text = read_text(exefs)
    n = len(text) // 4
    words = memoryview(text)

    import struct
    vals = struct.unpack_from("<%dI" % n, text, 0)

    # base rate over every aligned position
    hits_by_kind = {}
    hits = 0
    for i in range(n):
        k = prologue_kind(vals[i])
        if k:
            hits += 1
            hits_by_kind[k] = hits_by_kind.get(k, 0) + 1
    print("text: %d bytes, %d aligned positions" % (len(text), n))
    print("base prologue rate: %d/%d = %.3f%%" % (hits, n, 100.0 * hits / n))
    for k, v in sorted(hits_by_kind.items(), key=lambda x: -x[1]):
        print("    %-12s %8d  (%.3f%%)" % (k, v, 100.0 * v / n))

    pairs = extract_sym_offsets(src)
    syms = [(o, k) for o, k, r in pairs if k.startswith("sym_") and o < len(text)]
    other = [(o, k) for o, k, r in pairs if not k.startswith("sym_") and o < len(text)]
    print("\ntable entries: %d total, %d sym_* inside .text, %d others in .text"
          % (len(pairs), len(syms), len(other)))

    for label, lst in (("sym_*", syms), ("other", other)):
        if not lst:
            continue
        hit = sum(1 for o, _k in lst if prologue_kind(vals[o // 4]))
        print("  %-6s prologue-hit: %4d/%4d = %.1f%%" % (label, hit, len(lst),
                                                         100.0 * hit / len(lst)))

    print("\nper-symbol detail (first 40 sym_* entries):")
    for o, k in syms[:40]:
        w = vals[o // 4]
        kind = prologue_kind(w)
        print("  0x%-8X %-46s %08X  %s" % (o, k, w, kind or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
