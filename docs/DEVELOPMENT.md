# Generate and maintain the print library

Run commands from the repository root. Tile size is **33.02 mm / 1.3 inches**
across flats. The current boards target a **270 × 270 mm bed** and at most
four filaments. Keep those dimensions unless the user explicitly changes them.

## Current generators

| Command | Output |
|---|---|
| `python generate_board_270.py` | `output/boards/buzzle/` |
| `python generate_othello_board_270.py` | `output/boards/othello/` |
| `python generate_biobuzz_tiles.py --plates` | `output/tiles/biobuzz/` |
| `python generate_interlocking_logo_tiles.py --plates` | `output/tiles/interlocking/` |
| `python generate_team_tiles.py --plates` | `output/tiles/team/` |
| `python generate_tiles.py --word BUZZLE` | `output/tiles/plain/` |
| `python generate_hive_tiles.py --all --plates` | `output/tiles/hive/` |
| `python build_output_catalog.py` | Visual index, tile previews/guides, board checklists |

The tile generators also accept `--outdir` for an isolated output directory.
The OpenSCAD files default to 33.02 mm. Existing tile plate names retain
`plate_256` because their layout was not repacked during organization.

Install the project's Python dependencies in a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

This workspace also has an ignored `.board-deps/` installation used for the
board work. To reuse it in PowerShell:

```powershell
$env:PYTHONPATH = "$PWD/.board-deps"
$env:MPLCONFIGDIR = "$PWD/.mplconfig"
```

## Verification

```powershell
python generate_board_270.py
python generate_othello_board_270.py
python three_mf_colors.py
python -m unittest test_board_270 test_othello_board_270 test_three_mf_colors -v
python build_output_catalog.py
python verify_output_library.py
```

Board tests cover cells, pocket fit, joint clearance, material volumes,
watertight exported meshes, XML, palette, and bed/tower clearance. Library
verification checks current guide/image/model links and manifests. Rebuilding
the library does not imply that the models have been physically printed.

## Source assets and history

- `assets/artwork/` holds portable team/interlocking logo images and the
  original Othello underside artwork as GeoJSON. Regeneration no longer
  depends on a user's external upload directory or an old board master.
- `assets/branding/` retains the earlier vector/raster brand assets.
- `docs/reference/buzzle/` holds the existing coordinate exports.
- `archive/` holds superseded board models, old reference images, and older
  rules/printouts. Its 1.5-inch paper board is not for current tiles.
- `docs/maintenance/` records the earlier oversized-tile deletion and this
  folder migration, including hashes of files at the time of the move.

`generate_buzzle_rosette_board.py` and `render_new_buzzle_board.py` still supply
shared geometry/export helpers. Their old standalone board outputs are routed
to the archive. `generate_board.py` and `generate_printouts.py` describe legacy
workflows; they are not the commands for current printable boards.

Keep one canonical copy of each tile plate. The Othello 30-piece plate is
intentionally printed twice rather than stored under two identical filenames.

The shared `three_mf_colors.py` helper adds triangle colors, named base materials,
and Snapmaker/Orca part settings without changing geometry. The board and word-tile
exporters call it automatically. Run its standalone command to update retained
tile files without regenerating their meshes. See [color import notes](3MF_COLOR_IMPORT.md).
