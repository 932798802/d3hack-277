"""Cross-check every patch site in the (already shifted) mod source against the
2.7.7 binary: does the instruction actually sitting at the mapped address write
the same destination register the patcher assumes?"""
import re, struct, sys, os, pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC  = str(REPO / '05_Code' / 'd3hack')
TEXT = str(REPO / '10_Other' / 'cache' / 'work' / 'update277' / 'exefs' / 'main.text.bin')

text = open(TEXT, 'rb').read(); N = len(text) // 4
V = struct.unpack_from('<%dI' % N, text, 0)

# ---- 1. name -> offset from the shifted tables -------------------------------
off_of = {}
for f in ('source/program/offsets.hpp', 'source/program/offsets_patch_only.inl'):
    t = open(os.path.join(SRC, f), encoding='utf-8').read()
    for m in re.finditer(r'\{\s*util::ModuleIndex::Main\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"', t):
        off_of[m.group(2)] = int(m.group(1), 16)

def dst(w):
    if (w & 0x7F800000) == 0x52800000 or (w & 0x7F800000) == 0x72800000 or (w & 0x7F800000) == 0x12800000:
        return ('W%d' % (w & 0x1F))
    if (w & 0xFF800000) == 0xD2800000 or (w & 0xFF800000) == 0xF2800000 or (w & 0xFF800000) == 0x92800000:
        return ('X%d' % (w & 0x1F))
    if (w & 0x7FE0FFE0) == 0x2A0003E0:      # ORR Rd, WZR, Rm  == MOV Wd, Wm
        return ('W%d' % (w & 0x1F))
    if (w & 0xFFE0FFE0) == 0xAA0003E0:      # MOV Xd, Xm
        return ('X%d' % (w & 0x1F))
    if (w & 0xFFC00000) == 0xF9400000: return 'X%d' % (w & 0x1F)   # LDR X
    if (w & 0xFFC00000) == 0xB9400000: return 'W%d' % (w & 0x1F)   # LDR W
    if (w & 0xFFC00000) == 0x39400000: return 'W%d' % (w & 0x1F)   # LDRB W
    if (w & 0xFFC00000) == 0x79400000: return 'W%d' % (w & 0x1F)   # LDRH W
    if (w & 0x7F800000) == 0x12000000: return 'W%d' % (w & 0x1F)   # AND imm
    if (w & 0x7F800000) == 0x32000000: return 'W%d' % (w & 0x1F)   # ORR imm
    if (w & 0xFF800000) == 0x91000000: return 'X%d' % (w & 0x1F)   # ADD imm
    if (w & 0xFF800000) == 0xD1000000: return 'X%d' % (w & 0x1F)   # SUB imm
    if (w & 0xFF800000) == 0x11000000: return 'W%d' % (w & 0x1F)   # ADD imm 32
    if (w & 0xFF800000) == 0x51000000: return 'W%d' % (w & 0x1F)   # SUB imm 32
    if (w & 0x9F000000) == 0x90000000: return 'X%d' % (w & 0x1F)   # ADRP
    if (w & 0x9F000000) == 0x10000000: return 'X%d' % (w & 0x1F)   # ADR
    if (w & 0x7FE00000) in (0x1A000000,) and (w & 0x1F) != 31: return None
    if (w & 0x7FE00000) == 0x1A800000: return 'W%d' % (w & 0x1F)   # CSEL/CSINC family
    if (w & 0x7FE00000) == 0x5A800000: return 'W%d' % (w & 0x1F)   # CSET/CSINC 32
    if (w & 0xFFE00000) == 0x9A800000: return 'X%d' % (w & 0x1F)
    if (w & 0xFFE00000) == 0xDA800000: return 'X%d' % (w & 0x1F)
    if (w & 0xFFC00000) == 0x39000000: return 'W%d' % (w & 0x1F)   # STRB
    if (w & 0xFFC00000) == 0xB9000000: return 'W%d' % (w & 0x1F)   # STR W
    if (w & 0xFFC00000) == 0xF9000000: return 'X%d' % (w & 0x1F)   # STR X
    return None

