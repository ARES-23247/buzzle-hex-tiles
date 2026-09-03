# Hex-Tiles & BUZZLE 3D Project Context

## Overview
This repository contains the multi-material 3D printable parametric CAD generators, 3MF plate configurations, vector rulebooks, and developer specifications for:
- **BUZZLE™ 217-Cell 4-Color Board Suite** (Snapmaker Orca / Bambu AMS, 7 plates: 1 Central Rosette Hub + 6 Wedges)
- **Hex Scrabble Tiles & Math System** (1.5" / 38.1mm tiles with embossed letters and point values)
- **Hive Insect Tile Sets** (Dual-color & 4-color limited)

## Key Files & Structure
- `generate_buzzle_rosette_board.py`: Parametric OpenSCAD / 3MF generator for the official 217-cell board with embedded `<m:colorgroup>` 4-color AMS profiles.
- `output/board/3mf/`: Slicer-ready plates labeled with explicit Snapmaker Orca slot IDs (`[Slot 1 - Charcoal]`, `[Slot 2 - Lime]`, `[Slot 3 - Pink]`, `[Slot 4 - Cyan]`).
- `BUZZLE_217_BOARD_SPECIFICATION.md`: Master mathematical and coordinate specification for developers and game engine implementations.
- `output/board/buzzle_217_spec.json`: Machine-readable JSON definition of all 217 cells.

## Slicer Standards
- Slicer: Snapmaker Orca / OrcaSlicer / Bambu Studio
- Bed Volume: 256 x 256 mm
- Layer Height: 0.20mm standard, first layer 0.20mm
- Multi-material inlays: 0.80mm inlay thickness flush with top floor
