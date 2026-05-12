"""Trace p200 3-SIDES edge enumeration in BE022 and BE023."""
import ezdxf, math, re
from collections import defaultdict, Counter

SCALE = 10.0
SNAP_TOL = 1.5
ADJ_TOL = SNAP_TOL + 0.5
MIN_EDGE = 1.5

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

def _merge_collinear_edges(edges_with_lines, adj_tol):
    if len(edges_with_lines) <= 1:
        return [(e, op) for e, op, _ in edges_with_lines]
    groups = defaultdict(list)
    for ln_len, op, g_ln in edges_with_lines:
        groups[op].append((ln_len, g_ln))
    merged = []
    for op, items in groups.items():
        if len(items) == 1:
            merged.append((items[0][0], op))
            continue
        n = len(items)
        parent = list(range(n))
        def _find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def _union(a, b):
            parent[_find(a)] = _find(b)
        for i in range(n):
            li = items[i][1]
            for j in range(i + 1, n):
                lj = items[j][1]
                if (dist2d(li['start'], lj['start']) < adj_tol or
                    dist2d(li['start'], lj['end'])   < adj_tol or
                    dist2d(li['end'],   lj['start']) < adj_tol or
                    dist2d(li['end'],   lj['end'])   < adj_tol):
                    dx1 = li['end'][0] - li['start'][0]
                    dy1 = li['end'][1] - li['start'][1]
                    dx2 = lj['end'][0] - lj['start'][0]
                    dy2 = lj['end'][1] - lj['start'][1]
                    len1 = math.hypot(dx1, dy1)
                    len2 = math.hypot(dx2, dy2)
                    if len1 > 1e-9 and len2 > 1e-9:
                        cos_a = abs(dx1 * dx2 + dy1 * dy2) / (len1 * len2)
                        if cos_a > 0.985:
                            _union(i, j)
        comps = defaultdict(list)
        for i in range(n):
            comps[_find(i)].append(items[i])
        for comp_items in comps.values():
            total_len = sum(it[0] for it in comp_items)
            merged.append((total_len, op))
    return merged


def trace_3sides(dxf_path, comp, gusset_part_suffix, view_id):
    doc = ezdxf.readfile(dxf_path)
    
    view_parts = {}
    part_labels = {}
    for blk in doc.blocks:
        m = re.search(r' - (\d+)$', blk.name)
        if not m or m.group(1) != view_id:
            continue
        if blk.name.startswith('Part'):
            view_parts[blk.name] = get_part_lines(blk)

    print(f"\nView {view_id} parts:")
    for pname, lines in view_parts.items():
        total_lines = len(lines)
        print(f"  {pname}: {total_lines} lines")
    
    # Find gusset (the part matching suffix)
    gusset_name = None
    for pname in view_parts:
        if gusset_part_suffix in pname:
            gusset_name = pname
            break
    
    if not gusset_name:
        print(f"  ERROR: gusset part '{gusset_part_suffix}' not found!")
        return
    
    print(f"\nGusset: {gusset_name}")
    print(f"Gusset lines:")
    for ln in view_parts[gusset_name]:
        length_mm = round(ln['length'] * SCALE, 1)
        print(f"  len={length_mm}mm  s=({ln['start'][0]:.2f},{ln['start'][1]:.2f})  e=({ln['end'][0]:.2f},{ln['end'][1]:.2f})")
    
    # Find adjacent edges
    gusset_blk_set = {gusset_name}
    edges = []
    for g_ln in view_parts[gusset_name]:
        if g_ln['length'] < MIN_EDGE:
            continue
        p_s = None; pd_s = ADJ_TOL
        p_e = None; pd_e = ADJ_TOL
        for pname, plines in view_parts.items():
            if pname in gusset_blk_set:
                continue
            for ln in plines:
                d1, _ = dist_pt_to_seg(g_ln['start'], ln['start'], ln['end'])
                d2, _ = dist_pt_to_seg(g_ln['end'],   ln['start'], ln['end'])
                if d1 < pd_s: pd_s = d1; p_s = pname
                if d2 < pd_e: pd_e = d2; p_e = pname
        geo_mm = round(g_ln['length'] * SCALE, 1)
        if p_s and p_e:
            if p_s == p_e:
                edges.append((g_ln['length'], p_s, g_ln))
                print(f"  EDGE: {geo_mm}mm -> {p_s} (both ends)")
            else:
                print(f"  EDGE: {geo_mm}mm -> start={p_s} end={p_e} (diff parts, skip)")
        elif p_s:
            edges.append((g_ln['length'], p_s, g_ln))
            print(f"  EDGE: {geo_mm}mm -> {p_s} (start only)")
        elif p_e:
            edges.append((g_ln['length'], p_e, g_ln))
            print(f"  EDGE: {geo_mm}mm -> {p_e} (end only)")
        else:
            print(f"  NO-ADJ: {geo_mm}mm")
    
    print(f"\nPre-merge edges ({len(edges)}):")
    for e, op, g in edges:
        print(f"  {round(e * SCALE, 1)}mm -> {op}")
    
    if len(edges) > 1:
        merged = _merge_collinear_edges(edges, ADJ_TOL)
        print(f"\nPost-merge edges ({len(merged)}):")
        for e, op in merged:
            print(f"  {round(e * SCALE, 1)}mm -> {op}")
    else:
        merged = [(e, op) for e, op, _ in edges]
    
    # Show BOM mapping attempt
    print(f"\nExpected output: edges mapped to BOM dimensions")


# BE022 - p200 view 5343
print("=" * 60)
print("BE022 / p200 - View 5343")
print("=" * 60)
# In view 5343: p200 = Part-251777343-5351, BE022 = Part-251777343-5352
trace_3sides('361-RC3210-S-01-BE022_01.dxf', 'BE022', '5351', '5343')

# BE022 - p200 view 5608
print()
print("=" * 60)
print("BE022 / p200 - View 5608")
print("=" * 60)
trace_3sides('361-RC3210-S-01-BE022_01.dxf', 'BE022', '5615', '5608')

# BE023 - p200 view 4826
print()
print("=" * 60)
print("BE023 / p200 - View 4826")
print("=" * 60)
trace_3sides('361-RC3210-S-01-BE023_01.dxf', 'BE023', '4831', '4826')
