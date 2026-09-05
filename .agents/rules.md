# BUZZLE project rules and output layout

- All current tiles, including Scrabble, are 1.3 inches / 33.02 mm across flats.
- Board printer: 270 x 270 mm bed, at most four filaments.
- BUZZLE slots: black, white, blue, yellow. Othello board: black/yellow; pieces: black/white. Word tiles: yellow/black.
- Current print-library entry point: output/README.md.
- BUZZLE: generate_board_270.py -> output/boards/buzzle/ (217 cells, seven sections).
- Othello: generate_othello_board_270.py -> output/boards/othello/ (61 cells, four sections).
- Board folders contain plates/, images/, PRINT_GUIDE.md, and print_manifest.json.
- Tile families live in output/tiles/; holders live in output/accessories/tile-holders/.
- Portable logos and vector artwork live in assets/artwork/.
- Historical models, earlier images, and old paper printouts belong in archive/.
- Do not recreate the deleted 1.5-inch tile exports or the former output_* folders by default.
- Refresh images/guides with python build_output_catalog.py.
- Validate with python -m unittest test_board_270 test_othello_board_270 test_three_mf_colors -v
  and python verify_output_library.py.
- Read docs/DEVELOPMENT.md for regeneration commands and dependency setup.
- The approved BUZZLE scoring coordinates remain in BUZZLE_217_BOARD_SPECIFICATION.md.
