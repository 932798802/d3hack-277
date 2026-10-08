#!/usr/bin/env python3
"""Rewrite d3hack's offset tables to add a full 2.7.7.92380 table.

IMPORTANT: the runtime lookup does NOT merge tables. exl::reloc::Lookup::Apply()
takes the single table returned by TableSet::Get(version) and applies it to the
mod's own ELF relocations, so **every version table must be complete** -- a
partial table would silently leave the missing symbols unrelocated. That is why
this emits all 449 entries rather than just the changed ones (the comment in
offsets.hpp suggesting "only override entries that change" is misleading).

Region handling (see PORT-FINDINGS.md):
  .text                     -> shift by the reconstructed delta function
  .text/.rodata padding     -> unchanged; 2.7.7's padding covers the same range
  .rodata                   -> per-item; the two items are located by content
  .data / .bss              -> unchanged (layout spot-checked against 2.7.7)

Usage:
    python inject_table.py <src_dir> [--dry-run]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 2.7.7 segment layout (measured)
TEXT_END_277 = 0xC72B90
RODATA_OFF_277 = 0xC73000
B1, B2, B3 = 0x29CBB0, 0x3A73A8, 0x495BC0

# Entries parked in the .text->.rodata padding ("code cave"). 2.7.7's padding
# spans 0xC72B90..0xC73000, which still contains 0xC72F7C..0xC72F88, so these
# keep their addresses.
CAVE = {0xC72F7C, 0xC72F80, 0xC72F84, 0xC72F88}

# .rodata entries resolved individually by searching 2.7.7's rodata:
#   0xE46144 contains "%3.1f FPS"  -> found at 0xE4612B (delta -0x19)
#   0xE6D9E4 is a 21-byte array the mod overwrites; its original content was not
#            identified, so it is left at the 2.7.6 value and flagged as UNVERIFIED.
RODATA_FIX = {
    "data_release_fps_format_rw": 0xE4612B,
}
RODATA_UNVERIFIED = {"data_build_locker_format_rw"}

ENTRY_RE = re.compile(
    r'(\{\s*util::ModuleIndex::Main\s*,\s*)(0x[0-9A-Fa-f]+)(\s*,\s*"([^"]+)"\s*\})'
)


def delta(x):
    if x < B1:
        return 0
    if x < B2:
        return 0x10
    if x < B3:
        return 0x70
    return 0x100


def remap(offset, key):
    """Return (new_offset, status)."""
    if offset in CAVE:
        return offset, "cave"
    if offset < TEXT_END_277:
        return offset + delta(offset), "text"
    if key in RODATA_FIX:
        return RODATA_FIX[key], "rodata-fixed"
    if key in RODATA_UNVERIFIED:
        return offset, "rodata-UNVERIFIED"
    return offset, "data/bss"


def transform(text, stats):
    def sub(m):
        head, off_s, tail, key = m.group(1), m.group(2), m.group(3), m.group(4)
        off = int(off_s, 16)
        new, status = remap(off, key)
        stats[status] = stats.get(status, 0) + 1
        return head + "0x%X" % new + tail
    return ENTRY_RE.sub(sub, text)


def main():
    src = sys.argv[1]
    dry = "--dry-run" in sys.argv
    hpp = os.path.join(src, "source/program/offsets.hpp")
    inl = os.path.join(src, "source/program/offsets_patch_only.inl")
    out_inl = os.path.join(src, "source/program/offsets_patch_only_277.inl")

    hpp_txt = open(hpp, encoding="utf-8").read()
    inl_txt = open(inl, encoding="utf-8").read()

    stats = {}
    new_inl = transform(inl_txt, stats)

    # Extract the DEFAULT block body so it can be re-emitted with shifted offsets.
    start = hpp_txt.index("UserTableType<VersionType::DEFAULT,")
    body_start = hpp_txt.index("\n", start) + 1
    end_marker = "\n        >\n"
    end = hpp_txt.index(end_marker, body_start)
    default_body = hpp_txt[body_start:end]

    body_277 = transform(default_body, stats)
    body_277 = body_277.replace('#include "offsets_patch_only.inl"',
                                '#include "offsets_patch_only_277.inl"')

    banner = (
        "        /* 2.7.7.92380 -- the final retail update.\n"
        "           Offsets are the 2.7.6 ones remapped by the delta function\n"
        "           reconstructed from public multi-version cheat tables plus the\n"
        "           original instruction bytes recorded in d3/patches.cpp.\n"
        "           See d3hack-port/PORT-FINDINGS.md. */\n"
    )
    block_277 = ("        UserTableType<VersionType::V277,\n"
                 + body_277
                 + "\n        >,\n")

    # Insert ',' after the DEFAULT block and append the V277 block.
    new_hpp = (hpp_txt[:end]
               + "\n        >,\n"
               + banner
               + block_277
               + hpp_txt[end + len(end_marker):])

    print("region stats:", stats)
    if dry:
        print("dry run, nothing written")
        return 0

    open(out_inl, "w", encoding="utf-8", newline="\n").write(new_inl)
    open(hpp, "w", encoding="utf-8", newline="\n").write(new_hpp)
    print("wrote %s" % out_inl)
    print("rewrote %s" % hpp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
