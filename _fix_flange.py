"""Fix p200 flange plate detection to work without comp_dims."""

with open('weld_extractor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the flange plate detection logic
found = False
for i, line in enumerate(lines):
    if '_is_flange_plate = False' in line and i > 750:
        print(f"Found at line {i+1}")
        # Check next few lines
        if i+1 < len(lines) and "if _bw3 and comp_dims.get('flange_w'):" in lines[i+1]:
            print("Found old logic, replacing...")
            # Replace the next 3 lines
            lines[i+1] = "                    if _bw3:\n"
            lines[i+2] = "                        # Check against comp flange width if available\n"
            lines[i+3] = "                        if comp_dims.get('flange_w') and abs(_bw3 - comp_dims['flange_w']) < 10:\n"
            lines.insert(i+4, "                            _is_flange_plate = True\n")
            lines.insert(i+5, "                        # Also check for typical flange plate widths (140mm for H300, etc.)\n")
            lines.insert(i+6, "                        elif _bw3 in [140, 145, 150]:\n")
            # The old line "if abs(_bw3 - comp_dims['flange_w']) < 10:" becomes the new True assignment
            # Find and replace it
            if i+4 < len(lines) and "_is_flange_plate = True" in lines[i+7]:
                lines[i+7] = "                            _is_flange_plate = True\n"
            found = True
            break

if found:
    with open('weld_extractor.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Successfully fixed flange plate detection!")
else:
    print("ERROR: Could not find the pattern to replace")
    print("Searching for the line...")
    for i, line in enumerate(lines):
        if '_is_flange_plate' in line and i > 750 and i < 800:
            print(f"  {i+1}: {line.rstrip()}")
