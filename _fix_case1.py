"""Fix BOM case1 logic for p26/p48."""

with open('weld_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the BOM case1 logic
old_logic = """                    if bl and bl > 0 and abs(weld_len_mm - bl) / weld_len_mm < BOM_LEN_TOL:
                        # Case 1: geo ≈ bom_len
                        # Only apply if geo is far from bom_width (end-face weld scenario)
                        if abs(weld_len_mm - bw) / max(weld_len_mm, 1) < BOM_LEN_TOL:
                            # Both bw and bl match; prefer bl (typically the weld
                            # run length, as engineering convention rounds up)
                            print(f"    [BOM case1-both] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl}")
                            weld_len_mm = round(bl)
                        elif abs(weld_len_mm - bw) / max(weld_len_mm, 1) > 0.3:
                            # Only bl matches and geo far from bw → plate end-face weld, use bw
                            print(f"    [BOM case1] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl}")
                            weld_len_mm = round(bw)
                        else:
                            # geo ≈ bl but also somewhat close to bw → keep geo (weld along length)
                            print(f"    [BOM case1-skip] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl} (geo close to both, keep geo)")"""

new_logic = """                    if bl and bl > 0 and abs(weld_len_mm - bl) / weld_len_mm < BOM_LEN_TOL:
                        # Case 1: geo ≈ bom_len
                        # Sub-case: if geo also matches bw closely, prefer bl (both dimensions match)
                        if abs(weld_len_mm - bw) / max(weld_len_mm, 1) < BOM_LEN_TOL:
                            # Both bw and bl match; prefer bl (typically the weld
                            # run length, as engineering convention rounds up)
                            print(f"    [BOM case1-both] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl}")
                            weld_len_mm = round(bl)
                        elif abs(bl - bw) / max(bl, 1) > 0.3:
                            # bl and bw are very different (not a square plate)
                            # geo matches bl → weld runs along plate length, keep geo unchanged
                            # This handles cases like p26: geo=200, bw=95, bl=200
                            print(f"    [BOM case1-skip] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl} (geo=bl, keep geo)")
                        elif abs(weld_len_mm - bw) / max(weld_len_mm, 1) > 0.3:
                            # Only bl matches and geo far from bw → plate end-face weld, use bw
                            print(f"    [BOM case1] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl}")
                            weld_len_mm = round(bw)
                        else:
                            # geo ≈ bl but also somewhat close to bw → keep geo (weld along length)
                            print(f"    [BOM case1-skip2] {lbl_non_comp} geo={weld_len_mm} bw={bw} bl={bl} (geo close to both, keep geo)")"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('weld_extractor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully fixed BOM case1 logic!")
else:
    print("ERROR: Could not find old logic to replace")
    print("Searching for partial match...")
    if "Case 1: geo" in content and "Only apply if geo is far" in content:
        print("Found partial match - logic may have been modified already")
