"""Add debug output for flange plate detection."""

lines = open('weld_extractor.py', 'r', encoding='utf-8').readlines()
for i, line in enumerate(lines):
    if 'if _bw3 and _is_flange_plate:' in line and i > 760:
        print(f'Found at line {i+1}')
        # Insert debug line after this
        indent = '                        '
        debug_line = indent + 'print(f"    [Flange plate check] {lbl_g}  w={_bw3} is_flange={_is_flange_plate}")\n'
        lines.insert(i+1, debug_line)
        print('Added debug line')
        break
with open('weld_extractor.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done')
