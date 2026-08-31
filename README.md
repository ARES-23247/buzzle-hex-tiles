# 🎲 Hex-Tiles: Dual-Color & 4-Color 3D Printable Gaming System
### Scrabble • Hive (Base + Expansions) • Hex-Words • Hive-Swarm • Number Hive

A complete, parametric, multi-material 3D printable gaming ecosystem built around **1.5-inch ($38.1\text{ mm}$) regular hexagonal tiles**, specifically engineered for toolhead changers and multi-material 3D printers (Bambu Lab AMS, Prusa XL, Voron StealthChanger/ERCF, IDEX, and dual-extrusion systems).

---

## 🌟 What's Included in This Project

```
hex-scrabble-tiles/
├── 🎲 Scrabble System (output/)
│   ├── 3mf/                           # 44 individual multi-material Scrabble & Math 3MF models
│   ├── stl/                           # 88 paired binary STLs (Base & Inlay)
│   └── plates/                        # Batch print plates (A–M, N–Z+Blank, Numbers & Symbols)
│
├── 🐜 Hive Game System (output_hive/)
│   ├── 3mf/                           # 8 individual insect pieces (Queen, Spider, Beetle, Ant, Hopper, + Expansions)
│   ├── stl/                           # 16 paired binary STLs
│   ├── plates/                        # Honeycomb batch plates (1-Player & 2-Player Master Set)
│   └── plates_4color_limited/         # Batch plates strictly limited to ≤ 4 colors for 4-slot AMS
│
├── 🖨️ Printouts & Companion Game Sheets (printouts/)
│   ├── hex_game_board_1.5in.pdf       # Exact 1.5" calibrated game board with multiplier bonus hexes
│   ├── hex_games_rulebook.pdf         # Illustrated 2-page pamphlet for 5 original games
│   ├── score_sheets_and_tracker.pdf   # Multi-round score tally sheets & piece tracker
│   ├── number_hive_math_puzzles.pdf   # Target-number math challenge rosette worksheets
│   └── printouts_hub.html             # Browser-viewable print portal with @media print styling
│
├── 📜 Documentation & Guides
│   ├── PRINTING_COLOR_GUIDE.md        # Filament color recommendations & 4-slot AMS mapping
│   ├── GAMES_AND_RULES.md             # Complete rulebook for all 5 hex games
│   └── README.md                      # Master project overview & slicing manual
│
├── 🛠️ CAD Generators & Scripts
│   ├── generate_tiles.py              # Scrabble & symbol CAD generator pipeline
│   ├── generate_hive_tiles.py         # Hive insect vector CAD & plate generator
│   ├── generate_printouts.py          # Vector PDF board and rulebook generator
│   ├── hex_scrabble_tiles.scad        # Parametric OpenSCAD Customizer for Scrabble
│   └── hex_hive_tiles.scad            # Parametric OpenSCAD Customizer for Hive
```

---

## 📐 Unified Engineering Specifications

* **Flat-to-Flat Diameter**: `1.50 inches` (`38.10 mm`) — Adjacent tiles snap flush in a regular hexagonal lattice.
* **Point-to-Point Diameter**: `43.99 mm` circumcircle across opposite vertices.
* **Tile Height / Thickness**: `4.80 mm` (~3/16 inch) — Substantial weight and tactile feel.
* **Perimeter Chamfer**: `0.80 mm` ($45^\circ$) along top perimeter for smooth ergonomics.
* **Inlay Depth**: `0.80 mm` ($4$ solid layers @ $0.20\text{ mm}$ layer height) — 100% color opacity.
* **Multi-Part Architecture**: Single `.3mf` assembly containers with named sub-meshes (`Tile_Base`, `Tile_Text`, `Insects_*`).

---

## 🎨 4-Color Printer Slicing Strategy (AMS / 4-Toolhead Setup)

For printers with **up to 4 filament colors at once** (e.g. Bambu AMS 4-slot or Prusa XL 4-head), load the pre-partitioned plates from `output_hive/plates_4color_limited/`:

1. **Plate A: "Core Swarm"** (`plate_4color_A_core_swarm_7tiles.3mf`):
   - **Slot 1**: ⚪ Base (White or Black)
   - **Slot 2**: 🟡 Queen Bee (Yellow / Gold)
   - **Slot 3**: 🟢 Grasshopper (Green)
   - **Slot 4**: 🔵 Soldier Ant (Blue)
2. **Plate B: "Crawlers"** (`plate_4color_B_crawlers_4tiles.3mf`):
   - **Slot 1**: ⚪ Base (White or Black)
   - **Slot 2**: 🟤 Spider (Brown / Burnt Orange)
   - **Slot 3**: 🟣 Beetle (Purple)
3. **Plate C: "Expansions Pack"** (`plate_4color_C_expansions_3tiles.3mf`):
   - **Slot 1**: ⚪ Base (White or Black)
   - **Slot 2**: 🔴 Ladybug (Red)
   - **Slot 3**: ⚪ Mosquito (Silver / Gray)
   - **Slot 4**: 🔷 Pillbug (Cyan / Teal)

### 💡 Pro Tip: Face-Down Printing on Textured PEI
* Rotate the plate **$180^\circ$ face-down** so the top surface with the insect/letter glyphs rests directly on the build plate.
* All color swaps occur only in the **first $0.80\text{ mm}$ (layers 1 to 4)**. The remaining 20 layers print in the single base color with **zero tool swaps**!

---

## 🎮 5 Games to Play With Your Tiles

1. **Hex-Words**: Free-form tabletop crossword with 3-axis connections and the **+15 pt Honeycomb Ring Bonus**.
2. **Hive-Swarm**: Real-time speed word race. Shout *"FORAGE!"* to draw tiles from the Meadow, *"EJECT!"* to swap bad letters, and *"QUEEN'S COMB!"* to win.
3. **Number Hive / Equation Clash**: Math strategy game connecting branching equations across the 3 hex axes.
4. **Honeycomb Crossword**: Classic board game played on the printable 1.5" calibrated game board with 2L, 3L, 2W, 3W bonus multipliers.
5. **Target 24 & Rosette Math**: Daily brainteasers and solo math challenges.

See **[`GAMES_AND_RULES.md`](GAMES_AND_RULES.md)** for full rules and scoring details.

---

## 🛠️ CLI Generation Commands

```bash
# Activate environment
.venv\Scripts\activate

# Generate custom Scrabble word or letter
python generate_tiles.py --word HONEYCOMB

# Generate custom Hive tile or batch plates
python generate_hive_tiles.py --all --plates

# Regenerate printable game board and rulebook PDFs
python generate_printouts.py
```
