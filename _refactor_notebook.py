import json
import re
from pathlib import Path

src = Path(r"c:/Users/schona/OneDrive - Capgemini/Capgemini/SampleMLProjet-main/OG file.ipynb")
dst = Path(r"c:/Users/schona/OneDrive - Capgemini/Capgemini/SampleMLProjet-main/OG file_refactored_full.ipynb")

nb = json.loads(src.read_text(encoding="utf-8"))
cells = nb.get("cells", [])
code_cells = [c for c in cells if c.get("cell_type") == "code"]

import_lines = []
seen_imports = set()
for cell in code_cells:
    for raw in cell.get("source", []):
        line = raw.rstrip("\n").strip()
        if re.match(r"^(import\s+.+|from\s+.+\s+import\s+.+)$", line):
            normalized = re.sub(r"\s+", " ", line)
            if normalized not in seen_imports:
                seen_imports.add(normalized)
                import_lines.append(normalized)

required = [
    "import pandas as pd",
    "import numpy as np",
    "import matplotlib.pyplot as plt",
    "import random",
]
for req in required:
    if req not in seen_imports:
        import_lines.insert(0, req)
        seen_imports.add(req)

palette_block = None
for cell in code_cells:
    src_lines = [s.rstrip("\n") for s in cell.get("source", [])]
    for i, line in enumerate(src_lines):
        if line.strip().startswith("complementary_colors") and "=" in line:
            start = i
            end = i
            while end < len(src_lines) and "]" not in src_lines[end]:
                end += 1
            palette_block = [l.rstrip() for l in src_lines[start:end+1]]
            break
    if palette_block:
        break

if not palette_block:
    palette_block = [
        "complementary_colors = [",
        "    '#8EA4D2', '#6A0136', '#706A58', '#FF8552', '#031A6B',",
        "    '#FF6978', '#DCEED1', '#E0CA3C', '#F24333', '#FE5D9F',",
        "    '#98CE00', '#CFD2B2', '#F2AF29', '#FFD6AF', '#C4F1BE',",
        "    '#F6BD60', '#197BBD', '#F2BAC9', '#8A89C0', '#F4F9E9',",
        "]",
    ]

setup_helpers = [
    "def get_colors_for_bars_random(n_bars, palette):",
    "    if n_bars <= 0:",
    "        return []",
    "    if n_bars > len(palette):",
    "        full_palette = palette * ((n_bars // len(palette)) + 1)",
    "        random.shuffle(full_palette)",
    "        return full_palette[:n_bars]",
    "    return random.sample(palette, n_bars)",
    "",
    "def get_colors_for_bars(n_bars, palette):",
    "    return get_colors_for_bars_random(n_bars, palette)",
    "",
    "def get_colors(n_bars, palette):",
    "    return get_colors_for_bars_random(n_bars, palette)",
    "",
    "def clean_column_names(dataframe):",
    "    dataframe = dataframe.copy()",
    "    dataframe.columns = (",
    "        dataframe.columns",
    "        .str.strip()",
    "        .str.replace('\\n', ' ', regex=False)",
    "        .str.replace('\\xa0', ' ', regex=False)",
    "    )",
    "    return dataframe",
]

setup_source = ["# Global setup: consolidated imports, palette, helpers"] + import_lines + [""] + palette_block + [""] + setup_helpers
load_source = [
    "# Centralized data loading and preparation",
    "file_path = 'Sheriffhall Roundabout & A720 Bypass_ Community Travel and Congestion Questionnaire.xlsx'",
    "df = pd.read_excel(file_path)",
    "df = clean_column_names(df)",
    "print('Total responses:', len(df))",
]

def strip_duplicate_blocks(lines):
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].rstrip("\n")
        t = s.strip()
        low = t.lower()

        if re.match(r"^(import\s+.+|from\s+.+\s+import\s+.+)$", t):
            i += 1
            continue

        if t.startswith("complementary_colors") and "=" in t:
            i += 1
            while i < len(lines) and "]" not in lines[i]:
                i += 1
            if i < len(lines):
                i += 1
            continue

        if re.match(r"^def\s+(get_colors_for_bars_random|get_colors_for_bars|get_colors|clean_column_names|find_col_enhanced)\s*\(", t):
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    i += 1
                    continue
                if not nxt.startswith(" ") and not nxt.startswith("\t"):
                    break
                i += 1
            continue

        if t.startswith("file_path =") or t.startswith("df = pd.read_excel"):
            i += 1
            continue

        if t.startswith("df.columns ="):
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                i += 1
                if nxt == ")":
                    break
            continue

        if "# load data" in low or "# clean column names" in low or "# custom color palette" in low:
            i += 1
            continue

        out.append(s)
        i += 1

    while out and out[0].strip() == "":
        out.pop(0)
    while out and out[-1].strip() == "":
        out.pop()

    return out

new_cells = [
    {
        "cell_type": "markdown",
        "metadata": {"language": "markdown"},
        "source": [
            "# Refactored Notebook (Outputs Preserved)",
            "",
            "This version consolidates imports, palette/theme helpers, and common data preparation while keeping figure/theme logic intact.",
        ],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"language": "python"},
        "outputs": [],
        "source": [ln + "\n" for ln in setup_source],
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"language": "python"},
        "outputs": [],
        "source": [ln + "\n" for ln in load_source],
    },
]

code_idx = 0
for cell in cells:
    ctype = cell.get("cell_type")
    if ctype == "markdown":
        src_text = "".join(cell.get("source", [])).strip().lower()
        if src_text in {"done", ""}:
            continue
        new_cells.append({
            "cell_type": "markdown",
            "metadata": {
                "language": "markdown",
                "id": cell.get("id", f"md-{len(new_cells)+1}"),
            },
            "source": cell.get("source", []),
        })
    elif ctype == "code":
        code_idx += 1
        stripped = strip_duplicate_blocks(cell.get("source", []))
        if not stripped:
            continue
        new_cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {
                "language": "python",
                "id": cell.get("id", f"code-{code_idx}"),
            },
            "outputs": [],
            "source": [ln + "\n" for ln in stripped],
        })

refactored_nb = {
    "cells": new_cells,
    "metadata": nb.get("metadata", {}),
    "nbformat": nb.get("nbformat", 4),
    "nbformat_minor": nb.get("nbformat_minor", 5),
}

dst.write_text(json.dumps(refactored_nb, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created: {dst}")
print(f"Refactored cells: {len(new_cells)}")
print(f"Refactored code cells: {sum(1 for c in new_cells if c.get('cell_type') == 'code')}")
