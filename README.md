# 焊缝统计自动提取工具

从结构构件 DXF 图纸中自动提取焊缝信息，输出 Excel 焊缝统计表。

---

## 目录

- [项目背景](#项目背景)
- [环境依赖](#环境依赖)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [核心脚本详解](#核心脚本详解)
- [DXF 结构约定](#dxf-结构约定)
- [关键参数与常量](#关键参数与常量)
- [算法流程](#算法流程)
- [当前精度状态](#当前精度状态)
- [已知遗留问题](#已知遗留问题)
- [诊断脚本说明](#诊断脚本说明)

---

## 项目背景

钢结构工程图纸（DWG/DXF 格式）中，焊缝信息分散在各构件图中，需要人工汇总统计。本工具通过解析 DXF 文件内的 `WeldMark` 和 `Part` 块，自动提取每道焊缝的：

- 所属构件（如 BE018、CO007）
- 焊缝位置（Above / Below 箭头侧）
- 焊脚尺寸 hf（mm），CJP 坡口焊为 None
- 焊缝长度（mm）
- 连接零件对（如 `BE020/p175`）

输出文件：`焊缝统计_auto.xlsx`

---

## 环境依赖

```
Python 3.9+
ezdxf >= 1.1
openpyxl >= 3.1
```

安装：

```bash
pip install ezdxf openpyxl
```

---

## 文件说明

### 主要脚本

| 文件 | 用途 |
|------|------|
| `weld_extractor.py` | **核心**：读取所有 DXF → 输出 `焊缝统计_auto.xlsx` |
| `compare_lengths.py` | 将脚本输出与人工标准答案做精确对比 |
| `analyse_diff.py` | 对比脚本输出与人工答案的逐构件详细差异 |
| `convert_dwg_to_dxf.py` | 批量把 DWG 转换为 DXF（只需运行一次）|

### 数据文件

| 文件 | 说明 |
|------|------|
| `焊缝统计_auto.xlsx` | 脚本自动生成的焊缝统计（每次运行覆盖）|
| `焊缝统计R3_auto(1).xlsx` | **人工标准答案**，用于精度对比 |
| `焊缝统计.xlsx` | 另一份人工参考表（`analyse_diff.py` 使用）|
| `*.dxf` | 各构件 DXF 图纸（由 DWG 转换得到）|

### 有 DXF 文件的构件

```
BE018  BE019  BE020  BE021  BE022  BE023
CO007  CO008  CO009
```

> CO006、CO010 目前**没有 DXF 文件**，脚本不处理这两个构件。

---

## 快速开始

### 第一步：转换 DWG（如 DXF 已存在可跳过）

```bash
python convert_dwg_to_dxf.py
```

### 第二步：提取焊缝

```bash
python weld_extractor.py
```

输出：`焊缝统计_auto.xlsx`

### 第三步：与标准答案对比（可选）

```bash
python compare_lengths.py
```

输出每行的状态：`OK` / `LEN-DIFF` / `MISSED` / `SCRIPT-ONLY`，并汇总精确匹配数。

---

## 核心脚本详解

### `weld_extractor.py`

#### 顶部配置（修改这里来适配新图纸）

```python
FOLDER   = r"c:\...\hanf"       # DXF 文件所在目录
OUTPUT   = os.path.join(FOLDER, "焊缝统计_auto.xlsx")
SCALE    = 10.0                  # 1 CAD 单位 = 10 mm
SNAP_TOL = 1.5                   # 焊缝箭头与零件线的捕捉容差（CAD 单位）
MAX_HF   = 20                    # hf 上限；超过此值视为板厚标注
LABEL_TIP_TOL = 8.0              # 引线端点匹配零件的容差（CAD 单位）
```

#### 主要函数

| 函数 | 说明 |
|------|------|
| `parse_weldmark(blk)` | 解析 WeldMark 块：提取 hf、CJP 标志、`3 SIDES`/`2 SIDES` 标注、`TYP` 标志、箭头位置 |
| `get_part_lines(blk)` | 获取 Part 块中所有 LINE 实体的几何信息 |
| `find_all_labels(doc)` | 从 Mark 块的引线端点提取零件编号（如 p122）|
| `assign_labels_by_leader_tip(...)` | 将零件编号分配到对应的 Part 块 |
| `choose_weld_line(arrow, matches)` | 四级规则确定焊缝所在的零件线 |
| `parse_bom(doc, comp)` | 解析 Unknown 块中的材料表，得到零件厚度/宽度/长度 |
| `hf_from_thickness(t)` | 按板厚查标准最小填角焊脚尺寸 |
| `extract_welds(dxf_path)` | 单个 DXF 文件的完整提取逻辑（主函数）|

---

## DXF 结构约定

脚本依赖以下 DXF 块命名规则（由 Tekla/AutoCAD 导出）：

```
WeldMark-<ID> - <视图ID>   → 焊缝标注块
Part-<ID> - <视图ID>       → 零件几何块
Mark-<ID> - <视图ID>       → 零件编号引线块
Unknown-<ID>               → 材料表（BOM）块（无视图ID后缀）
```

同一 `视图ID` 的 WeldMark 和 Part 块属于同一个视图，脚本按视图分组处理。

---

## 关键参数与常量

### 几何容差

| 常量 | 值 | 含义 |
|------|----|------|
| `SNAP_TOL` | 1.5 CAD | 箭头端点到零件线的最大距离 |
| `LABEL_TIP_TOL` | 8.0 CAD | 引线端点匹配零件线的最大距离 |
| `MIN_EDGE` | 1.5 CAD | 3-SIDES 中忽略的退化短边（< 15 mm）|
| `ADJ_TOL` | `SNAP_TOL+0.5` | 3-SIDES 中判断零件边邻接的容差 |

### hf 修正（Sub-rule 3）

当 WM 标注的尺寸恰好等于板厚或腹板厚时，按标准表替换为最小填角尺寸：

```python
_HF_FROM_T = {6:5, 7:5, 8:6, 9:6, 10:7, 11:8, 12:8, 14:10, 16:10, 18:12, 20:12}
```

### TYP（典型焊缝）处理

WM 文本包含 `TYP` 时，表示图中只标了一次，但实际有多个对称实例。脚本会：

1. 统计**主视图**（Part 块最多的视图）中该零件的实例数 → `typ_multiplier`
2. 将焊缝行复制 `typ_multiplier` 份输出
3. 对于 3-SIDES TYP：`typ_multiplier ÷ len(gusset_names)`，避免与多筋板逻辑重复计数

### BOM 回退（comp/comp 情形）

当 WM 箭头落在构件本体（comp）自身线上导致两端零件都是 comp 时，脚本扫描 BOM 中的零件宽度，找到与焊缝几何长度最接近的非 comp 零件（容差 15%），并以该零件在 `part_number_map` 中的实例数确定输出行数。

---

## 算法流程

```
DXF 文件
  │
  ├─ parse_bom()           读取材料表 → part_dims, comp_dims
  │
  ├─ 按视图 ID 分组
  │    WeldMark 块 → wm_by_view
  │    Part 块    → part_by_view
  │
  ├─ find_all_labels()     解析引线 → 零件编号
  ├─ assign_labels_by_leader_tip()  → part_number_map
  │
  └─ 对每个视图中的每个 WeldMark：
       │
       ├─ parse_weldmark()   提取 hf/CJP/annotation/is_typ
       │
       ├─ [3-SIDES 分支]
       │    找最小非 comp 零件作为筋板 (gusset)
       │    枚举筋板所有邻接边 → edge_rows
       │    TYP 倍数 × edge_rows → results
       │
       └─ [普通 WM 分支]
            choose_weld_line() 确定焊缝零件和长度
            hf 修正（Sub-rule 3）
            haunch 端面长度修正
            BOM 宽度修正
            TYP 倍数 / BOM 回退倍数
            → results

  结果写入 Excel（焊缝统计_auto.xlsx）
```

---

## 当前精度状态

以 `焊缝统计R3_auto(1).xlsx` 为标准答案：

| 构件 | 行数（AUTO） | 行数（CORR）| 状态 |
|------|:-----------:|:-----------:|------|
| BE018 | 14 | 14 | ✅ 完全匹配 |
| BE019 | 14 | 14 | ✅ 完全匹配 |
| BE020 | 22 | 22 | ✅ 完全匹配 |
| BE021 | 20 | 20 | ✅ 行数匹配（部分长度/零件名有差异）|
| BE022 | 30 | 30 | ✅ 完全匹配 |
| BE023 | 22 | 22 | ✅ 完全匹配 |
| CO007 | 37 | 48 | ⚠️ 少行（Part 标签/焊缝匹配偏差）|
| CO008 | 35 | 42 | ⚠️ 少行（同上）|
| CO009 | 24 | 28 | ⚠️ 少行 |
| CO006 | — | 12 | ❌ 无 DXF |
| CO010 | — | 166 | ❌ 无 DXF |

---

## 已修复问题

### BE022 / BE023 — p26 / p48 BOM 长度映射错误

p26 (bw=95, bl=200) 和 p48 (bw=95, bl=140) 中当焊缝几何长度 `geo` 等于 BOM 长度 `bl` 时，原 BOM case1 逻辑错误地将 `geo` 替换为 `bw`（例如 `geo=200 → 95`）。

**修复**：增加 `case1-skip` 分支（`weld_extractor.py:1030-1034`），当 `geo ≈ bl` 且 `bl` 与 `bw` 差异明显（`>30%`）时跳过替换，保留 `geo` 不变。这对应"焊缝沿板长方向"的场景。

### BE023 — p200 三边映射错误

p200 (bw=140, bl=268) 的 3-SIDES 三条几何边为 `[231.4, 268.0, 438.9]`。原 Strategy B 用"排序后盲配"将 `[231.4, 268.0, 438.9]` 依次对应 `[140, 140, 268]`，导致 `geo=268.0`（与 `bl=268` 几乎相等）被错误映射为 `140`(bw)，而 `geo=438.9` 被错误映射为 `268`(bl)。

**修复**：修改 Strategy B（`weld_extractor.py:836-855`），不再用排序位置盲配，改为"找最接近 bl 的几何边作为长度边，其余两边映射为 bw"。修复后正确输出：`231.4→140, 438.9→140, 268.0→268`。

### BOM 零件数量解析 & CO 类构件 TYP 计数修正

BOM 解析时 `qty` 列原本取第一个匹配 `\d{1,2}` 的数字（序号），修正为按 X 坐标左→右排序后取**第二个**匹配数字（数量列）。同时，柱型构件（CO）的 TYP 倍数从仅统计主视图改为优先使用 BOM 中的零件数量，弥补加劲肋分布在多个截面视图导致主视图统计不足的问题。梁型构件（BE）不受影响，仍沿用主视图统计。

**修复位置**：
- BOM qty 解析：`weld_extractor.py:506-531`
- 普通 WM TYP 计数：`weld_extractor.py:990-1001`（CO 类构件启用 BOM qty 回退）
- 效果：CO007 `+6` 行（p124 TYP ×2），CO008 `+6` 行，BE022/BE023 不受影响

## 已知遗留问题

### CO007 / CO008 / CO009 — Part 标签与焊缝匹配偏差

TYP 计数问题已通过 BOM qty 回退部分改善（CO007/CO008 各增加约 6 行），但距离标准答案仍有差距。剩余偏差主要来自：

1. **Part 标签分配错误**：部分焊缝箭头落在加劲肋线上被标注为 `p124/p47` 而非 `CO007/p47`，因为构件本体（CO007）在该视图中缺少 Part 块。
2. **焊脚尺寸 hf 不匹配**：部分焊缝标注了 CJP/坡口焊而人工答案标记为填角焊（如 p124），或 hf 等级不一致。
3. **3-SIDES 边数多于预期**：p101 筋板几何边数与人工答案条目数不一致。

**建议方向**：引入"comp 回退匹配"——当箭头落在非 comp 零件线上时，检查临近是否有 comp 的几何边；优化 hf 从板厚推算的规则（Sub-rule 3）。

### CO006 / CO010 — 缺少 DXF

这两个构件只有 DWG 和 PDF，需要先用 ODA File Converter 或 AutoCAD 导出为 DXF，再运行 `convert_dwg_to_dxf.py` 处理。

---

## 诊断脚本说明

| 脚本 | 用途 |
|------|------|
| `compare_lengths.py` | 精确对比 `焊缝统计_auto.xlsx` 与标准答案，输出 OK/LEN-DIFF/MISSED/SCRIPT-ONLY |
| `analyse_diff.py` | 逐构件列出漏报行和误报行，含长度对比 |
| `diag_wm.py` | 打印指定 DXF 的所有 WeldMark 块文本内容 |
| `diag_be021.py` | BE021 专项：打印各视图的零件→标签映射和 WM 箭头信息 |
| `diag_bom.py` | 打印指定 DXF 的 BOM 解析结果（零件厚度/宽度/长度）|
| `diag_blocks.py` | 列出 DXF 中所有块名及类型 |
| `diag_parts.py` | 打印各视图的 Part 块几何信息 |
| `show_fp.py` | 显示指定构件的焊缝 "false positive"（脚本多出的行）|
| `explore_dxf.py` | 通用 DXF 结构探查工具 |

**典型调试流程**：

```bash
# 1. 查看某构件所有 WM 的文本
python diag_wm.py          # 在脚本内修改 target DXF 路径

# 2. 运行提取并对比
python weld_extractor.py
python compare_lengths.py

# 3. 详细差异
python analyse_diff.py
```
