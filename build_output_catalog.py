"""Refresh the visual output index and tile previews from the actual 3MF files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'output'
IVORY, CHARCOAL = '#F2EADB', '#23272B'


def render_tile(source, destination, title):
    with zipfile.ZipFile(source) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
    triangles, heights, colors = [], [], []
    for obj in model.findall('.//{*}object'):
        if obj.find('{*}mesh') is None:
            continue
        resource = model.find(f'.//{{*}}basematerials[@id="{obj.get("pid")}"]')
        if resource is None:
            raise ValueError(f'Missing embedded display colors: {source}')
        color = list(resource)[int(obj.get('pindex'))].get('displaycolor')[:7]
        vertices = np.array([[float(v.get(a)) for a in 'xyz'] for v in obj.findall('.//{*}vertex')])
        faces = np.array([[int(f.get(a)) for a in ['v1', 'v2', 'v3']] for f in obj.findall('.//{*}triangle')])
        for points in vertices[faces]:
            cross = np.cross(points[1]-points[0], points[2]-points[0])
            if abs(cross[2]) < 1e-8:
                continue
            triangles.append(points[:, :2]); heights.append(points[:, 2].mean()); colors.append(color)
    triangles = np.array(triangles); colors = np.array(colors)
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.6))
    fig.set_facecolor('#141619')
    for ax, direction, caption in zip(axes, [1, -1], ['Front', 'Back']):
        order = np.argsort(np.array(heights)*direction, kind='stable')
        faces = triangles[order].copy()
        if direction == -1:
            faces[:, :, 0] *= -1
        ax.add_collection(PolyCollection(faces, facecolors=colors[order], edgecolors='none', antialiased=False))
        ax.set_xlim(-23, 23); ax.set_ylim(-21, 21); ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(caption, color='white', fontsize=12)
    fig.suptitle(f'{title} · 1.3-inch / 33.02 mm', color='white', fontsize=14)
    fig.text(.5, .035, 'Orthographic preview from the supplied 3MF geometry', color='#B7BCC0', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .07, 1, .9))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=150, facecolor=fig.get_facecolor()); plt.close(fig)


def tile_guide(family, title, source):
    folder = OUTPUT/'tiles'/family
    render_tile(folder/'3mf'/source, folder/'images/tile_front_back.png', title)
    plates = sorted((folder/'plates').glob('*.3mf'))
    text = f'''# {title}

**1.3 inches / 33.02 mm across flats. Print at 100% scale.**

![Front and back](images/tile_front_back.png)

The retained geometry is unchanged. Colors and explicit filament-slot labels
are now embedded in the 3MF files. Word tiles use yellow bodies with black
lettering/logos; Othello pieces use black and yellow.
Read the [color import guide](../../../docs/3MF_COLOR_IMPORT.md) before importing.

## Individual files

'''
    for p in sorted((folder/'3mf').glob('*.3mf')):
        text += f'- [{p.name}](3mf/{p.name})\n'
    text += '\n## Batch plates\n\n'
    if family == 'othello':
        text += 'Both BUZZELLO sizes use these same pieces. For **Classic (61 cells)**,\nprint the 30-piece batch twice plus one single. For **Large (91 cells)**, print\nit three times plus one single. If you already have 60 pieces, add one single\nfor Classic, or one batch plus one single for Large. The legacy filename\n`plate_30_pieces_print_twice.3mf` contains 30 pieces; use the quantities above.\n\n'
    else:
        text += 'Choose one set: print each of the four **Scrabble** plates once for 100\ntiles, or each of the six **Hive-Swarm** plates once for 144 tiles. The numbers\nand math plate is a separate 26-tile collection. Do not print both word sets\nunless you want both quantities. Files named `plate_256` retain their existing\nlayout; check placement and purge-tower space in your 270 mm slicer profile.\n\n'
    for p in plates:
        text += f'- [{p.name}](plates/{p.name})\n'
    text += '\nThe tile exports were retained and organized; they have not been re-sliced or\nphysically validated in this cleanup. The preview is a top/bottom geometry view.\n'
    (folder/'PRINT_GUIDE.md').write_text(text, encoding='utf-8')


def build():
    for family, title, source in [
        ('biobuzz', 'BioBuzz word tiles', 'tile_doublesided_biobuzz_A_score1.3mf'),
        ('interlocking', 'Interlocking-logo word tiles', 'tile_doublesided_interlocking_A_score1.3mf'),
        ('team', 'Team token and word sets', 'tile_team_spartan_token.3mf'),
        ('othello', 'Othello reversible pieces', 'hex_othello_piece_single.3mf'),
    ]:
        tile_guide(family, title, source)
    text = '''# Print library

**Start here. All current tiles are 1.3 inches / 33.02 mm across flats.**
Boards are arranged for a **270 × 270 mm bed** and use at most **four colors**.

**Colors:** yellow/black word tiles; black/yellow Othello board with black/yellow
pieces; black/white/blue/yellow BUZZLE board. The corrected 3MFs include surface
colors, named parts, and filament-slot assignments.
[Snapmaker and Printables import help](../docs/3MF_COLOR_IMPORT.md).

Both boards use sturdy dimensions: **2.2 mm dividers**, **2.8 mm floors**,
and deeper pockets. BUZZLE is 5.8 mm tall with 3 mm pockets; Othello is 5.2 mm tall
with 2.4 mm pockets. Tile sizes are unchanged. Print a complete new set because
the wider cell spacing will not align with earlier board sections.

Both boards retain **0.40 mm tab/socket clearance** and a
**0.30 mm seam gap** to reduce binding. Print its revised fit test first;
physical fit verification is pending.

1. Choose a board below and read its print guide.
2. Print its small pocket-and-joint test first.
3. Print the numbered board plates at 100% scale, then choose a matching tile set.

## BUZZLE · 217 cells · 7 sections

![BUZZLE board and bed layout](boards/buzzle/images/board_and_bed_preview.png)

[Print guide](boards/buzzle/PRINT_GUIDE.md) · [Fit-test 3MF](boards/buzzle/plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf) · [Plates](boards/buzzle/plates/)

## BUZZELLO · Preferred Large 91 and Classic 61 · 4 sections each

We prefer the 91-cell board — it plays better. Large is the default edition;
Classic remains available as the smaller alternative.

| Edition | Cells | Assembled size | Files |
|---|---:|---|---|
| Large (preferred) | 91 | 351.8 × 394.1 mm | [Guide and 3MFs](boards/othello/PRINT_GUIDE.md) · [STLs](boards/othello/stl/README.md) |
| Classic | 61 | 289.9 × 322.7 mm | [Guide and 3MFs](boards/othello-classic/PRINT_GUIDE.md) · [STLs](boards/othello-classic/stl/README.md) |

![Othello board and bed layout](boards/othello/images/board_and_bed_preview.png)

[Print guide](boards/othello/PRINT_GUIDE.md) · [Fit-test 3MF](boards/othello/plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf) · [Reversible pieces](tiles/othello/PRINT_GUIDE.md)

The Large board adds a 30-cell outer ring around the original 61 cells. It uses
the same 1.3-inch pieces and four larger sections. Print all four as a matching
set. For 91 pieces, print the 30-piece batch three times plus one single.

## BUZZHEX · 11 × 11 Hex · 121 cells · 6 sections

![BUZZHEX board and bed layout](boards/buzzhex/images/board_and_bed_preview.png)

[Print guide](boards/buzzhex/PRINT_GUIDE.md) · [Fit-test 3MF](boards/buzzhex/plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf) · [Game rules](../docs/BUZZHEX_RULES.md) · [Website-agent prompt](../docs/BUZZHEX_WEBSITE_AGENT_PROMPT.md)

Uses the same 33.02 mm black/yellow reversible tiles as Buzzello. For a full
121-tile supply, print the existing 30-piece plate four times plus one single;
if you already have 60, add two 30-piece plates and one single. Board colors:
black/yellow goal rails and white pocket floors. Six sections retain 2.8 mm floors, 2.4 mm pockets,
0.40 mm socket clearance, and a 0.30 mm seam gap.

## Matching tile sets

| Set | Image | Guide |
|---|---|---|
'''
    for family, title in [('biobuzz','BioBuzz'),('interlocking','Interlocking logo'),('team','Team'),('othello','Othello')]:
        text += f'| {title} | ![{title}](tiles/{family}/images/tile_front_back.png) | [Files and quantities](tiles/{family}/PRINT_GUIDE.md) |\n'
    text += '''
## Accessories and reference

- [Seven-tile holders](accessories/tile-holders/PRINT_GUIDE.md)
- [Shared printing guide](../PRINTING_COLOR_GUIDE.md)
- [Development and regeneration](../docs/DEVELOPMENT.md)
- [Archived designs and old printouts](../archive/README.md)

Plain letter and Hive insect exports are not currently included: their obsolete
1.5-inch files were removed. Their generators now default to 33.02 mm; see the
development guide to generate fresh sets.

Every board folder contains `plates/`, `images/`, `PRINT_GUIDE.md`, and
`print_manifest.json`. Choose files from this library, not from the archive.
Board geometry/export checks pass; physical fit still needs the test print.
'''
    (OUTPUT/'README.md').write_text(text, encoding='utf-8')
    for family in ['buzzle','othello','othello-classic','buzzhex']:
        folder = OUTPUT/'boards'/family
        manifest = json.loads((folder/'print_manifest.json').read_text())
        table = '\n## Plate checklist\n\n| File | Cells | Width × depth |\n|---|---:|---:|\n'
        for p in manifest['plates']:
            table += f"| [{Path(p['file']).name}]({p['file']}) | {p['cells']} | {p['width_mm']:.1f} × {p['height_mm']:.1f} mm |\n"
        guide = (folder/'PRINT_GUIDE.md').read_text(encoding='utf-8').split('\n## Plate checklist')[0]
        (folder/'PRINT_GUIDE.md').write_text(guide.rstrip()+'\n'+table, encoding='utf-8')
    print('Updated output/README.md, four tile guides/previews, and four board checklists.')


if __name__ == '__main__':
    build()