def kind(w):
    if (w & 0xFC000000) == 0x14000000: return 'B'
    if (w & 0xFC000000) == 0x94000000: return 'BL'
    if (w & 0xFF000010) == 0x54000000: return 'B.cond'
    if (w & 0x7F000000) in (0x34000000, 0x35000000): return 'CBZ/CBNZ'
    if (w & 0x7F000000) in (0x36000000, 0x37000000): return 'TBZ/TBNZ'
    if (w & 0xFFFFFC1F) == 0xD65F0000: return 'RET'
    if w == 0xD503201F: return 'NOP'
    return None

# ---- 2. patch sites + expected register from patches.cpp --------------------
pc = open(os.path.join(SRC, 'source/program/d3/patches.cpp'), encoding='utf-8').read()
rows = []
for m in re.finditer(r'jest\.Patch<\s*(ins::\w+)\s*>\s*\(\s*PatchTable\("([^"]+)"\)\s*(?:,\s*(reg::\w+))?', pc):
    rows.append((m.group(1).split('::')[1], m.group(2), m.group(3)))
for m in re.finditer(r'MakeAdrlPatch\(\s*PatchTable\("([^"]+)"\)', pc):
    rows.append(('Adrp', m.group(1), None))
for m in re.finditer(r'jest\.Patch<dword>\(\s*PatchTable\("([^"]+)"\)', pc):
    rows.append(('Bytes', m.group(1), None))

bad = 0; okc = 0
print('%-40s %-9s %-8s %-18s %-24s %s' % ('key', 'type', 'reg', 'addr_277', 'insn@277', 'verdict'))
for typ, key, reg in rows:
    if key not in off_of:
        print('%-40s %-9s %-8s %s' % (key, typ, reg or '-', '** NOT IN TABLE **')); bad += 1; continue
    a = off_of[key]
    if a % 4 or a + 4 > len(text):
        print('%-40s %-9s %-8s 0x%-8X %s' % (key, typ, reg or '-', a, '** OUT OF RANGE **')); bad += 1; continue
    w = V[a // 4]
    d = dst(w); k = kind(w)
    exp = (reg or '').replace('reg::', '')
    verdict = ''
    if typ in ('Movz', 'Movk', 'Movn'):
        if d is None and k in ('B', 'BL', 'B.cond', 'CBZ/CBNZ', 'TBZ/TBNZ'):
            verdict = 'default-value overwrite (branch) OK'
        elif d is not None and (d == exp or d[0] == exp[0] and d[1:] == exp[1:]):
            verdict = 'OK (same dst)'
        else:
            verdict = '*** MISMATCH ***'; bad += 1
    elif typ == 'Nop':
        verdict = 'OK' if k else '*** NOT A BRANCH ***'; bad += (0 if k else 1)
    elif typ == 'Ret':
        verdict = 'OK' if (w & 0xFFC003FF) == 0xD10003FF or (w & 0xFFC003E0) == 0xA98003E0 or (w & 0xFFE00000) == 0xF8000000 else '*** NOT A PROLOGUE ***'
        bad += (0 if verdict == 'OK' else 1)
    elif typ == 'Adrp':
        verdict = 'OK' if (w & 0x9F000000) == 0x90000000 else '*** NOT ADRP ***'; bad += (0 if verdict == 'OK' else 1)
    else:
        verdict = '(bytes patch, manual)'
    if verdict.startswith('  ') or '***' in verdict:
        print('%-40s %-9s %-8s 0x%-8X 0x%08X %s' % (key, typ, reg or '-', a, w, verdict))
    else:
        okc += 1
print()
print('checked %d sites: %d clean, %d flagged' % (len(rows), okc, bad))
