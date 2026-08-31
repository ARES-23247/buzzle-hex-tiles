# 🎨 3D Printing Color & Filament Guide (4-Color Printer Optimized)

This guide details the recommended filament colors, 4-slot AMS/Toolhead assignments, and print counts for both the **Hive Game Set** and the **Scrabble Tile Set**.

---

## 🐜 1. "HIVE" 4-Color-Limited Build Plates

If your 3D printer supports a maximum of **4 colors at once** (e.g. Bambu Lab AMS with 4 spool slots, Prusa XL, Voron StealthChanger, or IDEX), the official 8-color Hive set is pre-partitioned into plates containing **at most 1 Base color + 3 Insect colors (4 colors total)**.

Each `.3mf` file in [`output_hive/plates_4color_limited/`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited) has pre-grouped color bodies so your slicer automatically recognizes each extruder slot.

---

### 📦 Set A: 1-Player Army (14 Tiles Across 3 Print Runs)

#### 🖨️ Plate A1: "Core Swarm" (7 Tiles)
* **File**: [`plate_4color_A_core_swarm_7tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_A_core_swarm_7tiles.3mf)
* **Tiles on Plate**: $1\times$ Queen Bee, $3\times$ Grasshopper, $3\times$ Soldier Ant
* **4-Slot Extruder Assignment**:
  * **Slot 1 (Plate_Base)**: ⚪ **White / Ivory** (or ⚫ **Black**)
  * **Slot 2 (Insects_Queen_Bee)**: 🟡 **Bright Yellow / Gold**
  * **Slot 3 (Insects_Grasshopper)**: 🟢 **Vibrant Green**
  * **Slot 4 (Insects_Soldier_Ant)**: 🔵 **Royal Blue / Cyan**

#### 🖨️ Plate A2: "Crawlers" (4 Tiles)
* **File**: [`plate_4color_B_crawlers_4tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_B_crawlers_4tiles.3mf)
* **Tiles on Plate**: $2\times$ Spider, $2\times$ Beetle
* **4-Slot Extruder Assignment**:
  * **Slot 1 (Plate_Base)**: ⚪ **White / Ivory** (or ⚫ **Black**)
  * **Slot 2 (Insects_Spider)**: 🟤 **Brown / Burnt Orange**
  * **Slot 3 (Insects_Beetle)**: 🟣 **Purple / Violet**
  * **Slot 4**: *(Unused / Empty)*

#### 🖨️ Plate A3: "Expansions Pack" (3 Tiles)
* **File**: [`plate_4color_C_expansions_3tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_C_expansions_3tiles.3mf)
* **Tiles on Plate**: $1\times$ Ladybug, $1\times$ Mosquito, $1\times$ Pillbug
* **4-Slot Extruder Assignment**:
  * **Slot 1 (Plate_Base)**: ⚪ **White / Ivory** (or ⚫ **Black**)
  * **Slot 2 (Insects_Ladybug)**: 🔴 **Crimson Red**
  * **Slot 3 (Insects_Mosquito)**: ⚪ **Metallic Silver / Light Gray**
  * **Slot 4 (Insects_Pillbug)**: 🔷 **Sky Blue / Teal**

---

### 🏆 Set B: Complete 2-Player Master Batches (28 Tiles Total)
*Print each plate once for White Team, then repeat with Black Base for Black Team, or print both teams simultaneously!*

| Plate File | Total Tiles | Content | 4-Slot Filament Mapping |
| :--- | :---: | :--- | :--- |
| [`plate_4color_2player_core_swarm_14tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_2player_core_swarm_14tiles.3mf) | **14** | $2\times$ Queen, $6\times$ Hopper, $6\times$ Ant | **1**: Base, **2**: 🟡 Yellow, **3**: 🟢 Green, **4**: 🔵 Blue |
| [`plate_4color_2player_crawlers_8tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_2player_crawlers_8tiles.3mf) | **8** | $4\times$ Spider, $4\times$ Beetle | **1**: Base, **2**: 🟤 Brown, **3**: 🟣 Purple |
| [`plate_4color_2player_expansions_6tiles.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output_hive/plates_4color_limited/plate_4color_2player_expansions_6tiles.3mf) | **6** | $2\times$ Ladybug, $2\times$ Mosquito, $2\times$ Pillbug | **1**: Base, **2**: 🔴 Red, **3**: ⚪ Silver/Gray, **4**: 🔷 Cyan/Teal |

---

## 🎲 2. "SCRABBLE" 4-Color & 2-Color Printing

For Scrabble, only **2 colors** are required per plate:
* **Extruder 1 (Base)**: Warm Ivory, Cream, or Wood PLA
* **Extruder 2 (Glyphs)**: Dark Walnut Brown or Jet Black PLA

#### Scrabble Batch Plates:
* [`plate_letters_A_M.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output/plates/plate_letters_A_M.3mf) (13 tiles)
* [`plate_letters_N_Z_Blank.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output/plates/plate_letters_N_Z_Blank.3mf) (14 tiles)
* [`plate_numbers_and_symbols.3mf`](file:///C:/Users/david/.gemini/antigravity/scratch/hex-scrabble-tiles/output/plates/plate_numbers_and_symbols.3mf) (17 tiles)

---

## 💡 Pro Slicing Tip: Face-Down Printing
1. Rotate the plate assembly **$180^\circ$ upside-down** so the top face rests directly on the build plate.
2. Print on a **textured PEI sheet**.
3. **Huge Efficiency Benefit**: All multi-color toolhead changes happen in the **first $0.80\text{ mm}$ (layers 1 to 4 only)**. After layer 4, the entire remainder of the tile prints in the base color with **zero additional filament purges or tool swaps**!
