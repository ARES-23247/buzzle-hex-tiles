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
        name = obj.get('name', '')
        color = IVORY if ('Ivory' in name or 'Base' in name) else CHARCOAL
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

These are the retained tile exports; their geometry was not resized during
the folder cleanup. Import each 3MF as a single assembly and assign its named
parts to filaments. The board's four-filament palette includes ivory and
charcoal, which can also be used for these two-color tiles.

## Individual files

'''
    for p in sorted((folder/'3mf').glob('*.3mf')):
        text += f'- [{p.name}](3mf/{p.name})\n'
    text += '\n## Batch plates\n\n'
    if family == 'othello':
        text += 'The two old 30-piece plates were byte-for-byte identical. Use the single\nplate below twice for 60 reversible pieces. Use the single-piece file for extras.\n\n'
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

Both boards now use the **v2_sturdy** design: **2.2 mm dividers**, **2.8 mm floors**,
and deeper pockets. BUZZLE is 5.8 mm tall with 3 mm pockets; Othello is 5.2 mm tall
with 2.4 mm pockets. Tile sizes are unchanged. Print a complete new set because
the wider cell spacing will not align with earlier board sections.

1. Choose a board below and read its print guide.
2. Print its small pocket-and-joint test first.
3. Print the numbered board plates at 100% scale, then choose a matching tile set.

## BUZZLE · 217 cells · 7 sections

![BUZZLE board and bed layout](boards/buzzle/images/board_and_bed_preview.png)

[Print guide](boards/buzzle/PRINT_GUIDE.md) · [Fit-test 3MF](boards/buzzle/plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf) · [Plates](boards/buzzle/plates/)

## Othello · 61 cells · 4 sections

![Othello board and bed layout](boards/othello/images/board_and_bed_preview.png)

[Print guide](boards/othello/PRINT_GUIDE.md) · [Fit-test 3MF](boards/othello/plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf) · [Reversible pieces](tiles/othello/PRINT_GUIDE.md)

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
    for family in ['buzzle','othello']:
        folder = OUTPUT/'boards'/family
        manifest = json.loads((folder/'print_manifest.json').read_text())
        table = '\n## Plate checklist\n\n| File | Cells | Width × depth |\n|---|---:|---:|\n'
        for p in manifest['plates']:
            table += f"| [{Path(p['file']).name}]({p['file']}) | {p['cells']} | {p['width_mm']:.1f} × {p['height_mm']:.1f} mm |\n"
        guide = (folder/'PRINT_GUIDE.md').read_text(encoding='utf-8').split('\n## Plate checklist')[0]
        (folder/'PRINT_GUIDE.md').write_text(guide.rstrip()+'\n'+table, encoding='utf-8')
    print('Updated output/README.md, four tile guides/previews, and both board checklists.')


if __name__ == '__main__':
    build()
