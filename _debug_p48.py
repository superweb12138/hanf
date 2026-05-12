import ezdxf, os, math
from collections import defaultdict, Counter

dxf_path = 'D:/hanf/361-RC3210-S-01-BE023_01.dxf'
doc = ezdxf.readfile(dxf_path)
comp = 'BE023'

import weld_extractor as we
part_dims, comp_dims = we.parse_bom(doc, comp)

lbl_non_comp = 'p48'
weld_len_mm = 95.0
BOM_LEN_TOL = 0.08
BOM_WIDTH_TOL = 0.25

pd = part_dims.get(lbl_non_comp)
print(f'Part dims: {pd}')
bw = pd['width']
bl = pd.get('bom_len')
print(f'bw={bw}, bl={bl}, weld_len_mm={weld_len_mm}')

if bw and bw > 0 and weld_len_mm > 0:
    r1 = abs(weld_len_mm - bl) / weld_len_mm
    c1 = r1 < BOM_LEN_TOL
    print(f'Case1: |{weld_len_mm}-{bl}|/95 = {r1:.4f} < {BOM_LEN_TOL} ? {c1}')

    c2a = abs(weld_len_mm - bw) / weld_len_mm < 0.05
    r2b = abs(bl - bw) / max(bw, 1)
    c2b = r2b > 0.3
    c2 = bl and bl > 0 and c2a and c2b
    print(f'Case2a: |95-95|/95 = 0 < 0.05 ? {c2a}')
    print(f'Case2b: |140-95|/95 = {r2b:.4f} > 0.3 ? {c2b}')
    print(f'Case2: {c2}')

    r3 = abs(weld_len_mm - bw) / weld_len_mm
    c3 = r3 < BOM_WIDTH_TOL
    print(f'Case3: |95-95|/95 = 0 < 0.25 ? {c3}')
