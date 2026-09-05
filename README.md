# BUZZLE hex-tile print library

**1.3-inch / 33.02 mm tiles · 270 × 270 mm bed · four-color boards**

## Start here

Open the **[visual print library](output/README.md)** for the current boards,
matching tile sets, pictures, file links, and quantities.

- [BUZZLE board](output/boards/buzzle/PRINT_GUIDE.md): 217 cells, seven sections.
- [Othello board](output/boards/othello/PRINT_GUIDE.md): 61 cells, four sections.
- [Shared printing guide](PRINTING_COLOR_GUIDE.md): filament slots and fit checks.
- [Development guide](docs/DEVELOPMENT.md): generation commands and validation.

Both boards include a small pocket-and-joint test. Print that first at 100%
scale; geometry checks pass, but physical fit still depends on your printer.

## Folder layout

```text
output/
  README.md                  Visual index of current print files
  boards/buzzle/             Plates, images, guide, measured manifest
  boards/othello/            Plates, images, guide, measured manifest
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
