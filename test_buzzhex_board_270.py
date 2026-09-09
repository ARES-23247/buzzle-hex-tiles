"""Geometry, manufacturing, and web-coordinate contract checks for BUZZHEX."""
import itertools
import json
import math
import unittest
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh
from shapely.geometry import Polygon, box

import generate_buzzhex_board_270 as board


class BuzzhexBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = board.make_cells()
        cls.sections = board.make_sections(cls.cells)
        cls.rails = board.goal_rails(cls.cells)

    def test_121_cells_and_exact_buzzello_tile_fit(self):
        self.assertEqual({c['coord'] for c in self.cells}, set(itertools.product(range(11), repeat=2)))
        self.assertEqual([len(s['cells']) for s in self.sections], [24, 24, 18, 20, 20, 15])
        source = board.OUTPUT.parents[1]/'tiles/othello/3mf/hex_othello_piece_single.3mf'
        with zipfile.ZipFile(source) as archive:
            root = ET.fromstring(archive.read('3D/3dmodel.model'))
        ys = [float(v.get('y')) for v in root.findall('.//{*}vertex')]
        zs = [float(v.get('z')) for v in root.findall('.//{*}vertex')]
        self.assertAlmostEqual(max(ys)-min(ys), board.TILE_FLAT, places=3)
        self.assertAlmostEqual(max(zs)-min(zs)-board.POCKET_DEPTH, 2.4)
        for c in self.cells:
            tile = Polygon(board.make_flat_hex_pts(c['cx'], c['cy'], board.TILE_FLAT))
            self.assertTrue(c['pocket'].contains(tile))
            self.assertAlmostEqual(tile.boundary.distance(c['pocket'].boundary), .24, places=4)

    def test_adjacency_matches_physical_hex_grid_and_web_spec(self):
        lookup = {c['coord']: c for c in self.cells}
        for c in self.cells:
            q, r = c['coord']
            logical = {(q+dq, r+dr) for dq, dr in board.NEIGHBORS} & lookup.keys()
            physical = {other['coord'] for other in self.cells if abs(math.hypot(
                other['cx']-c['cx'], other['cy']-c['cy'])-board.PITCH) < 1e-5}
            self.assertEqual(logical, physical)
        spec = json.loads((board.OUTPUT/'game_spec.json').read_text())
        self.assertEqual(spec['size'], 11)
        self.assertEqual(spec['cell_count'], 121)
        self.assertEqual(spec['black_goal'], dict(axis='q', edges=[0, 10]))
        self.assertEqual(spec['yellow_goal'], dict(axis='r', edges=[0, 10]))
        for c in spec['cells']:
            original = lookup[c['q'], c['r']]
            self.assertAlmostEqual(c['cx_mm'], original['cx'], places=5)
            self.assertAlmostEqual(c['cy_mm'], original['cy'], places=5)

    def test_connected_sections_clearance_pockets_and_print_bed(self):
        for s in self.sections:
            self.assertIsInstance(s['footprint'], Polygon)
            p = board.placed(s['footprint'], board.placement(s['footprint']))
            self.assertTrue(box(5, 5, 265, 265).covers(p))
            self.assertGreaterEqual(p.distance(box(225, 225, 265, 265)), 5)
            for c in s['cells']:
                self.assertTrue(s['original'].covers(c['pocket']))
            for inner, outer, socket, tongue in s.get('connections', []):
                self.assertTrue(socket.covers(tongue))
                self.assertAlmostEqual(socket.boundary.distance(tongue.boundary), .4, places=4)
        for a, b in itertools.combinations(self.sections, 2):
            self.assertLess(a['footprint'].intersection(b['footprint']).area, 1e-4)
            self.assertGreaterEqual(a['footprint'].distance(b['footprint']), .3-1e-4)
        for sample in board.fit_samples(self.sections):
            c = sample['cells'][0]
            expected = self.sections[c['section']]['footprint'].intersection(c['outer'])
            self.assertLess(sample['footprint'].intersection(c['outer']).symmetric_difference(expected).area, 1e-4)

    def test_disjoint_materials_and_solid_floor(self):
        for s in self.sections:
            layers = board.layers(s, self.rails)
            for a, b in itertools.combinations(layers, 2):
                if min(a[4], b[4])-max(a[3], b[3]) > 1e-6:
                    self.assertLess(a[2].intersection(b[2]).area, 1e-4)
            for z in [1, 2.4]:
                coverage = board.union([p for _, _, p, z0, z1 in layers if z0 < z < z1])
                self.assertLess(coverage.symmetric_difference(s['footprint']).area, 1e-4)
            for layer in layers:
                for z in layer[3:]:
                    self.assertAlmostEqual(z/.2, round(z/.2))
        black, yellow = self.rails
        self.assertLess(black.intersection(yellow).area, 1e-4)
        self.assertAlmostEqual(black.area, yellow.area, places=2)
        # Every boundary cell meets its assigned rail, including BOTH colors at corners.
        for c in self.cells:
            q, r = c['coord']
            if q in (0, 10):
                self.assertLess(c['outer'].distance(black), 1e-4)
            if r in (0, 10):
                self.assertLess(c['outer'].distance(yellow), 1e-4)

    def test_exported_3mf_meshes_and_manifest(self):
        manifest = json.loads((board.OUTPUT/'print_manifest.json').read_text())
        self.assertEqual(sum(p['cells'] for p in manifest['plates']), 121)
        self.assertEqual(len(manifest['plates']), 6)
        paths = list((board.OUTPUT/'plates').glob('*.3mf'))
        self.assertEqual(len(paths), 7)
        for path in paths:
            with self.subTest(file=path.name), zipfile.ZipFile(path) as archive:
                root = ET.fromstring(archive.read('3D/3dmodel.model'))
                self.assertEqual([v.get('color') for v in root.findall('.//{*}color')], [c+'FF' for c in board.COLORS])
                for obj in root.findall('.//{*}object'):
                    if obj.find('{*}mesh') is None:
                        continue
                    vertices = np.array([[float(v.get(a)) for a in 'xyz'] for v in obj.findall('.//{*}vertex')])
                    faces = np.array([[int(f.get(a)) for a in ['v1', 'v2', 'v3']] for f in obj.findall('.//{*}triangle')])
                    mesh = trimesh.Trimesh(vertices, faces, process=True)
                    self.assertTrue(mesh.is_volume, obj.get('name'))
                    self.assertIn(int(obj.get('pindex')), range(3))
                    self.assertTrue(np.all(mesh.bounds[0] >= [5, 5, 0]))
                    self.assertTrue(np.all(mesh.bounds[1] <= [265, 265, board.TOTAL_HEIGHT]))


if __name__ == '__main__':
    unittest.main()
