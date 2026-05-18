with open("weld_extractor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find MIN_EDGE line
min_edge_idx = None
for i, line in enumerate(lines):
    if "MIN_EDGE        = 1.5  # CAD units" in line:
        min_edge_idx = i
        break

# Find unlabeled_passthru line
unlabeled_idx = None
for i in range(min_edge_idx, len(lines)):
    if "unlabeled_passthru = {}" in lines[i]:
        unlabeled_idx = i
        break

# Find weld_edges_all line  
weld_all_idx = None
for i in range(unlabeled_idx, len(lines)):
    if "weld_edges_all = [(e, op, gn, frags)" in lines[i]:
        weld_all_idx = i
        break

# Find the "if not weld_edges_all:" skip block and the continue line
# after the output loop (the "continue  # skip normal weld processing for 3-SIDES" line)
continue_idx = None
for i in range(weld_all_idx, len(lines)):
    if "continue  # skip normal weld processing for 3-SIDES" in lines[i]:
        continue_idx = i
        break

print(f"MIN_EDGE={min_edge_idx+1}, unlabeled={unlabeled_idx+1}, weld_all={weld_all_idx+1}, continue={continue_idx+1}")

# 1. Insert synthetic block after MIN_EDGE line + blank line
synth_block = '''                # Circle-annotated plate on non-comp: generate
                # 3 perimeter edges from comp section + weld line.
                _synth = _use_largest_gusset and bool(comp_dims.get("flange_w"))
                if _synth:
                    _, _wl, _ = choose_weld_line(arrow, matches)
                    _mid_cad = _wl["length"] if _wl else 0
                    _fw_cad = comp_dims["flange_w"] / SCALE
                    if _mid_cad > 0 and _fw_cad > 0:
                        _comp_blk = next((pn for pn, lbl in part_number_map.items()
                                         if lbl == comp), gusset_name)
                        _dum_fw = {"start": (0.0, 0.0), "end": (_fw_cad, 0.0), "length": _fw_cad}
                        _dum_md = {"start": (0.0, 0.0), "end": (_mid_cad, 0.0), "length": _mid_cad}
                        _synth_edges = [
                            (_fw_cad, _comp_blk, [_dum_fw]),
                            (_mid_cad, _comp_blk, [_dum_md]),
                            (_fw_cad, _comp_blk, [_dum_fw]),
                        ]
                        weld_edges_by_gusset = {}
                        for _gn in gusset_names:
                            weld_edges_by_gusset[_gn] = _synth_edges
                    else:
                        skipped.append((wm_name, "CIRCLE: no weld line or comp flange width"))
                        continue
                if not _synth:

'''.splitlines(True)

# Insert synthetic block after MIN_EDGE + blank line
insert_pos = min_edge_idx + 2  # after MIN_EDGE line + blank line
lines = lines[:insert_pos] + synth_block + lines[insert_pos:]

# Now we need to indent the existing code from unlabeled_passthru to weld_edges_all
# Each line in this range needs 4 more spaces of indentation
# Re-find indices after insertion
new_unlabeled = None
new_weld_all = None
new_continue = None
for i, line in enumerate(lines):
    if "unlabeled_passthru = {}" in line and new_unlabeled is None:
        new_unlabeled = i
    if "weld_edges_all = [(e, op, gn, frags)" in line and new_unlabeled is not None:
        new_weld_all = i
        break
for i in range(new_weld_all, len(lines)):
    if "continue  # skip normal weld processing for 3-SIDES" in line:
        new_continue = i
        break

print(f"New: unlabeled={new_unlabeled+1}, weld_all={new_weld_all+1}, continue={new_continue+1}")

# Indent from unlabeled to weld_all (exclusive) by 4 spaces
for i in range(new_unlabeled, new_weld_all):
    if lines[i].strip():
        lines[i] = "    " + lines[i]

# Indent from weld_all+1 to continue (inclusive) - these are INSIDE the output block
# but at the same indentation as weld_edges_all. They should also be indented.
# Actually, weld_edges_all is OUTSIDE the if not _synth block.
# The block structure is:
# if not _synth:
#     (unlabeled through weld_edges_by_gusset)
# weld_edges_all = ...  (same level as if not _synth)
# if not weld_edges_all: ...
# output loop...
# continue  (same level as if not _synth)

# The "continue" line is at the same level as "if not _synth"
# weld_edges_all is at the same level
# Everything between them stays at same indentation

with open("weld_extractor.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("BOM synthetic + wrapper applied")
