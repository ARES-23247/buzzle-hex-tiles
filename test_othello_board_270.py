import itertools
import unittest
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from shapely.geometry import Polygon, box
import generate_othello_board_270 as board


class OthelloBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells=board.make_cells();cls.sections=board.make_sections(cls.cells)
        cls.logo=board.underside_logo()

    def test_piece_fit_and_cell_count(self):
        self.assertEqual(len({c['coord'] for c in self.cells}),61)
        self.assertAlmostEqual(board.TILE_FLAT,1.3*25.4)
        for c in self.cells:
            tile=Polygon(board.make_flat_hex_pts(c['cx'],c['cy'],33.02))
            self.assertTrue(c['pocket'].contains(tile))
        # Verify existing pieces were not resized or removed.
        source=board.OUTPUT.parents[1]/'tiles/othello/3mf/hex_othello_piece_single.3mf'
        with zipfile.ZipFile(source) as archive:
            root=ET.fromstring(archive.read('3D/3dmodel.model'))
        ys=[float(v.get('y')) for v in root.findall('.//{*}vertex')]
        self.assertAlmostEqual(max(ys)-min(ys),33.02,places=3)

    def test_connected_sections_and_clearance(self):
        for s in self.sections:
            self.assertIsInstance(s['footprint'],Polygon)
            p=board.placed(s['footprint'],board.placement(s['footprint']))
            self.assertTrue(box(5,5,265,265).covers(p))
            self.assertGreaterEqual(p.distance(box(225,225,265,265)),5)
            for _,_,socket,tongue in s.get('connections',[]):
                self.assertTrue(socket.covers(tongue))
                self.assertGreater(tongue.boundary.distance(socket.boundary),.19)
        for a,b in itertools.combinations(self.sections,2):
            self.assertLess(a['footprint'].intersection(b['footprint']).area,1e-4)

    def test_material_partition_and_six_corners(self):
        corner_shapes=[];start_shapes=[]
        for s in self.sections:
            layers=board.layers(s,self.logo)
            for a,b in itertools.combinations(layers,2):
                if min(a[4],b[4])-max(a[3],b[3])>1e-6:
                    self.assertLess(a[2].intersection(b[2]).area,1e-4)
            boundaries=sorted({0,board.FLOOR_HEIGHT} | {z for layer in layers for z in layer[3:] if z<board.FLOOR_HEIGHT})
            for z in [(a+b)/2 for a,b in zip(boundaries,boundaries[1:])]:
                coverage=board.union([p for _,_,p,z0,z1 in layers if z0<z<z1])
                self.assertLess(coverage.symmetric_difference(s['footprint']).area,1e-4)
            corner_shapes += [p for _,name,p,_,_ in layers if name=='Six corner anchors']
            start_shapes += [p for _,name,p,_,_ in layers if name=='Starting side markers']
        self.assertEqual(len(board.union(corner_shapes).geoms),6)
        self.assertEqual(len(board.union(start_shapes).geoms),6)

    def test_sturdier_dimensions(self):
        center=next(c for c in self.cells if c['coord']==(0,0,0))
        neighbor=next(c for c in self.cells if c['coord']==(-1,1,0))
        self.assertAlmostEqual(center['pocket'].distance(neighbor['pocket']),2.2,places=4)
        layers=board.layers(self.sections[0],self.logo)
        floor=next(layer for layer in layers if layer[1]=='Pocket floors')
        top=max(layer[4] for layer in layers)
        self.assertAlmostEqual(floor[4],2.8)
        self.assertAlmostEqual(top,5.2)
        self.assertAlmostEqual(top-floor[4],2.4)
        self.assertAlmostEqual(4.8-(top-floor[4]),2.4)
        for layer in layers:
            for z in layer[3:]:
                self.assertAlmostEqual(z/.2,round(z/.2))

    def test_generated_files(self):
        paths=list((board.OUTPUT/'plates').glob('*.3mf'))
        self.assertEqual(len(paths),5)
        for path in paths:
            with self.subTest(file=path.name),zipfile.ZipFile(path) as archive:
                root=ET.fromstring(archive.read('3D/3dmodel.model'))
                self.assertEqual([v.get('color') for v in root.findall('.//{*}color')],[c+'FF' for c in board.COLORS])
                for obj in root.findall('.//{*}object'):
                    if obj.find('{*}mesh') is None:continue
                    vertices=np.array([[float(v.get(a)) for a in 'xyz'] for v in obj.findall('.//{*}vertex')])
                    faces=np.array([[int(f.get(a)) for a in ['v1','v2','v3']] for f in obj.findall('.//{*}triangle')])
                    mesh=trimesh.Trimesh(vertices,faces,process=True)
                    self.assertTrue(mesh.is_volume,obj.get('name'))
                    self.assertIn(int(obj.get('pindex')),range(4))
                    self.assertTrue(np.all(mesh.bounds[0]>=[5,5,0]))
                    self.assertTrue(np.all(mesh.bounds[1]<=[265,265,board.TOTAL_HEIGHT]))


if __name__=='__main__':unittest.main()
