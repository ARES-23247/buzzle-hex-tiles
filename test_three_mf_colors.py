"""Validate viewer colors and the actual part metadata read by Orca/Snapmaker."""
import json
from pathlib import Path
import uuid
import unittest
import xml.etree.ElementTree as ET
import zipfile

from three_mf_colors import add_color_metadata, CORE, MATERIAL

ROOT = Path(__file__).resolve().parent


class ColorExportTests(unittest.TestCase):
    def check_file(self, path):
        with zipfile.ZipFile(path) as archive:
            model = ET.fromstring(archive.read('3D/3dmodel.model'))
            config = ET.fromstring(archive.read('Metadata/model_settings.config'))
            project = json.loads(archive.read('Metadata/project_settings.config'))
        resources = {r.get('id'): r for r in model.find(f'{{{CORE}}}resources')}
        self.assertEqual(len(resources), len(model.find(f'{{{CORE}}}resources')), 'Duplicate resource IDs')
        palette = project['filament_colour']
        self.assertLessEqual(len(palette), 4)
        self.assertEqual(set(project), {'filament_colour'}, 'Do not change printer/material profiles')
        for obj in model.findall('.//{*}object'):
            if obj.find('{*}mesh') is None:
                continue
            slot = int(obj.get('pindex'))
            base = list(resources[obj.get('pid')])[slot]
            self.assertEqual(base.get('displaycolor'), palette[slot]+'FF')
            self.assertIn(f'[Slot {slot+1} - {base.get("name")}]', obj.get('name'))
            for triangle in obj.findall('.//{*}triangle'):
                group = resources[triangle.get('pid')]
                self.assertEqual(group.tag, f'{{{MATERIAL}}}colorgroup')
                self.assertEqual([triangle.get(k) for k in ['p1','p2','p3']], [str(slot)]*3)
                self.assertEqual(list(group)[slot].get('color'), palette[slot]+'FF')
        for item in model.findall('.//{*}build/{*}item'):
            assembly = resources[item.get('objectid')]
            cfg = config.find(f'object[@id="{item.get("objectid")}"]')
            self.assertIsNotNone(cfg)
            parts = assembly.findall('{*}components/{*}component')
            ids = [p.get('objectid') for p in parts] or [assembly.get('id')]
            self.assertEqual([p.get('id') for p in cfg.findall('part')], ids)
            for part in cfg.findall('part'):
                obj = resources[part.get('id')]
                values = {m.get('key'): m.get('value') for m in part.findall('metadata')}
                self.assertEqual(values['name'], obj.get('name'))
                self.assertEqual(int(values['extruder']), int(obj.get('pindex'))+1)

    def test_every_current_board_and_tile(self):
        files = list((ROOT/'output/boards').rglob('*.3mf')) + list((ROOT/'output/tiles').rglob('*.3mf'))
        self.assertGreater(len(files), 50)
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                self.check_file(path)

    def test_reapplying_metadata_preserves_mesh_and_transforms(self):
        source = ROOT/'output/tiles/biobuzz/3mf/tile_doublesided_biobuzz_A_score1.3mf'
        path = ROOT/f'color-test-{uuid.uuid4().hex}.3mf'
        try:
            path.write_bytes(source.read_bytes())
            with zipfile.ZipFile(path) as archive:
                before = archive.read('3D/3dmodel.model')
            add_color_metadata(path, ['#FFFF00','#000000'], ['Yellow','Black'])
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(before, archive.read('3D/3dmodel.model'))
            self.check_file(path)
        finally:
            path.unlink(missing_ok=True)
            path.with_suffix('.3mf.tmp').unlink(missing_ok=True)

    def test_requested_palettes(self):
        for game, palette in [('buzzle',['#000000','#FFFFFF','#0077CC','#FFFF00']),
                              ('othello',['#000000','#FFFF00'])]:
            manifest = json.loads((ROOT/'output/boards'/game/'print_manifest.json').read_text())
            self.assertEqual(manifest['colors'], palette)
        for path in (ROOT/'output/tiles').rglob('*.3mf'):
            with zipfile.ZipFile(path) as archive:
                colors = json.loads(archive.read('Metadata/project_settings.config'))['filament_colour']
            if 'othello' in path.parts:
                self.assertEqual(colors, ['#000000','#FFFFFF'])
            elif not path.name.startswith('plate_256_board_'):
                self.assertEqual(colors, ['#FFFF00','#000000'])


if __name__ == '__main__':
    unittest.main()
