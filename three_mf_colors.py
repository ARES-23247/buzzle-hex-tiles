"""Portable surface colors plus explicit Snapmaker/Orca part assignments.

3MF display colors are not filament assignments. Store both, without embedding
printer, temperature, speed, or material profiles. Existing mesh coordinates,
triangles, and assembly transforms are preserved.
"""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
MATERIAL = 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02'
ET.register_namespace('', CORE)
ET.register_namespace('m', MATERIAL)
REVERSIBLE_COLORS = ['#000000', '#FFFF00']
WORD_COLORS = ['#FFFF00', '#000000']


def metadata(parent, key, value, **attrs):
    return ET.SubElement(parent, 'metadata', key=key, value=str(value), **attrs)


def add_color_metadata(filepath, palette, names, assignments=None):
    """Decorate a generated 3MF; assignments maps mesh ids to zero-based slots.

    When omitted, existing object pindex values are used. Idempotent: prior
    color/config metadata is replaced, not appended. Only flat assemblies or
    direct meshes are accepted, matching this project's exporters.
    """
    if not 1 <= len(palette) <= 4 or len(names) != len(palette):
        raise ValueError('One to four named colors are required')
    if any(not re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in palette):
        raise ValueError('Colors must be #RRGGBB')
    filepath = Path(filepath)
    with zipfile.ZipFile(filepath) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    model = ET.fromstring(entries['3D/3dmodel.model'])
    resources = model.find(f'{{{CORE}}}resources')
    objects = {obj.get('id'): obj for obj in resources.findall(f'{{{CORE}}}object')}
    for child in list(resources):
        if child.tag in (f'{{{MATERIAL}}}colorgroup', f'{{{CORE}}}basematerials'):
            resources.remove(child)
    color_id = str(max(map(int, objects), default=0) + 1)
    base_id = str(int(color_id) + 1)
    group = ET.Element(f'{{{MATERIAL}}}colorgroup', id=color_id)
    bases = ET.Element(f'{{{CORE}}}basematerials', id=base_id)
    for color, name in zip(palette, names):
        ET.SubElement(group, f'{{{MATERIAL}}}color', color=color+'FF')
        ET.SubElement(bases, f'{{{CORE}}}base', name=name, displaycolor=color+'FF')
    resources.insert(0, bases)
    resources.insert(1, group)
    slots = {}
    for obj_id, obj in objects.items():
        mesh = obj.find(f'{{{CORE}}}mesh')
        if mesh is None:
            continue
        slot = int(obj.get('pindex', '0')) if assignments is None else assignments[obj_id]
        if slot not in range(len(palette)):
            raise ValueError(f'Invalid slot {slot} for {obj_id}')
        slots[obj_id] = slot
        label = re.sub(r'^\[Slot \d+ - [^]]+\]\s*', '', obj.get('name', f'Part {obj_id}'))
        obj.set('name', f'[Slot {slot+1} - {names[slot]}] {label}')
        obj.set('pid', base_id)
        obj.set('pindex', str(slot))
        # Explicit per-face color for viewers that ignore object-level defaults.
        for triangle in mesh.findall(f'.//{{{CORE}}}triangle'):
            triangle.attrib.update(pid=color_id, p1=str(slot), p2=str(slot), p3=str(slot))

    config = ET.Element('config')
    for item in model.findall(f'{{{CORE}}}build/{{{CORE}}}item'):
        obj_id = item.get('objectid')
        obj = objects[obj_id]
        component_ids = [c.get('objectid') for c in obj.findall(f'{{{CORE}}}components/{{{CORE}}}component')]
        component_ids = component_ids or [obj_id]
        if any(i not in slots for i in component_ids):
            raise ValueError('Nested assemblies require an explicit metadata implementation')
        cfg_obj = ET.SubElement(config, 'object', id=obj_id)
        metadata(cfg_obj, 'name', obj.get('name', filepath.stem))
        metadata(cfg_obj, 'extruder', slots[component_ids[0]]+1)
        for part_id in component_ids:
            part = objects[part_id]
            cfg_part = ET.SubElement(cfg_obj, 'part', id=part_id, subtype='normal_part')
            metadata(cfg_part, 'name', part.get('name'))
            metadata(cfg_part, 'extruder', slots[part_id]+1)
    entries['3D/3dmodel.model'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    entries['Metadata/model_settings.config'] = ET.tostring(config, encoding='utf-8', xml_declaration=True)
    # Do not add another slicer's config signature: that can select its importer.
    entries.pop('Metadata/Slic3r_PE_model.config', None)
    entries.pop('Metadata/Slic3r_PE.config', None)
    entries['Metadata/project_settings.config'] = (json.dumps({
        'filament_colour': palette,
    }, indent=2)+'\n').encode()
    entries['Metadata/COLOR_ASSIGNMENTS.txt'] = ('Color slots (choose your own material presets):\n'+
        '\n'.join(f'{i+1}: {name} {color}' for i,(name,color) in enumerate(zip(names,palette)))+
        '\n\nOpen as a project to retain filament colors. Mesh-only import may use your current filament swatches.\n').encode()
    # Register added file extensions without changing the package relationships.
    ct = ET.fromstring(entries['[Content_Types].xml'])
    ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
    existing = {e.get('Extension') for e in ct}
    for ext, content_type in [('config','application/octet-stream'),('txt','text/plain')]:
        if ext not in existing:
            ET.SubElement(ct, f'{{{ns}}}Default', Extension=ext, ContentType=content_type)
    entries['[Content_Types].xml'] = ET.tostring(ct, encoding='utf-8', xml_declaration=True)
    temporary = filepath.with_suffix('.3mf.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    temporary.replace(filepath)


def color_existing_tiles(root=Path(__file__).resolve().parent/'output/tiles'):
    for path in sorted(root.rglob('*.3mf')):
        with zipfile.ZipFile(path) as archive:
            model = ET.fromstring(archive.read('3D/3dmodel.model'))
        othello = 'othello' in path.parts
        retained_board = path.name.startswith('plate_256_board_')
        assignments = {}
        for obj in model.findall('.//{*}object'):
            if obj.find('{*}mesh') is None:
                continue
            name = obj.get('name', '')
            if retained_board:
                if 'Bonus_Blue' in name:
                    slot = 2
                elif 'Bonus_Green' in name:
                    slot = 1
                elif 'Base' in name or 'Bonus_Gold' in name:
                    slot = 3
                elif any(s in name for s in ['Wall', 'Text', 'Inlay']):
                    slot = 0
                else:
                    raise ValueError(f'Unrecognized retained board part: {name}')
            elif othello:
                slot = 1 if 'Ivory' in name else 0
            elif 'Base' in name:
                slot = 0
            elif any(s in name for s in ['Graphics','Text','Inlay']):
                slot = 1
            else:
                raise ValueError(f'Unrecognized tile part: {path}: {name}')
            assignments[obj.get('id')] = slot
        palette = ['#000000','#FFFFFF','#0077CC','#FFFF00'] if retained_board else REVERSIBLE_COLORS if othello else WORD_COLORS
        names = ['Black','White','Blue','Yellow'] if retained_board else ['Black','Yellow'] if othello else ['Yellow','Black']
        add_color_metadata(path, palette, names, assignments)
        print(path.relative_to(root))


if __name__ == '__main__':
    color_existing_tiles()
