#!/usr/bin/env python3
"""Probe how far the 2.7.6.90885 code layout moved in 2.7.7.92380.

Builds one flat module image from the decompressed NSO segments
(text @0, rodata @dst_off, data @dst_off) and then:

  1. locates the build-version strings, giving a hard anchor delta between the
     two builds (d3hack hardcodes rodata offset 0x0E45863 for "C2.7.6.90885");
  2. reports the 4 bytes sitting at every offset d3hack hardcodes for 2.7.6, so
     drift can be measured rather than guessed.

Usage:
    python probe_drift.py <exefs_dir>
"""
import os
import struct
import sys

SEGS = ("text", "rodata", "data")
D3_276_VER_STR_OFF = 0x0E45863          # rodata, per main.cpp kBuildVersionFullOffset


def load_image(exefs_dir):
    """Return (image: bytes, seg_bounds: {name: (start, size)})."""
    info = []
    for name in SEGS:
        p = os.path.join(exefs_dir, "main.%s.bin" % name)
        data = open(p, "rb").read()
        info.append((name, data))
    nso = open(os.path.join(exefs_dir, "main"), "rb").read() if \
        os.path.exists(os.path.join(exefs_dir, "main")) else None
    # dst_off comes from the NSO header; re-derive it from the raw `main`.
    main_nso = os.path.join(exefs_dir, "main")
    segs = None
    if os.path.exists(main_nso):
        blob = open(main_nso, "rb").read()
        segs = [struct.unpack_from("<IIII", blob, 0x10 + i * 0x10) for i in range(3)]
    total = 0
    bounds = {}
    for i, (name, data) in enumerate(info):
        do = segs[i][1] if segs else total
        bounds[name] = (do, len(data))
        total = max(total, do + len(data))
    img = bytearray(total)
    for i, (name, data) in enumerate(info):
        do = bounds[name][0]
        img[do:do + len(data)] = data
    return bytes(img), bounds


def main():
    exefs = sys.argv[1]
    img, bounds = load_image(exefs)
    print("module image: %d bytes (0x%X)" % (len(img), len(img)))
    for name in SEGS:
        do, sz = bounds[name]
        print("  %-7s dst_off=0x%-9X size=%-10d ends 0x%X"
              % (name, do, sz, do + sz))

    print("\n=== build version strings ===")
    for needle in (b"2.7.7.92380", b"2.7.6.90885", b"C2.7.7", b"C2.7.6"):
        hits = []
        start = 0
        while True:
            p = img.find(needle, start)
            if p < 0:
                break
            hits.append(p)
            start = p + 1
            if len(hits) > 8:
                break
        print("  %-12r hits=%d %s" % (needle, len(hits),
                                      ["0x%X" % h for h in hits[:8]]))
        if needle == b"2.7.7.92380" and hits:
            for h in hits[:4]:
                ctx = img[max(0, h - 24):h + 32]
                print("      @0x%-9X ctx=%r" % (h, ctx))

    print("\n=== d3hack 2.7.6 anchors: what sits at those offsets in 2.7.7 ===")
    anchors = [
        (0x0E45863, "kBuildVersionFullOffset ('C'+ver string)"),
        (0x000480, "sym_main_init"),
        (0x298BD0, "sym_gfx_init"),
        (0x667830, "sym_shell_initialize"),
        (0x7B08A0, "sym_sgame_initialize"),
        (0x4CABA0, "sym_game_common_data_init"),
        (0x185F70, "sym_challenge_rift_callback"),
        (0x0BB5E8, "sym_floating_dmg"),
        (0xA2AC70, "sym_print_error"),
        (0x17DE610, "main_rwindow (global)"),
        (0x1830F68, "gfx_internal_data_ptr (global)"),
        (0x1905610, "app_globals (global)"),
    ]
    for off, label in anchors:
        if off + 4 > len(img):
            print("  %-11s 0x%-9X  <out of image>" % ("", off))
            continue
        b = img[off:off + 4]
        w = struct.unpack("<I", b)[0]
        if True:  # printable preview
            ctx = img[off:off + 16]
            s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        print("  %-11s 0x%-9X  %s  %s" % ("", off, b.hex(' '), s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
