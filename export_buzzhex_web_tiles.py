"""Export exact top/bottom surface artwork from the existing Buzzello tile 3MF."""
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from shapely.affinity import scale
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'output/tiles/othello/3mf/hex_othello_piece_single.3mf'
OUTPUT = ROOT/'assets/artwork/buzzhex'


def svg_path(poly):
    parts = []
    for p in [poly] if isinstance(poly, Polygon) else poly.geoms:
        for ring in [p.exterior]+list(p.interiors):
            coords = list(ring.coords)
            parts.append('M'+' L'.join(f'{x:.5f},{y:.5f}' for x, y in coords)+' Z')
    return ' '.join(parts)


def generate():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE) as archive:
        root = ET.fromstring(archive.read('3D/3dmodel.model'))
    if [base.get('displaycolor') for base in root.findall('.//{*}base')] != ['#000000FF', '#FFFF00FF']:
        raise ValueError('Expected the shared black/yellow reversible tile palette')
    for name, z, mirror in [('yellow', 4.8, 1), ('black', 0.0, -1)]:
        surfaces = {0: [], 1: []}
        for obj in root.findall('.//{*}object'):
            if obj.find('{*}mesh') is None:
                continue
            vertices = [[float(v.get(a)) for a in 'xyz'] for v in obj.findall('.//{*}vertex')]
            for face in obj.findall('.//{*}triangle'):
                points = [vertices[int(face.get(a))] for a in ['v1', 'v2', 'v3']]
                if all(abs(p[2]-z) < 1e-5 for p in points):
                    poly = Polygon([(p[0], p[1]) for p in points])
                    if poly.area > 1e-8:
                        surfaces[int(obj.get('pindex'))].append(poly)
        shapes = {i: scale(unary_union(polys), xfact=mirror, yfact=-1, origin=(0, 0)) for i, polys in surfaces.items()}
        silhouette = unary_union(list(shapes.values()))
        if abs(silhouette.area-(33.02**2*3**.5/2)) > .01:
            raise ValueError('Tile surface does not cover the expected hexagon')
        paths = '\n'.join(f'<path fill="{["#000000", "#FFFF00"][i]}" fill-rule="evenodd" d="{svg_path(p)}"/>' for i, p in shapes.items())
        text = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -18 40 36" role="img" aria-label="{name.capitalize()} Buzzello tile"><title>{name.capitalize()} Buzzello tile</title>\n{paths}\n</svg>\n'
        (OUTPUT/f'buzzello-tile-{name}.svg').write_text(text, encoding='utf-8')
    (OUTPUT/'README.md').write_text('''# Exact Buzzello tile artwork for BUZZHEX

These SVGs are orthographic projections of the existing reversible tile's
outermost mesh surfaces, including its real BioBuzz rosette artwork.
The black face is viewed from below with its X axis mirrored; both SVGs use
screen coordinates. The tile remains 33.02 mm across flats and 4.8 mm thick.

- [Black face](buzzello-tile-black.svg)
- [Yellow face](buzzello-tile-yellow.svg)
- [Original 3MF](../../../output/tiles/othello/3mf/hex_othello_piece_single.3mf)

Regenerate with `python export_buzzhex_web_tiles.py`. Keep the internal
black/yellow rosette exactly as supplied; the large background color identifies
the owner. Do not replace these tiles with circular stones or a bee emoji.
''', encoding='utf-8')


if __name__ == '__main__':
    generate()
