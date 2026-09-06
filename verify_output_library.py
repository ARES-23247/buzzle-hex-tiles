"""Check current documentation links, manifests, images, and folder hygiene."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parent


def verify():
    documents = [ROOT/name for name in ['README.md', 'PRINTING_COLOR_GUIDE.md',
                 'GAMES_AND_RULES.md', 'BUZZLE_217_BOARD_SPECIFICATION.md',
                 'GEMINI.md', 'docs/DEVELOPMENT.md', 'docs/3MF_COLOR_IMPORT.md', 'archive/README.md',
                 'docs/BUZZHEX_RULES.md', 'docs/BUZZHEX_WEBSITE_AGENT_PROMPT.md', 'assets/artwork/buzzhex/README.md']]
    documents += list((ROOT/'output').rglob('*.md'))
    broken, checked = [], 0
    for document in documents:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            target = target.strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme:
                if parsed.scheme == 'file':
                    broken.append(f'{document.relative_to(ROOT)}: non-portable file URI {target}')
                continue
            if not parsed.path:
                continue
            checked += 1
            path = (document.parent/unquote(parsed.path)).resolve()
            if not path.exists():
                broken.append(f'{document.relative_to(ROOT)}: {target}')
    if broken:
        raise AssertionError('Broken current documentation links:\n'+'\n'.join(broken))
    for game, count in [('buzzle', 7), ('othello', 4), ('othello-classic', 4), ('buzzhex', 6)]:
        folder = ROOT/'output/boards'/game
        manifest = json.loads((folder/'print_manifest.json').read_text())
        assert len(manifest['plates']) == count
        assert len(list((folder/'plates').glob('*.3mf'))) == count+1
        for plate in manifest['plates']:
            assert (folder/plate['file']).is_file(), plate['file']
        assert (folder/'images/board_and_bed_preview.png').is_file()
        if game in ['othello', 'othello-classic']:
            import trimesh
            expected_cells = 91 if game == 'othello' else 61
            assert sum(p['cells'] for p in manifest['plates']) == expected_cells
            stls = list((folder/'stl').rglob('*.stl'))
            assert len(stls) == 15
            for path in stls:
                mesh = trimesh.load_mesh(path)
                assert mesh.is_volume, f'Invalid STL solid: {path}'
    images = list((ROOT/'output').rglob('*.png'))
    for path in images:
        with Image.open(path) as img:
            img.verify()
    hashes = {}
    for path in (ROOT/'output').rglob('*.3mf'):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest not in hashes, f'Duplicate active models: {path} and {hashes.get(digest)}'
        hashes[digest] = path
    for old in ['output_biobuzz', 'output_team', 'output_interlocking', 'output_hive',
                'output/3mf', 'output/plates', 'output/board', 'output/othello', 'printouts']:
        assert not (ROOT/old).exists(), f'Old output folder returned: {old}'
    assert (ROOT/'assets/artwork/ares_23247_underside.geojson').is_file()
    print(f'PASS: {checked} local links, {len(images)} images, four board manifests, 30 solid STLs, '
          f'{len(hashes)} unique active 3MF files, and clean output folders.')


if __name__ == '__main__':
    verify()
