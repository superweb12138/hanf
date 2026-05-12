"""Patch weld_extractor.py to add flange plate override for p200."""

# Read the file
with open('weld_extractor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "_bom_edge_map = {}"
insert_pos = None
for i, line in enumerate(lines):
    if '_bom_edge_map = {}' in line and i > 700:
        insert_pos = i
        break

if insert_pos is None:
    print("ERROR: Could not find insertion point")
    exit(1)

print(f"Found insertion point at line {insert_pos + 1}")

# Find the line "if _bw3 and _bl3:" after insert_pos
target_line = None
for i in range(insert_pos, min(insert_pos + 20, len(lines))):
    if 'if _bw3 and _bl3:' in lines[i]:
        target_line = i
        print(f"Found target line at {target_line + 1}: {lines[i].strip()}")
        break

if target_line is None:
    print("ERROR: Could not find target line 'if _bw3 and _bl3:'")
    print("Lines after insert_pos:")
    for i in range(insert_pos, min(insert_pos + 20, len(lines))):
        print(f"  {i+1}: {lines[i].rstrip()}")
    exit(1)

# Insert the new code before "if _bw3 and _bl3:"
indent = '                    '
new_code = [
    indent + '\n',
    indent + '# Strategy C: Flange plate override (for p200-like plates)\n',
    indent + '# Check if this is a flange plate (width ≈ comp flange width)\n',
    indent + '_is_flange_plate = False\n',
    indent + "if _bw3 and comp_dims.get('flange_w'):\n",
    indent + "    if abs(_bw3 - comp_dims['flange_w']) < 10:\n",
    indent + '        _is_flange_plate = True\n',
    indent + '\n',
    indent + 'if _bw3 and _is_flange_plate:\n',
    indent + '    # Collect all unique geo lengths from this gusset\n',
    indent + '    _gusset_geo_lens = []\n',
    indent + '    for _el, _op, _cg in weld_edges_all:\n',
    indent + '        _geo_mm = round(_el * SCALE, 1)\n',
    indent + '        if _geo_mm not in _gusset_geo_lens:\n',
    indent + '            _gusset_geo_lens.append(_geo_mm)\n',
    indent + '    \n',
    indent + '    # Check if geo edges are far from BOM width (section-view distortion)\n',
    indent + '    _all_far = all(\n',
    indent + '        abs(_g - _bw3) / max(_g, 1) > 0.4\n',
    indent + '        for _g in _gusset_geo_lens\n',
    indent + '    )\n',
    indent + '    \n',
    indent + '    if _all_far and len(_gusset_geo_lens) >= 2:\n',
    indent + '        # Map: largest geo → comp depth, others → plate width\n',
    indent + '        _sorted_geo = sorted(_gusset_geo_lens)\n',
    indent + "        _comp_depth = comp_dims.get('depth', _bl3 if _bl3 else 270)\n",
    indent + '        \n',
    indent + '        # Map all geo edges for all gusset instances\n',
    indent + '        for _cg in set(_cg for _, _, _cg in weld_edges_all):\n',
    indent + '            for _g in _gusset_geo_lens:\n',
    indent + '                if _g == _sorted_geo[-1]:\n',
    indent + '                    # Largest edge → comp depth\n',
    indent + '                    _bom_edge_map[(_cg, _g)] = round(_comp_depth)\n',
    indent + '                else:\n',
    indent + '                    # Other edges → plate width\n',
    indent + '                    _bom_edge_map[(_cg, _g)] = round(_bw3)\n',
    indent + '        \n',
    indent + '        print(f"    [BOM map-flange] {lbl_g}  w={_bw3} depth={round(_comp_depth)} (geo far from BOM)")\n',
    indent + '\n',
]

# Insert the new code
lines[target_line:target_line] = new_code

# Write back
with open('weld_extractor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Successfully patched! Inserted {len(new_code)} lines before line {target_line + 1}")
