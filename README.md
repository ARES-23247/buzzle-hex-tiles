# Dual-Color Hexagonal Scrabble 3D Printable Tiles

Parametric 3D printable 1.5-inch diameter hexagonal tiles with Scrabble-style letters and numbers. Specifically designed and optimized for **two-color 3D printing with toolhead changers** (such as the Prusa XL multi-toolhead, Bambu Lab X1/P1/A1 with AMS, Voron StealthChanger/ERCF, IDEX, and dual-extrusion printers).

---

## 📐 Design & Engineering Specifications

- **Diameter**: `1.5 inches` (`38.1 mm`) flat-to-flat incircle diameter. Adjacent tiles snap together in a continuous hexagonal grid with exact 1.5" row spacing. (Point-to-point circumcircle diameter is `44.0 mm`).
- **Thickness / Height**: `4.8 mm` (~3/16 inch) — provides solid heft and tactile feel.
- **Perimeter Chamfer**: `0.8 mm` ($45^\circ$) along the top outer rim for smooth ergonomics and easy pickup from flat tabletop surfaces.
- **Inlay Depth**: `0.8 mm` ($4$ solid layers at $0.20\text{ mm}$ layer height), guaranteeing complete visual color opacity without the base color showing through.
- **Multi-Part Architecture**:
  - **`Tile_Base`** (Toolhead 1): Main hexagonal body with a 0.8mm negative cavity.
  - **`Tile_Text`** (Toolhead 2): Exact positive glyph inlay with matching 0.8mm depth.

---

## 🖨️ Slicing & Toolhead Changer Instructions

### 1. Loading `.3mf` Files (PrusaSlicer, OrcaSlicer, Bambu Studio)
1. Drag and drop any `.3mf` file from `output/3mf/` or `output/plates/` into your slicer.
2. When prompted: **"This file contains multiple objects. Do you want to load them as a single object with multiple parts?"** $\to$ Click **YES**.
3. In the object list:
   - Set **`Tile_Base`** to **Extruder / Filament 1** (e.g., Ivory, Cream, White, or Wood PLA/PETG).
   - Set **`Tile_Text`** to **Extruder / Filament 2** (e.g., Jet Black, Navy, Maroon, or Gold PLA/PETG).

### 2. Loading Dual STL Files (Cura, SuperSlicer, Simplify3D)
1. Select both `*_base.stl` and `*_text.stl` files simultaneously.
2. Drag and drop both into the slicer.
3. Select both parts, right-click, and choose **Merge / Group as Multi-Material Object**.
4. Assign Extruder 1 to Base and Extruder 2 to Text.

### 💡 Pro Tip: Face-Down Printing on Textured PEI
For the absolute highest quality finish with **minimal toolhead swaps**:
1. Rotate the tile assembly **$180^\circ$ upside down** so the top face with the letters rests directly on the build plate.
2. Print on a **textured PEI sheet** (or satin powder-coated sheet).
3. **Benefits**:
   - The top face of the tile will take on the beautiful, uniform, seamless texture of the PEI sheet with zero visible layer lines.
   - Both colors are printed flat on the first $0.8\text{ mm}$ (layers 1 to 4).
   - After layer 4, the printer switches to the Base toolhead and finishes the remainder of the tile with **zero additional toolhead changes**!

### Recommended Print Settings
- **Layer Height**: `0.20 mm` (or `0.16 mm` for ultra-fine lettering)
- **First Layer Height**: `0.20 mm`
- **Perimeters / Wall Loops**: `3` or `4`
- **Top / Bottom Solid Layers**: `4` or `5`
- **Infill**: `15% - 20%` (Gyroid or Grid)
- **Ironing** (if printing face-up): Enabled on topmost surface with 15% flow for smooth top faces.

---

## 📁 File Structure

```
hex-scrabble-tiles/
├── generate_tiles.py             # Python CAD & 3MF/STL generation pipeline
├── hex_scrabble_tiles.scad       # Parametric OpenSCAD Customizer script
├── requirements.txt              # Python dependencies
├── README.md                     # Printing & slicing guide
└── output/
    ├── 3mf/                      # 44 individual multi-material .3mf tiles
    │   ├── tile_A_score1.3mf
    │   ├── tile_B_score3.3mf
    │   ├── tile_num_7.3mf
    │   └── ...
    ├── stl/                      # 88 paired binary STL models
    │   ├── tile_A_score1_base.stl
    │   ├── tile_A_score1_text.stl
    │   └── ...
    ├── plates/                   # Batch build plates (honeycomb packed)
    │   ├── plate_letters_A_M.3mf             # 13 tiles (Letters A to M)
    │   ├── plate_letters_N_Z_Blank.3mf       # 14 tiles (Letters N to Z + Blank)
    │   └── plate_numbers_and_symbols.3mf     # 17 tiles (0-9, +, -, x, /, =, ?, !)
    └── previews/                 # Visual 3D Isometric & Top-Down preview renders
```

---

## 🛠️ Generating Custom Tiles & Words via CLI

You can generate custom words, custom sizes, or specific single tiles using `generate_tiles.py`:

```bash
# Generate a specific letter tile with custom score
python generate_tiles.py --letter K --score 5

# Generate a specific number tile
python generate_tiles.py --number 8

# Generate a complete word set
python generate_tiles.py --word SCRABBLE

# Generate a 2.0 inch (50.8 mm) oversized tile
python generate_tiles.py --letter A --size 50.8

# Generate embossed (raised 0.6mm) text instead of flush inlay
python generate_tiles.py --letter A --embossed 0.6

# Regenerate the entire set and all batch plates
python generate_tiles.py --all --plates
```

---

## 🎛️ Parametric Customization in OpenSCAD

If you prefer OpenSCAD:
1. Open `hex_scrabble_tiles.scad` in **OpenSCAD**.
2. Open the **Window $\to$ Customizer** panel.
3. Adjust `tile_flat_to_flat`, `tile_height`, `chamfer`, `inlay_depth`, `char_letter`, `char_score`, or `font_name`.
4. Render (`F6`) and export as STL or 3MF.
