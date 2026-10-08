import re, struct, os, pathlib
REPO = pathlib.Path(__file__).resolve().parents[2]
SRC  = str(REPO / '05_Code' / 'd3hack')
text = (REPO / '10_Other' / 'cache' / 'work' / 'update277' / 'exefs' / 'main.text.bin').read_bytes()
N=len(text)//4; V=struct.unpack_from('<%dI'%N,text,0)
off_of={}
for f in ('source/program/offsets.hpp','source/program/offsets_patch_only.inl'):
    t=open(os.path.join(SRC,f),encoding='utf-8').read()
    for m in re.finditer(r'\{\s*util::ModuleIndex::Main\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"',t):
        off_of[m.group(2)]=int(m.group(1),16)
def dst(w):
    if (w&0xFF800000)==0xD2800000: return 'X%d'%(w&0x1F)     # MOVZ 64
    if (w&0xFF800000)==0xF2800000: return 'X%d'%(w&0x1F)     # MOVK 64
    if (w&0xFF800000)==0x92800000: return 'X%d'%(w&0x1F)     # MOVN 64
    if (w&0xFF800000)==0xD2400000: return 'X%d'%(w&0x1F)     # MOVZ 64 (top-bit forms)
    if (w&0x7F800000)==0x52800000: return 'W%d'%(w&0x1F)
    if (w&0x7F800000)==0x72800000: return 'W%d'%(w&0x1F)
    if (w&0x7F800000)==0x12800000: return 'W%d'%(w&0x1F)
    if (w&0xFFE00000)==0xAA000000 and (w>>16)&0x1F==31: return 'X%d'%(w&0x1F)   # MOV Xd,Xm
    if (w&0x7FE00000)==0x2A000000 and (w>>16)&0x1F==31: return 'W%d'%(w&0x1F)   # MOV Wd,Wm
    if (w&0xFF000000)==0x53000000: return 'W%d'%(w&0x1F)     # logical imm
    if (w&0xFF000000)==0x12000000: return 'W%d'%(w&0x1F)
    if (w&0xFF000000)==0x32000000: return 'W%d'%(w&0x1F)
    if (w&0xFF000000)==0x92000000: return 'X%d'%(w&0x1F)
    if (w&0xFF000000)==0xB2000000: return 'X%d'%(w&0x1F)
    if (w&0xFFC00000)==0xF9400000: return 'X%d'%(w&0x1F)
    if (w&0xFFC00000)==0xB9400000: return 'W%d'%(w&0x1F)
    if (w&0xFFC00000)==0x39400000: return 'W%d'%(w&0x1F)
    if (w&0xFFC00000)==0x79400000: return 'W%d'%(w&0x1F)
    if (w&0xFF800000)==0x91000000: return 'X%d'%(w&0x1F)
    if (w&0xFF800000)==0xD1000000: return 'X%d'%(w&0x1F)
    if (w&0xFF800000)==0x11000000: return 'W%d'%(w&0x1F)
    if (w&0xFF800000)==0x51000000: return 'W%d'%(w&0x1F)
    if (w&0x9F000000)==0x90000000: return 'X%d'%(w&0x1F)
    if (w&0x9F000000)==0x10000000: return 'X%d'%(w&0x1F)
    if (w&0x7FE0F800) in (0x1A800000,): return 'W%d'%(w&0x1F)
    if (w&0xFFE0F800)==0x9A800000: return 'X%d'%(w&0x1F)
    if (w&0xFFC00000)==0x39000000: return 'W%d'%(w&0x1F)
    if (w&0xFFC00000)==0xB9000000: return 'W%d'%(w&0x1F)
    if (w&0xFFC00000)==0xF9000000: return 'X%d'%(w&0x1F)
    return None
def branchish(w):
    if (w&0xFC000000)==0x14000000: return 'B'
    if (w&0xFC000000)==0x94000000: return 'BL'
    if (w&0xFF000010)==0x54000000: return 'B.cond'
    if (w&0x7F000000) in (0x34000000,0x35000000): return 'CBZ'
    if (w&0x7F000000) in (0x36000000,0x37000000): return 'TBZ'
    if (w&0xFFFFFC1F)==0xD65F0000: return 'RET'
    return None
pc=open(os.path.join(SRC,'source/program/d3/patches.cpp'),encoding='utf-8').read()
rows=[]
for m in re.finditer(r'jest\.Patch<\s*(ins::\w+)\s*>\s*\(\s*PatchTable\("([^"]+)"\)\s*(?:,\s*(reg::\w+))?',pc):
    rows.append((m.group(1).split('::')[1],m.group(2),(m.group(3) or '').replace('reg::','')))
for m in re.finditer(r'MakeAdrlPatch\(\s*PatchTable\("([^"]+)"\)',pc): rows.append(('Adrp',m.group(1),''))
seen=set(); out=[]
for typ,key,reg in rows:
    if (typ,key) in seen: continue
    seen.add((typ,key))
    a=off_of.get(key)
    if a is None or a%4 or a+4>len(text):
        out.append((key,typ,reg,a,'-','NOT IN TEXT')); continue
    w=V[a//4]; d=dst(w); b=branchish(w)
    if typ in ('Movz','Movk','Movn'):
        if d and d==reg: v='ok'
        elif d and d[0]==reg[0] and d[1:]==reg[1:]: v='ok'
        elif b: v='ok(branch->value)'
        elif d is None: v='?no-dst'
        else: v='** REG %s != %s **'%(d,reg)
    elif typ=='Nop':
        v='ok' if b else ('nop-over-data' if d else '?')
    elif typ=='Ret':
        v='ok' if (w&0xFFC003FF)==0xD10003FF or (w&0xFFC003E0)==0xA98003E0 or (w&0xFFE00000)==0xF8000000 else 'ret-over-nonprologue'
    elif typ=='Adrp':
        v='ok' if (w&0x9F000000)==0x90000000 else '** NOT ADRP **'
    else: v='bytes'
    out.append((key,typ,reg,a,'0x%08X'%w,v))
print('=== 需要人工确认的 ===')
for key,typ,reg,a,w,v in out:
    if v not in ('ok','ok(branch->value)','bytes'): print('%-38s %-6s %-5s @%-9s %s  %s'%(key,typ,reg,('0x%X'%a) if a else '-',w,v))
print()
from collections import Counter
print(Counter(v for *_ ,v in out))
