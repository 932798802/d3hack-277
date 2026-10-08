import re, struct, os, pathlib
# 仓库根：<repo>/05_Code/tools/audit.py -> parents[2]
REPO = pathlib.Path(__file__).resolve().parents[2]
SRC  = str(REPO / '05_Code' / 'd3hack')
ORIG_O=os.path.join(SRC,'source/program/offsets.hpp.orig')
ORIG_I=os.path.join(SRC,'source/program/offsets_patch_only.inl.orig')
T=(REPO / '10_Other' / 'cache' / 'work' / 'update277' / 'exefs' / 'main.text.bin').read_bytes()
V=struct.unpack_from('<%dI'%(len(T)//4),T,0); N=len(T)//4
def reg_of(w):
    if (w&0xFF800000)==0xD2800000: return 'X%d'%(w&0x1F)
    if (w&0xFF800000)==0xF2800000: return 'X%d'%(w&0x1F)
    if (w&0xFF800000)==0x92800000: return 'X%d'%(w&0x1F)
    if (w&0x7F800000)==0x52800000: return 'W%d'%(w&0x1F)
    if (w&0x7F800000)==0x72800000: return 'W%d'%(w&0x1F)
    if (w&0x7F800000)==0x12800000: return 'W%d'%(w&0x1F)
    if (w&0xFFE00000)==0xAA000000 and (w>>16)&0x1F==31: return 'X%d'%(w&0x1F)
    if (w&0x7FE00000)==0x2A000000 and (w>>16)&0x1F==31: return 'W%d'%(w&0x1F)
    if (w&0xFF000000)==0x53000000: return 'W%d'%(w&0x1F)
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
    return None
def isbranch(w):
    return (w&0xFC000000) in (0x14000000,0x94000000) or (w&0xFF000010)==0x54000000 \
        or (w&0x7F000000) in (0x34000000,0x35000000,0x36000000,0x37000000)
def isframe(w):
    return (w&0xFFC003FF)==0xD10003FF or (w&0xFFC003E0)==0xA98003E0 \
        or ((w&0xFFE00000)==0xF8000000 and ((w>>5)&0x1F)==31) or w in (0xD503233F,0xD503237F)
def isadrp(w): return (w&0x9F000000)==0x90000000
def pair_ok(w2,base,r):
    if (w2&0x9F000000)==0x90000000:  # two adrp in a row = the pair was NOT a pair
        return False
    if (w2&0xFF800000)==0x91000000: return (w2&0x1F)==r and ((w2>>5)&0x1F)==r
    if (w2&0xFFC00000) in (0xF9400000,0xB9400000,0xF9000000,0xB9000000): return (w2&0x1F)==r and ((w2>>5)&0x1F)==r
    return False
def isldr_x8_50(w): return w==0xF9402908
def isldr_same_shape(w,wnew):
    # wnew is an LDR Xd,[Xn,#imm]; require current to be an LDR with same d/n
    if (wnew&0xFFC00000)==0xF9400000:
        return (w&0xFFC00000)==0xF9400000 and (w&0x1F)==(wnew&0x1F) and ((w>>5)&0x1F)==((wnew>>5)&0x1F)
    return None
# ---- gather original 2.7.6 addresses (patch table only) ----
orig={}
for f in (ORIG_O,ORIG_I):
    t=open(f,encoding='utf-8').read()
    for m in re.finditer(r'\{\s*util::ModuleIndex::Main\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"([^"]+)"',t):
        orig.setdefault(m.group(2),int(m.group(1),16))
pc=open(os.path.join(SRC,'source/program/d3/patches.cpp'),encoding='utf-8').read()
site={}
for m in re.finditer(r'jest\.Patch<\s*(ins::\w+)\s*>\s*\(\s*PatchTable\("([^"]+)"\)\s*(?:,\s*(reg::\w+))?',pc):
    site.setdefault(m.group(2),(m.group(1).split('::')[1],(m.group(3) or '').replace('reg::','')))
for m in re.finditer(r'MakeAdrlPatch\(\s*PatchTable\("([^"]+)"\)',pc): site.setdefault(m.group(1),('Adrp',''))
for m in re.finditer(r'jest\.Patch<dword>\(\s*PatchTable\("([^"]+)"\)',pc): site.setdefault(m.group(1),('Bytes',''))
CANDS=(0,0x10,0x70,0x100)
CUR={'patch_hideonline_04_movz':0x10,'patch_hideonline_05_movz':0x10,'patch_hideonline_06_bytes':0x10,
     'patch_hideonline_07_movz':0x10,'patch_autosave_string_01_adrl':0x10}
print('%-40s %-6s %-5s %-8s %s'%('key','type','reg','model','各候选 delta 的判定'))
fix=[];skip=[];oky=[]
for key,(typ,reg) in sorted(site.items()):
    o=orig.get(key)
    if o is None: continue
    verdicts={}
    for d in CANDS:
        a=o+d
        if a%4 or a+8>len(T): verdicts[d]='-'; continue
        w=V[a//4]; w2=V[a//4+1]
        if typ=='Adrp':
            verdicts[d]='STRONG' if (isadrp(w) and pair_ok(w2,a,reg_of(w) and int(reg_of(w)[1:]) if reg_of(w) else -1)) else ('weak' if isadrp(w) else 'fail')
        elif typ=='Ret':
            verdicts[d]='STRONG' if isframe(w) else 'fail'
        elif typ in ('Movz','Movk','Movn'):
            r=reg_of(w)
            if r and reg and r==reg: verdicts[d]='STRONG'
            elif isframe(w) and 0==(w&0x1F): verdicts[d]='STRONG'
            elif isbranch(w): verdicts[d]='weak'
            else: verdicts[d]='fail'
        elif typ=='Bytes':
            shape=isldr_same_shape(w,0xF9402908)
            verdicts[d]='STRONG' if shape else 'fail'
        else: verdicts[d]='?'
    model=CUR.get(key,None)
    # decide the delta actually used by the injected table: derive from current file
    cur=None
    for f in ('offsets.hpp','offsets_patch_only.inl'):
        t=open(os.path.join(SRC,'source/program',f),encoding='utf-8').read()
        m=re.search(r'\{\s*util::ModuleIndex::Main\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*"'+re.escape(key)+r'"',t)
        if m: cur=int(m.group(1),16)-o; break
    best=[d for d in CANDS if verdicts.get(d)=='STRONG']
    tag=''
    if cur in best: tag='OK'
    elif best: tag='*FIX* -> +0x%X'%best[0]; fix.append((key,typ,reg,o,cur,best[0]))
    elif any(verdicts.get(d)=='weak' for d in CANDS): tag='weak-only (keep)'
    else: tag='?? UNRESOLVED'; skip.append((key,typ,reg,o,cur))
    if tag!='OK': print('%-40s %-6s %-5s +0x%-5X %s (%s)'%(key,typ,reg,cur,tag,verdicts))
print()
print('=== 需改址 %d 条 ==='%len(fix))
for k,t,r,o,c,b in fix: print('  %-40s 当前+0x%-5X 建议+0x%-5X  (2.7.6=0x%X -> 0x%X)'%(k,c,b,o,o+b))
print('=== 无法判定 %d 条 ==='%len(skip))
for k,t,r,o,c in skip: print('  %-40s type=%-6s reg=%-4s 2.7.6=0x%-8X 当前+0x%X'%(k,t,r,o,c))
