#pragma once

/* Target game build.
 *
 * This tree is pinned to the FINAL retail update, 2.7.7.92380 (2024-01-09).
 * The offset table (source/program/offsets.hpp) and the build guard in
 * main.cpp are both fixed to this build; the upstream 2.7.6.90885 support was
 * dropped when the offsets were remapped. See d3hack-port/PORT-FINDINGS.md for
 * how the 2.7.6 -> 2.7.7 delta function was reconstructed.
 *
 * Measured layout of this build (main module):
 *   .text    0x000000 .. 0xC72B90
 *   .rodata  0xC73000 .. 0x10979C4   (base identical to 2.7.6)
 *   .data    0x1098000 .. 0x115CA14  (layout unchanged from 2.7.6)
 *   .bss     .. 0x1A7BFE0 total
 */
#define D3CLIENT_VER "2.7.7.92380"

/* Kept for reference / diffing against upstream. */
#define D3CLIENT_VER_276 "2.7.6.90885"
#define D3CLIENT_VER_277 "2.7.7.92380"
