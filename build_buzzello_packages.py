"""Package the current BUZZELLO editions for Printables after CAD/STL export."""
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGES = ROOT / "docs/publishing/packages"


def main():
    PACKAGES.mkdir(parents=True, exist_ok=True)
    for edition, count, folder in [("Classic", 61, "othello-classic"), ("Large", 91, "othello")]:
        board = ROOT / "output/boards" / folder
        target = PACKAGES / f"BUZZELLO_{edition}_{count}_STL_and_3MF.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for source in sorted(board.rglob("*")):
                if source.is_file():
                    bundle.write(source, source.relative_to(board).as_posix())
            for source in [ROOT / "output/tiles/othello/3mf/hex_othello_piece_single.3mf",
                           ROOT / "output/tiles/othello/plates/plate_30_pieces_print_twice.3mf"]:
                bundle.write(source, "pieces/" + source.name)
            bundle.write(ROOT / "output/pdf/BUZZELLO_Rules_Classic_and_Large.pdf",
                         "BUZZELLO_Rules_Classic_and_Large.pdf")
            bundle.writestr("START_HERE.txt", f"""BUZZELLO {edition}: {count} playable cells
Revision v5: black floors and yellow raised hex dividers.
Print at 100% scale in millimeters. Existing 33.02 mm / 1.3-inch pieces fit.
Print the pocket-and-joint test first, then each of the four sections once.
Black: foundation, pocket floors and joint tops.
Yellow: full-depth dividers (3.2 mm), starting markers, corner rings and underside artwork.
Geometry and joint tolerances are unchanged from the prior edition.
3MF preserves aligned color parts. STL cannot store colors: assign Black and Yellow
to the matching color-part STLs imported together as one assembly.
Use either single-color STLs or color-part STLs, not both together.
Full piece supply: print the shared 30-piece batch {count // 30} times plus one single.
Read PRINT_GUIDE.md and the included PDF rules before printing and playing.
Play online: https://aresfirst.org/buzzello
""")
        with zipfile.ZipFile(target) as check:
            assert check.testzip() is None
            assert len([n for n in check.namelist() if n.endswith(".stl")]) == 15
            assert len([n for n in check.namelist() if n.endswith(".3mf")]) == 7
        shutil.copyfile(board / "images/board_and_bed_preview.png",
                        PACKAGES / f"BUZZELLO_{edition}_{count}_v5.png")
        print(f"Verified {target.name}: {target.stat().st_size:,} bytes")
    guides = PACKAGES / "othello"
    guides.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "output/boards/othello-classic/PRINT_GUIDE.md", guides / "BOARD_PRINT_GUIDE.txt")
    shutil.copyfile(ROOT / "docs/3MF_COLOR_IMPORT.md", guides / "COLOR_IMPORT_GUIDE.txt")


if __name__ == "__main__":
    main()
