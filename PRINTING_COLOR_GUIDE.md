# Printing guide for the current library

[Open the visual print library](output/README.md)

**All current tiles use 1.3 inches / 33.02 mm across flats.** Keep models at
100% scale. Use a 270 × 270 mm printer profile for the new board plates.

## Current color slots

| Model | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|---|---|---|---|---|
| BUZZLE board | Black base, labels, ribs | White caps, DW/KEY/start | Blue DL/TL | Yellow TW |
| Othello board | Black frame, markers, rings | Yellow floors, joint tops, underside logo | — | — |
| BUZZHEX board | Black base, grid, A/K goal rails | Yellow 1/11 goal rails | White pocket floors and joint tops | — |
| Word tiles | Yellow bodies | Black lettering/logos | — | — |
| Othello pieces | Black | Yellow | — | — |

The updated 3MFs include visible surface colors and explicit filament assignments.
Read the [Snapmaker and Printables color import guide](docs/3MF_COLOR_IMPORT.md).
Import each file as one multipart assembly. Part names include their slot and
color; the material preset dropdown (such as `Dave PETG`) remains your choice.

## What to print

| Item | Files/quantity | Instructions |
|---|---|---|
| BUZZLE board | Seven numbered plates, once each | [Board guide](output/boards/buzzle/PRINT_GUIDE.md) |
| Othello board | Four numbered plates, once each | [Board guide](output/boards/othello/PRINT_GUIDE.md) |
| BUZZHEX board | Six numbered plates, once each; 121 reversible tiles | [Board guide](output/boards/buzzhex/PRINT_GUIDE.md) |
| BioBuzz word tiles | Four Scrabble plates for 100, or six Hive-Swarm plates for 144 | [Tile guide](output/tiles/biobuzz/PRINT_GUIDE.md) |
| Interlocking word tiles | Same set quantities | [Tile guide](output/tiles/interlocking/PRINT_GUIDE.md) |
| Team word tiles | Same set quantities | [Tile guide](output/tiles/team/PRINT_GUIDE.md) |
| Othello pieces | One 30-piece plate printed twice gives 60 | [Piece guide](output/tiles/othello/PRINT_GUIDE.md) |
| Tile holders | Single holder or four-pack | [Holder guide](output/accessories/tile-holders/PRINT_GUIDE.md) |

Plain letter and Hive insect exports are currently absent because their old
1.5-inch files were removed. Their generators now default to the intended
33.02 mm size; generation commands are in the [development guide](docs/DEVELOPMENT.md).

## Board fit and orientation

Print the pocket-and-joint test supplied with each board before the full set.
BUZZLE pockets are 33.8 mm across flats; Othello pockets retain 33.5 mm.
Both accept the intended 33.02 mm pieces, with different nominal clearances.

The September 5 **v2_sturdy** revision uses **2.2 mm dividers** and **2.8 mm floors**
on both boards. BUZZLE has 3 mm pockets and a 5.8 mm total height; Othello has
2.4 mm pockets and a 5.2 mm total height. The guides include before/after images.
Wider cell spacing means current sections will not align with earlier prints.
Print a complete new set, or use the [saved earlier sets](archive/printed-revisions/2026-09-05-before-thicker-boards/README.md)
to match an existing board.

Print boards flat, pockets upward, at 0.20 mm layer height with a 0.20 mm first
layer. Do not apply face-down tile instructions to the recessed boards.
The supplied board placements allow a 40 × 40 mm purge tower at
X=225–265, Y=225–265. Adding a larger tower, a brim, or automatic arrangement
requires checking clearance in the slicer again.

The numbered board exports pass geometry, material, and bed-clearance tests.
They are model files, not sliced printer jobs, and have not been physically
printed here. Retained tile/accessory exports were organized without resizing.

## Historical materials

Old board experiments and older paper rulebooks/printouts are in the
[archive](archive/README.md). Their dimensions, links, and print quantities
may differ from the current library. Do not choose current print files from there.
