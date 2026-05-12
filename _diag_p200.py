"""Diagnostic: examine p200 3-SIDES geometry in BE022 and BE023."""
import ezdxf, math, re
from collections import defaultdict

SCALE = 10.0
SNAP_TOL = 1.5

def dist2d(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def dist_pt_to_seg(pt, s, e):
    dx, dy = e[0]-s[0], e[1]-s[1]
    len_sq = dx*dx + dy*dy
    if len_sq < 1e-12:
        return dist2d(pt, s), 0.0
    t = max(0.0, min(1.0, ((pt[0]-s[0])*dx + (pt[1]-s[1])*dy) / len_sq))
    proj = (s[0]+t*dx, s[1]+t*dy)
    return dist2d(pt, proj), t

def get_part_lines(blk):
    lines = []
    for e in blk:
        if e.dxftype() == 'LINE':
            s = (e.dxf.start.x, e.dxf.start.y)
            ep = (e.dxf.end.x, e.dxf.end.y)
            ln = dist2d(s, ep)
            if ln > 0.5:
                lines.append({'start': s, 'end': ep, 'length': ln})
    return lines


def analyze_3sides_view(dxf_path, comp, target_views):
    doc = ezdxf.readfile(dxf_path)
    
    for view_id in target_views:
        print(f"\n=== View {view_id} ===")
        parts = {}
        for blk in doc.blocks:
            m = re.search(r' - (\d+)$', blk.name)
            if not m or m.group(1) != view_id:
                continue
            if blk.name.startswith('Part'):
                lines = get_part_lines(blk)
                parts[blk.name] = lines
                print(f"  {blk.name}:")
                for ln in lines:
                    length_mm = round(ln['length'] * SCALE, 1)
                    s = ln['start']
                    e = ln['end']
                    dx = abs(e[0] - s[0])
                    dy = abs(e[1] - s[1])
                    orient = 'H' if dx > dy else 'V'
                    print(f"    {orient} len={length_mm}mm  s=({s[0]:.2f},{s[1]:.2f})  e=({e[0]:.2f},{e[1]:.2f})")


# BE022 - p200 appears in views 5343 and 5608
print("=" * 60)
print("BE022 - p200 views")
print("=" * 60)
analyze_3sides_view(
    '361-RC3210-S-01-BE022_01.dxf', 'BE022',
    ['5343', '5608']
)

# BE023 - p200 appears in views 4826 and 2407
print()
print("=" * 60)
print("BE023 - p200 views")
print("=" * 60)
analyze_3sides_view(
    '361-RC3210-S-01-BE023_01.dxf', 'BE023',
    ['4826', '2407']
)

# BE022 - p26 view 2304
print()
print("=" * 60)
print("BE022 - p26 view")
print("=" * 60)
analyze_3sides_view(
    '361-RC3210-S-01-BE022_01.dxf', 'BE022',
    ['2304']
)

# BE023 - p48 view 2361
print()
print("=" * 60)
print("BE023 - p48 view")
print("=" * 60)
analyze_3sides_view(
    '361-RC3210-S-01-BE023_01.dxf', 'BE023',
    ['2361']
)
