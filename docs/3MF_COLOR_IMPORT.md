# Color files for Snapmaker Orca and Printables

The September 5 color fix adds **surface colors, named parts, and explicit
filament assignments**. Earlier word-tile files had separate meshes but no
color properties. Earlier board files stored display colors and core object
names, but omitted the part settings that Snapmaker uses for its object list.

## Current colors

| Model | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|---|---|---|---|---|
| Word tiles | Yellow body | Black lettering/logo | — | — |
| BUZZLE/Scrabble board | Black base, labels, rib bodies | White grid caps, DW/KEY/start | Blue DL/TL | Yellow TW |
| Othello board | Black frame, starting markers, corner rings | Yellow floors, joint tops, underside logo | — | — |
| Reversible Othello pieces | Black side/inlays | White side/inlays | — | — |

Tile dimensions, deeper pockets, thicker dividers, and board joints are unchanged
by this color fix. [Choose files from the current print library](../output/README.md).

## In Snapmaker Orca

1. Import the **updated** 3MF into a fresh project. A model already in an open
   project will not update when its source file changes.
2. Keep the model as one multipart assembly. Expand its object row to see parts
   named, for example, `[Slot 1 - Yellow] Tile_Base` and
   `[Slot 2 - Black] Tile_Graphics`.
3. Check the filament column against the table above. Explicit per-part slot
   numbers are now included in the file; mesh-only imports can still retain
   existing project swatches in some slicer versions. If needed, set those
   swatches to the listed colors and assign parts by their labels.
4. Keep your Snapmaker U1 printer and your calibrated filament presets. The
   file sets colors, not temperatures, speeds, or a printer profile. `Dave PETG`
   is the material preset name in your screenshot; that dropdown is separate
   from the part labels and filament color swatches.
5. Slice and inspect the colored preview before printing. Save your finished
   slicer project to preserve your own printer/material configuration.

For Othello, expect black ribs and marks on yellow pocket floors. For word tiles,
expect yellow bodies with black text and logos. Both need only two slots.

## On Printables

Replace the earlier uploaded file with the **updated 3MF**. The corrected file
includes a color on every triangle, plus named base materials with display colors,
so a viewer does not have to infer colors from the slicer's filament settings.
The separate PNG previews in each model's `images/` folder can also be uploaded
as listing images. An existing uploaded file or cached preview will not change
just because the local source file was replaced.

Printables' live upload/preview has not been tested in this workspace. Its preview
is not a check of the printer's tool assignments; check the sliced preview too.

## Verification and implementation references

Automated checks inspect every current board/tile's face colors, material
references, part names, slot assignments, and palette. Board geometry tests still
apply. Snapmaker and Orca command-line validation both failed at application
startup with Windows access-violation exit code 0xC0000005; no successful slicer
round trip is claimed.

- [Snapmaker's 3MF importer/exporter](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/libslic3r/Format/bbs_3mf.cpp)
  reads part `name` and `extruder` metadata from `Metadata/model_settings.config`
  and filament colors from `Metadata/project_settings.config`.
- [Snapmaker's project import handling](https://github.com/Snapmaker/OrcaSlicer/blob/main/src/slic3r/GUI/Plater.cpp)
  separates project configuration, geometry import, and filament assignments.
- [3MF Material Extension specification](https://github.com/3MFConsortium/spec_materials)
  defines color groups and triangle properties.
- [Printables color-tool source](https://github.com/seasick/3mf-color-changer/blob/main/src/utils/3mf/changeColors.ts)
  writes triangle-level color references for model previews.

Regenerate with the board generators and `python three_mf_colors.py` for the
retained tile files, then run `python build_output_catalog.py` and
`python -m unittest test_board_270 test_othello_board_270 test_three_mf_colors -v`.
