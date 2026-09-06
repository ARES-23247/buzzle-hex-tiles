"""Create watertight single-color and aligned color-part STLs for both editions."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

ROOT = Path(__file__).resolve().parent


def export_board(folder):
    records = []
    for source in sorted((folder / 'plates').glob('*.3mf')):
        with zipfile.ZipFile(source) as archive:
            root = ET.fromstring(archive.read('3D/3dmodel.model'))
        groups = {0: [], 1: []}
        for obj in root.findall('.//{*}object'):
            if obj.find('{*}mesh') is None:
                continue
            vertices = [[float(v.get(a)) for a in 'xyz'] for v in obj.findall('.//{*}vertex')]
            faces = [[int(t.get(a)) for a in ['v1','v2','v3']] for t in obj.findall('.//{*}triangle')]
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
            if not mesh.is_volume:
                raise ValueError(f'Non-solid source part in {source}')
            groups[int(obj.get('pindex'))].append(mesh)
        meshes = groups[0] + groups[1]
        variants = [('single-color', '', meshes)] + [
            ('color-parts', '_' + name, groups[i])
            for i, name in enumerate(['Black','Yellow']) if groups[i]
        ]
        for directory, suffix, parts in variants:
            # Union removes internal faces between touching foundation/inlay layers.
            merged = trimesh.boolean.union(parts, engine='manifold')
            # Binary STL uses float32 coordinates. Remove sub-micron slivers
            # before that conversion so coincident vertices cannot open seams.
            solid = Manifold(Mesh(np.asarray(merged.vertices, dtype=np.float32),
                                  np.asarray(merged.faces, dtype=np.uint32)))
            simplified = solid.simplify(0.001).to_mesh()
            merged = trimesh.Trimesh(vertices=simplified.vert_properties[:, :3],
                                     faces=simplified.tri_verts, process=False)
            if not merged.is_volume:
                raise ValueError(f'Non-solid STL union: {source.name}{suffix}')
            destination = folder / 'stl' / directory / (source.stem + suffix + '.stl')
            destination.parent.mkdir(parents=True, exist_ok=True)
            merged.export(destination)
            loaded = trimesh.load_mesh(destination)
            expected_volume = sum(p.volume for p in parts)
            if not loaded.is_volume or not np.isclose(loaded.volume, expected_volume, rtol=1e-4):
                raise ValueError(f'STL volume changed: {destination}')
            if not np.allclose(loaded.bounds, trimesh.util.concatenate(parts).bounds, atol=0.001):
                raise ValueError(f'STL bounds changed: {destination}')
            records.append({'file': destination.relative_to(folder).as_posix(),
                            'volume_mm3': round(loaded.volume, 3), 'watertight': loaded.is_watertight})
        print(folder.name, source.name, '3 STL variants verified', flush=True)
    (folder / 'stl' / 'export_manifest.json').write_text(json.dumps(records, indent=2)+'\n')
    (folder / 'stl' / 'README.md').write_text(
        '# STL printing\n\nPrint at 100% scale in millimeters. Use either the single-color file or the\n'
        'matching Black and Yellow color-part files, never both sets together.\n'
        'STL stores geometry only. For two-color printing, import both color parts\n'
        'as one multipart object, keep their original shared coordinates, and assign\n'
        'black/yellow filaments manually. Do not center or drop each part separately.\n'
        'The 3MF files in ../plates already preserve this alignment and color metadata.\n'
        'Flush color markings disappear in the single-color version.\n', encoding='utf-8')


if __name__ == '__main__':
    for edition in ['othello-classic','othello']:
        export_board(ROOT / 'output/boards' / edition)
