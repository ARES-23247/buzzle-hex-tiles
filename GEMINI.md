# Project context

- All current game tiles, including Scrabble, are **1.3 inches / 33.02 mm across flats**.
- Current board print bed: **270 × 270 mm**. At most four filaments.
- BUZZLE palette: black, white, blue, yellow. Othello board: black/yellow; pieces: black/yellow. Word tiles: yellow/black.
- Entry point: `output/README.md`; current files live under `output/boards/`,
  `output/tiles/`, and `output/accessories/`.
- BUZZLE generator: `generate_board_270.py` → `output/boards/buzzle/` (217 cells, seven sections).
- BUZZELLO generator: `generate_othello_board_270.py --size both` produces Classic (61 cells) in `output/boards/othello-classic/` and Large (91 cells) in `output/boards/othello/`; four sections each.
- `export_buzzello_stls.py` produces solid single-color and aligned Black/Yellow STL variants for both editions.
- Current printable rules and the two-letter word reference are in `output/pdf/`.
- Each board folder has `plates/`, `images/`, `PRINT_GUIDE.md`, and `print_manifest.json`.
- `build_output_catalog.py` refreshes the visual index, tile images/guides, and plate checklists.
- Validate with `python -m unittest test_board_270 test_othello_board_270 -v`
  and `python verify_output_library.py`.
- Keep portable source assets in `assets/artwork/`; historical files belong in `archive/`.
- Legacy 1.5-inch tile exports were deleted. Do not recreate them by default.
- See `docs/DEVELOPMENT.md` for commands and `docs/maintenance/` for cleanup records.
