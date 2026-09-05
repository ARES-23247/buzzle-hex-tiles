"""Geometry and exported-file checks; run after generate_board_270.py."""
import itertools
import unittest
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np
import trimesh
from shapely.geometry import Polygon, box

import generate_board_270 as board


class BoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = board.make_cells()
        cls.sections = board.make_sections(cls.cells)

    def test_locked_layout_and_tile_fit(self):
        self.assertEqual(len({c['coord'] for c in self.cells}), 217)
        self.assertEqual(Counter(c['desc'] for c in self.cells), {
            'BLANK': 162, 'START': 1, 'DOUBLE LETTER': 24, 'TRIPLE LETTER': 6,
            'DOUBLE WORD': 12, 'TRIPLE WORD': 6, 'KEY WILD (DW)': 6})
        self.assertAlmostEqual(board.POCKET_FLAT-board.TILE_FLAT, 0.78)
        self.assertEqual(sorted(len(s['cells']) for s in self.sections), [30]*6+[37])
        for c in self.cells:
            tile = Polygon(board.make_flat_hex_pts(c['cx'], c['cy'], 33.02))
            self.assertTrue(c['pocket'].contains(tile))

    def test_connected_sections_and_mating_joints(self):
        hub = self.sections[0]
        for s in self.sections:
            self.assertIsInstance(s['footprint'], Polygon)
            self.assertTrue(s['footprint'].is_valid)
        for a, b in itertools.combinations(self.sections, 2):
            # Boolean precision grid is 0.00001 mm; tolerate sub-grid edge slivers.
            self.assertLess(a['footprint'].intersection(b['footprint']).area, 1e-4)
        for socket, wedge in zip(hub['sockets'], self.sections[1:]):
            tongue = wedge['tongues'][0]
            self.assertTrue(socket.covers(tongue))
            self.assertGreater(tongue.intersection(wedge['original']).area, 5)
            self.assertGreater(tongue.intersection(hub['original']).area, 50)
            # Female cutout has clearance around the actual male profile.
            self.assertGreater(tongue.boundary.distance(socket.boundary), 0.19)

    def test_materials_partition_floor_without_overlap(self):
        for s in self.sections:
            layers = board.make_layers(s)
            for a, b in itertools.combinations(layers, 2):
                if min(a[4], b[4])-max(a[3], b[3]) > 1e-6:
                    self.assertLess(a[2].intersection(b[2]).area, 1e-5)
            boundaries = sorted({0, board.FLOOR_HEIGHT} | {z for layer in layers for z in layer[3:] if z < board.FLOOR_HEIGHT})
            for z in [(a+b)/2 for a,b in zip(boundaries,boundaries[1:])]:
                coverage = board.union([p for _, _, p, z0, z1 in layers if z0 < z < z1])
                self.assertLess(coverage.symmetric_difference(s['footprint']).area, 1e-5)
            lower = board.union([p for _, _, p, _, z1 in layers if z1 == board.FLOOR_HEIGHT])
            ribs = board.union([p for _, _, p, _, z1 in layers if z1 == board.TOTAL_HEIGHT])
            self.assertLess(ribs.difference(lower).area, 1e-5)

    def test_sturdier_dimensions(self):
        center = next(c for c in self.cells if c['coord'] == (0,0,0))
        neighbor = next(c for c in self.cells if c['coord'] == (-1,1,0))
        self.assertAlmostEqual(center['pocket'].distance(neighbor['pocket']), 2.2, places=4)
        layers = board.make_layers(self.sections[0])
        floor = next(layer for layer in layers if layer[1] == 'Pocket floors')
        top = max(layer[4] for layer in layers)
        self.assertAlmostEqual(floor[4], 2.8)
        self.assertAlmostEqual(top, 5.8)
        self.assertAlmostEqual(top-floor[4], 3.0)
        self.assertGreater(4.8-(top-floor[4]), 1.0)
        for layer in layers:
            for z in layer[3:]:
                self.assertAlmostEqual(z/.2, round(z/.2))

    def test_bed_and_tower_clearance(self):
        for s in self.sections:
            p = board.placed(s['footprint'], board.placement(s['footprint']))
            self.assertTrue(box(5, 5, 265, 265).covers(p))
            self.assertGreaterEqual(p.distance(box(225, 225, 265, 265)), 5)

    def test_exported_3mf_xml_solids_and_four_colors(self):
        files = sorted((board.OUTPUT/'plates').glob('*.3mf'))
        self.assertEqual(len(files), 8, 'Generate the seven sections and test coupon first')
        for path in files:
            with self.subTest(file=path.name), zipfile.ZipFile(path) as archive:
                for name in ['[Content_Types].xml', '_rels/.rels', '3D/3dmodel.model']:
                    root = ET.fromstring(archive.read(name))
                self.assertEqual(len(root.findall('.//{*}color')), 4)
                ids = {obj.get('id') for obj in root.findall('.//{*}object')}
                for ref in root.findall('.//{*}component')+root.findall('.//{*}item'):
                    self.assertIn(ref.get('objectid'), ids)
                for obj in root.findall('.//{*}object'):
                    mesh_xml = obj.find('{*}mesh')
                    if mesh_xml is None:
                        continue
                    self.assertIn(int(obj.get('pindex')), range(4))
                    vertices = np.array([[float(v.get(a)) for a in 'xyz'] for v in mesh_xml.findall('.//{*}vertex')])
                    faces = np.array([[int(f.get(a)) for a in ['v1', 'v2', 'v3']] for f in mesh_xml.findall('.//{*}triangle')])
                    mesh = trimesh.Trimesh(vertices, faces, process=True)
                    self.assertTrue(mesh.is_volume, obj.get('name'))
                    self.assertTrue(np.all(mesh.bounds[0] >= [5, 5, 0]))
                    self.assertTrue(np.all(mesh.bounds[1] <= [265, 265, board.TOTAL_HEIGHT]))


if __name__ == '__main__':
    unittest.main()
