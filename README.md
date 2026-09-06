# BUZZLE hex-tile print library

**1.3-inch / 33.02 mm tiles · 270 × 270 mm bed · up to four colors**

## Start here

Open the **[visual print library](output/README.md)** for the current boards,
matching tile sets, pictures, file links, and quantities.

- [BUZZLE board](output/boards/buzzle/PRINT_GUIDE.md): 217 cells, seven sections.
- BUZZELLO: [Classic, 61 cells](output/boards/othello-classic/PRINT_GUIDE.md) or [Large, 91 cells](output/boards/othello/PRINT_GUIDE.md). Four sections each, STL and 3MF downloads, same 1.3-inch pieces.
- Complete BUZZELLO download bundles: [Classic STL + 3MF ZIP](docs/publishing/packages/BUZZELLO_Classic_61_STL_and_3MF.zip) · [Large STL + 3MF ZIP](docs/publishing/packages/BUZZELLO_Large_91_STL_and_3MF.zip).
- [BUZZHEX board](output/boards/buzzhex/PRINT_GUIDE.md): 11 × 11 Hex, 121 cells,
  six sections, reuses Buzzello tiles.
- [BUZZHEX website-agent prompt](docs/BUZZHEX_WEBSITE_AGENT_PROMPT.md).
- [BUZZHEX web handoff ZIP](docs/BUZZHEX_WEB_HANDOFF.zip): prompt, rules,
  coordinates, and exact yellow/black tile artwork.
- [Shared printing guide](PRINTING_COLOR_GUIDE.md): filament slots and fit checks.
- Printable play references: [BUZZLE rules](output/pdf/BUZZLE_Rules.pdf), [two-letter words](output/pdf/BUZZLE_Two_Letter_Words.pdf), and [BUZZELLO rules for both sizes](output/pdf/BUZZELLO_Rules_Classic_and_Large.pdf).
- [Development guide](docs/DEVELOPMENT.md): generation commands and validation.

All three boards include a small pocket-and-joint test. Print that first at 100%
scale; geometry checks pass, but physical fit still depends on your printer.

## Folder layout

```text
output/
  README.md                  Visual index of current print files
  boards/buzzle/             Plates, images, guide, measured manifest
  boards/othello/            Large 91-cell board: 3MFs, STLs, images, guide
  boards/othello-classic/    Classic 61-cell board: 3MFs, STLs, images, guide
  boards/buzzhex/            11 × 11 Hex board, rules contract, six plates
  tiles/                    BioBuzz, interlocking, team, Othello
  accessories/tile-holders/  Single holder and four-pack
assets/
  artwork/                  Portable source images and Othello logo geometry
  branding/                 Existing brand graphics
docs/                      Development, reference coordinates, maintenance records
archive/                    Superseded models, experiments, older printouts
```

The obsolete 1.5-inch tile exports were deleted. Current tile generators and
OpenSCAD templates default to 33.02 mm. Older paper printouts, reference
images, and board designs are clearly separated in the [archive](archive/README.md).

## Rebuild

With the [Python dependencies installed](docs/DEVELOPMENT.md):

```powershell
python generate_board_270.py
python generate_othello_board_270.py
python -m unittest test_board_270 test_othello_board_270 -v
python build_output_catalog.py
python verify_output_library.py
```

The [217-cell coordinate specification](BUZZLE_217_BOARD_SPECIFICATION.md)
and [existing game-rule notes](GAMES_AND_RULES.md) remain available for reference.

[Snapmaker / Printables color import help](docs/3MF_COLOR_IMPORT.md) — updated surface colors, named parts, and filament slots.
