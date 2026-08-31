# 🎨 3D Printing Color & Filament Guide

This guide details the recommended filament colors, toolhead assignments, and print counts for both the **Hive Game Set** and the **Scrabble Tile Set**.

---

## 🐜 1. "HIVE" Game Set: Printing Color Matrix

Hive is an asymmetric 2-player game where each player controls an opposing insect army (14 tiles per player = 28 tiles total).

### 📋 Full Piece Count & Inventory

| Insect Piece | Count (1 Player) | Total (2 Players) | Base Game / Exp |
| :--- | :---: | :---: | :--- |
| **Queen Bee** | 1 | 2 | Base Game |
| **Spider** | 2 | 4 | Base Game |
| **Beetle** | 2 | 4 | Base Game |
| **Grasshopper** | 3 | 6 | Base Game |
| **Soldier Ant** | 3 | 6 | Base Game |
| **Mosquito** | 1 | 2 | Expansion |
| **Ladybug** | 1 | 2 | Expansion |
| **Pillbug** | 1 | 2 | Expansion |
| **TOTAL** | **14 Tiles** | **28 Tiles** | **Master Set** |

---

### 🎨 Scheme A: Classic High-Contrast 2-Color Setup (Recommended)
*Requires only 2 spools of filament across your print runs.*

#### ⚪ Player 1: White / Ivory Team
* **Build Plate**: `output_hive/plates/plate_player_full_set_14tiles.3mf` (Run 1)
* **Toolhead 1 (Base Body)**: **White / Ivory / Cream PLA**
* **Toolhead 2 (Insect Inlay)**: **Jet Black / Dark Slate PLA**

#### ⚫ Player 2: Black / Carbon Team
* **Build Plate**: `output_hive/plates/plate_player_full_set_14tiles.3mf` (Run 2)
* **Toolhead 1 (Base Body)**: **Jet Black / Dark Slate PLA**
* **Toolhead 2 (Insect Inlay)**: **White / Ivory / Cream PLA**

---

### 🌈 Scheme B: Official Color-Coded Insect Scheme
*Matches the official Hive tournament colors for instant visual identification.*

| Insect Piece | Player 1 Base | Player 2 Base | Insect Inlay Color (Official) |
| :--- | :--- | :--- | :--- |
| **Queen Bee** | White / Ivory | Black / Carbon | 🟡 **Bright Yellow / Gold** |
| **Spider** | White / Ivory | Black / Carbon | 🟤 **Brown / Burnt Orange** |
| **Beetle** | White / Ivory | Black / Carbon | 🟣 **Purple / Violet** |
| **Grasshopper** | White / Ivory | Black / Carbon | 🟢 **Vibrant Green / Lime** |
| **Soldier Ant** | White / Ivory | Black / Carbon | 🔵 **Royal Blue / Cyan** |
| **Mosquito** *(Exp)* | White / Ivory | Black / Carbon | ⚪ **Metallic Silver / Light Gray** |
| **Ladybug** *(Exp)* | White / Ivory | Black / Carbon | 🔴 **Crimson Red** |
| **Pillbug** *(Exp)* | White / Ivory | Black / Carbon | 🔷 **Sky Blue / Teal** |

---

## 🎲 2. "SCRABBLE" Tile Set: Printing Color Matrix

### 📋 Full Scrabble Inventory & Points

| Letter | Points | Base Game Qty | Letter | Points | Base Game Qty |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 1 | 9 | **N** | 1 | 6 |
| **B** | 3 | 2 | **O** | 1 | 8 |
| **C** | 3 | 2 | **P** | 3 | 2 |
| **D** | 2 | 4 | **Q** | 10 | 1 |
| **E** | 1 | 12 | **R** | 1 | 6 |
| **F** | 4 | 2 | **S** | 1 | 4 |
| **G** | 2 | 3 | **T** | 1 | 6 |
| **H** | 4 | 2 | **U** | 1 | 4 |
| **I** | 1 | 9 | **V** | 4 | 2 |
| **J** | 8 | 1 | **W** | 4 | 2 |
| **K** | 5 | 1 | **X** | 8 | 1 |
| **L** | 1 | 4 | **Y** | 4 | 2 |
| **M** | 3 | 2 | **Z** | 10 | 1 |
| **BLANK** | 0 | 2 | **TOTAL** | — | **100 Tiles** |

---

### 🎨 Scrabble Filament Recommendations

#### Classic Wooden Look:
* **Toolhead 1 (Tile Base)**: **Wood-fill PLA** or **Warm Ivory / Birch Cream PLA**
* **Toolhead 2 (Letters & Score)**: **Dark Walnut Brown / Matte Black PLA**

#### Modern Luxury Look:
* **Toolhead 1 (Tile Base)**: **Marble White / Matte Off-White PLA**
* **Toolhead 2 (Letters & Score)**: **Silk Metallic Gold / Copper PLA**

#### High-Contrast Game Night:
* **Toolhead 1 (Tile Base)**: **Signal White PLA**
* **Toolhead 2 (Letters & Score)**: **Deep Navy / Jet Black PLA**

---

## 💡 Quick Slicer Setup Checklist

1. **Orientation**: Flip the tile **$180^\circ$ face-down** on a **textured PEI plate** for a glass-smooth or textured face finish with zero visible top lines.
2. **Layer Height**: `0.20 mm` (First layer `0.20 mm`).
3. **Multi-Material Swaps**: Because the inlay depth is $0.80\text{ mm}$, all color tool changes will occur in the first 4 layers only; the remaining 20 layers print seamlessly in a single toolhead with **zero tool swaps**!
4. **Tool Assignment in Slicer**:
   - `Tile_Base` $\to$ Extruder 1
   - `Tile_Insect` / `Tile_Text` $\to$ Extruder 2
