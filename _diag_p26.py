"""Trace the WeldMark arrow matching for BE022/p26 and BE023/p48."""
import ezdxf, math, re
from collections import defaultdict, Counter

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

def parse_weldmark(blk):
    lines_raw = []
    texts = []
    for e in blk:
        t = e.dxftype()
        if t == 'LINE':
            s  = (round(e.dxf.start.x, 4), round(e.dxf.start.y, 4))
            ep = (round(e.dxf.end.x,   4), round(e.dxf.end.y,   4))
            ln = dist2d(s, ep)
            if ln > 0.01:
                lines_raw.append((s, ep, ln))
        elif t == 'TEXT':
            try:
                txt = e.dxf.text.strip()
                pos = (e.dxf.insert.x, e.dxf.insert.y)
                if txt:
                    texts.append((txt, pos))
            except:
                pass
        elif t == 'MTEXT':
            try:
                txt = e.text.strip()
                pos = (e.dxf.insert.x, e.dxf.insert.y)
                if txt:
                    texts.append((txt, pos))
            except:
                pass
    if not lines_raw:
        return None
    ep_count = Counter()
    for s, ep, _ in lines_raw:
        ep_count[s]  += 1
        ep_count[ep] += 1
    dangling = {pt for pt, c in ep_count.items() if c == 1}
    horiz = [(s, ep, ln) for s, ep, ln in lines_raw
             if abs(s[1]-ep[1]) < 0.05*ln and ln > 3]
    if not horiz:
        return None
    ref_s, ref_e, _ = max(horiz, key=lambda x: x[2])
    ref_y = (ref_s[1] + ref_e[1]) / 2.0
    candidates = [pt for pt in dangling if abs(pt[1] - ref_y) > 0.5]
    if not candidates:
        return None
    arrow_tip = max(candidates, key=lambda pt: abs(pt[1] - ref_y))
    return {
        'arrow_tip': arrow_tip,
        'texts': texts,
    }

def find_parts_at_point(arrow_tip, view_part_lines, tol):
    matches = []
    for part_name, lines in view_part_lines.items():
        best_ep  = None
        best_int = None
        for ln in lines:
            d_start = dist2d(arrow_tip, ln['start'])
            d_end   = dist2d(arrow_tip, ln['end'])
            ep_d    = min(d_start, d_end)
            if ep_d <= tol:
                if best_ep is None or ep_d < best_ep[1]:
                    best_ep = (ln, ep_d)
            else:
                d_int, _ = dist_pt_to_seg(arrow_tip, ln['start'], ln['end'])
                if d_int <= tol:
                    if best_int is None or ln['length'] < best_int[0]['length']:
                        best_int = (ln, d_int)
        if best_ep is not None:
            matches.append({'part': part_name, 'how': 'endpoint',
                            'line': best_ep[0],  'ep_dist': best_ep[1]})
        elif best_int is not None:
            matches.append({'part': part_name, 'how': 'interior',
                            'line': best_int[0], 'int_dist': best_int[1]})
    return matches


# BE022 - WeldMark for p26 in view 2304
print("=" * 60)
print("BE022 / p26 - View 2304")
print("=" * 60)
doc = ezdxf.readfile('361-RC3210-S-01-BE022_01.dxf')
view_parts = {}
for blk in doc.blocks:
    m = re.search(r' - (\d+)$', blk.name)
    if not m or m.group(1) != '2304':
        continue
    if blk.name.startswith('Part'):
        view_parts[blk.name] = get_part_lines(blk)
    elif blk.name.startswith('WeldMark'):
        wm = parse_weldmark(blk)
        if wm:
            print(f"WM: {blk.name}")
            print(f"  arrow_tip = {wm['arrow_tip']}")
            print(f"  texts = {wm['texts']}")
            matches = find_parts_at_point(wm['arrow_tip'], view_parts, SNAP_TOL)
            print(f"  matches ({len(matches)}):")
            for m2 in matches:
                length_mm = round(m2['line']['length'] * SCALE, 1)
                print(f"    {m2['part']}: {m2['how']} line_len={length_mm}mm "
                      f"s={tuple(round(c,2) for c in m2['line']['start'])} "
                      f"e={tuple(round(c,2) for c in m2['line']['end'])}")

# BE023 - WeldMark for p48 in view 2361
print()
print("=" * 60)
print("BE023 / p48 - View 2361")
print("=" * 60)
doc2 = ezdxf.readfile('361-RC3210-S-01-BE023_01.dxf')
view_parts2 = {}
for blk in doc2.blocks:
    m = re.search(r' - (\d+)$', blk.name)
    if not m or m.group(1) != '2361':
        continue
    if blk.name.startswith('Part'):
        view_parts2[blk.name] = get_part_lines(blk)
    elif blk.name.startswith('WeldMark'):
        wm = parse_weldmark(blk)
        if wm:
            print(f"WM: {blk.name}")
            print(f"  arrow_tip = {wm['arrow_tip']}")
            print(f"  texts = {wm['texts']}")
            matches = find_parts_at_point(wm['arrow_tip'], view_parts2, SNAP_TOL)
            print(f"  matches ({len(matches)}):")
            for m2 in matches:
                length_mm = round(m2['line']['length'] * SCALE, 1)
                print(f"    {m2['part']}: {m2['how']} line_len={length_mm}mm "
                      f"s={tuple(round(c,2) for c in m2['line']['start'])} "
                      f"e={tuple(round(c,2) for c in m2['line']['end'])}")
