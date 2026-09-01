"""
Dual-Color Hexagonal Scrabble 3D Printable Tile Generator
=========================================================
Generates 1.5 inch (38.1 mm) diameter hexagonal game tiles with letters and numbers.
Optimized for multi-material 3D printing with toolhead changers (Prusa XL, Bambu AMS,
Voron StealthChanger, IDEX, OrcaSlicer, PrusaSlicer, Cura).
"""

import os
import sys
import argparse
import zipfile
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.affinity import translate
import mapbox_earcut
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# Standard English Scrabble Point Values
SCRABBLE_POINTS = {
    'A': '1',  'B': '3',  'C': '3',  'D': '2',  'E': '1',
    'F': '4',  'G': '2',  'H': '4',  'I': '1',  'J': '8',
    'K': '5',  'L': '1',  'M': '3',  'N': '1',  'O': '1',
    'P': '3',  'Q': '10', 'R': '1',  'S': '1',  'T': '1',
    'U': '1',  'V': '4',  'W': '4',  'X': '8',  'Y': '4',
    'Z': '10', 'BLANK': '0', ' ': '0'
}


def find_default_font():
    """Find a high-quality bold sans-serif font on the local system."""
    candidates = [
        r"C:\Windows\Fonts\trebucbd.ttf",   # Trebuchet MS Bold
        r"C:\Windows\Fonts\arialbd.ttf",    # Arial Bold
        r"C:\Windows\Fonts\segoeuib.ttf",   # Segoe UI Bold
        r"C:\Windows\Fonts\calibrib.ttf",   # Calibri Bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def triangulate_shapely_poly(poly):
    """
    Triangulate a 2D Shapely polygon (with holes) using mapbox_earcut.
    Returns (vertices, faces) where vertices is (N, 2) and faces is (M, 3).
    """
    if poly is None or poly.is_empty:
        return np.zeros((0, 2), dtype=np.float64), np.zeros((0, 3), dtype=np.int64)
        
    exterior_coords = np.array(poly.exterior.coords, dtype=np.float64)[:-1]
    rings = [exterior_coords]
    ring_ends = [len(exterior_coords)]
    
    for interior in poly.interiors:
        hole_coords = np.array(interior.coords, dtype=np.float64)[:-1]
        if len(hole_coords) >= 3:
            rings.append(hole_coords)
            ring_ends.append(ring_ends[-1] + len(hole_coords))
            
    vertices = np.ascontiguousarray(np.vstack(rings), dtype=np.float64)
    holes_arr = np.array(ring_ends, dtype=np.uint32)
    faces = mapbox_earcut.triangulate_float64(vertices, holes_arr)
    faces = faces.reshape(-1, 3).astype(np.int64)
    return vertices, faces


def make_hex_points_2d(flat_to_flat):
    """
    Generate 6 vertices of a flat-topped regular hexagon in CCW order.
    Distance between top flat (y=+r) and bottom flat (y=-r) is exactly flat_to_flat.
    """
    r = flat_to_flat / 2.0
    R = r / np.cos(np.deg2rad(30))
    s_half = r * np.tan(np.deg2rad(30))
    return np.array([
        [s_half, r],
        [-s_half, r],
        [-R, 0.0],
        [-s_half, -r],
        [s_half, -r],
        [R, 0.0]
    ], dtype=np.float64)


def char_to_polygons(text, font_path, size=20):
    """
    Convert a text string into a list of correctly oriented Shapely Polygons with hole nesting.
    """
    if not text:
        return []
    fp = FontProperties(fname=font_path) if font_path else FontProperties(weight='bold')
    tp = TextPath((0, 0), text, size=size, prop=fp)
    rings = tp.to_polygons()
    if not rings:
        return []
        
    raw_polys = []
    for r in rings:
        if len(r) >= 3:
            p = Polygon(r)
            if not p.is_valid:
                p = p.buffer(0)
            if p.area > 1e-5:
                raw_polys.append(p)
                
    if not raw_polys:
        return []
        
    # Sort by area descending so outer solids precede inner holes
    raw_polys.sort(key=lambda p: p.area, reverse=True)
    
    # Calculate nesting depths
    depths = []
    for i, p in enumerate(raw_polys):
        d = 0
        p_pt = p.representative_point()
        for j in range(i):
            other = raw_polys[j]
            if other.buffer(1e-6).contains(p_pt) or other.covers(p):
                d += 1
        depths.append(d)
        
    # Form polygons with attached holes
    solids = []
    for i, p in enumerate(raw_polys):
        if depths[i] % 2 == 0:
            holes = []
            for j in range(i + 1, len(raw_polys)):
                if depths[j] == depths[i] + 1:
                    hole_cand = raw_polys[j]
                    if p.buffer(1e-6).contains(hole_cand.representative_point()) or p.covers(hole_cand):
                        holes.append(hole_cand.exterior.coords)
            poly = Polygon(p.exterior.coords, holes=holes)
            poly = orient(poly, sign=1.0)
            solids.append(poly)
            
    return solids


def build_tile_pair(letter="A", score=None, flat_to_flat=38.1, height=4.8,
                     chamfer=0.8, inlay_depth=0.8, emboss_height=0.0,
                     font_path=None, letter_size=18.5, score_size=7.0):
    """
    Builds the complete watertight 3D meshes for:
      - Base Mesh (Hexagon with chamfer and negative cavity for glyphs)
      - Text Mesh (Glyphs with matching thickness flush or embossed)
    """
    if font_path is None:
        font_path = find_default_font()
        
    # 1. Process Main Letter/Character
    l_polys = []
    has_score = (score is not None and str(score).strip() and str(score) != '0')
    if letter and letter.strip():
        l_raw = char_to_polygons(letter, font_path, size=letter_size)
        if l_raw:
            l_union = l_raw[0] if len(l_raw) == 1 else MultiPolygon(l_raw)
            minx, miny, maxx, maxy = l_union.bounds
            cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
            
            # If score is present, shift letter slightly left/up for classic Scrabble balance
            shift_x = -2.0 if has_score else 0.0
            shift_y = 1.2 if has_score else 0.0
            l_polys = [translate(p, xoff=-cx + shift_x, yoff=-cy + shift_y) for p in l_raw]
            
    # 2. Process Score Subscript
    s_polys = []
    if has_score:
        s_raw = char_to_polygons(str(score), font_path, size=score_size)
        if s_raw:
            s_union = s_raw[0] if len(s_raw) == 1 else MultiPolygon(s_raw)
            minx, miny, maxx, maxy = s_union.bounds
            # Target position at bottom-right corner inside hex boundary
            target_x = 8.6
            target_y = -8.2
            s_polys = [translate(p, xoff=target_x - (minx + maxx) / 2.0, yoff=target_y - (miny + maxy) / 2.0) for p in s_raw]
            
    all_glyphs = l_polys + s_polys
    if all_glyphs:
        glyph_union = all_glyphs[0] if len(all_glyphs) == 1 else unary_union(all_glyphs)
        glyph_polys = [glyph_union] if isinstance(glyph_union, Polygon) else list(glyph_union.geoms)
        glyph_polys = [orient(gp, sign=1.0) for gp in glyph_polys]
    else:
        glyph_union = None
        glyph_polys = []
        
    z_cavity = height - inlay_depth
    z_top = height
    z_chamfer = height - chamfer
    z_bottom = 0.0
    text_total_height = inlay_depth + emboss_height
    
    # ------------------
    # 3. BUILD TEXT MESH
    # ------------------
    if glyph_polys:
        t_meshes = []
        for gp in glyph_polys:
            tm = trimesh.creation.extrude_polygon(gp, height=text_total_height)
            tm.apply_translation([0, 0, z_cavity])
            t_meshes.append(tm)
        mesh_text = trimesh.util.concatenate(t_meshes) if len(t_meshes) > 1 else t_meshes[0]
        mesh_text.merge_vertices(digits_vertex=4)
        mesh_text.fix_normals()
    else:
        mesh_text = None
        
    # ------------------
    # 4. BUILD BASE MESH
    # ------------------
    hex_base_2d = make_hex_points_2d(flat_to_flat)
    hex_top_2d = make_hex_points_2d(flat_to_flat - 2 * chamfer)
    poly_base = orient(Polygon(hex_base_2d), sign=1.0)
    poly_top = orient(Polygon(hex_top_2d), sign=1.0)
    
    verts_list = []
    faces_list = []
    
    def add_mesh_data(v, f):
        offset = sum(len(x) for x in verts_list)
        verts_list.append(v)
        faces_list.append(f + offset)
        
    # A. Bottom cap at z=0 (normal -Z)
    vb, fb = triangulate_shapely_poly(poly_base)
    vb3 = np.hstack([vb, np.zeros((len(vb), 1))])
    fb_flip = np.column_stack([fb[:, 0], fb[:, 2], fb[:, 1]])
    add_mesh_data(vb3, fb_flip)
    
    # B. Lower side walls (z=0 to z=z_chamfer)
    vw, fw = [], []
    for i in range(6):
        p1 = hex_base_2d[i]
        p2 = hex_base_2d[(i + 1) % 6]
        idx = len(vw)
        vw.extend([
            [p1[0], p1[1], 0.0],
            [p2[0], p2[1], 0.0],
            [p2[0], p2[1], z_chamfer],
            [p1[0], p1[1], z_chamfer]
        ])
        fw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
    add_mesh_data(np.array(vw), np.array(fw))
    
    # C. Chamfer side walls (z=z_chamfer to z=z_top)
    vc, fc = [], []
    for i in range(6):
        p1b = hex_base_2d[i]
        p2b = hex_base_2d[(i + 1) % 6]
        p1t = hex_top_2d[i]
        p2t = hex_top_2d[(i + 1) % 6]
        idx = len(vc)
        vc.extend([
            [p1b[0], p1b[1], z_chamfer],
            [p2b[0], p2b[1], z_chamfer],
            [p2t[0], p2t[1], z_top],
            [p1t[0], p1t[1], z_top]
        ])
        fc.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
    add_mesh_data(np.array(vc), np.array(fc))
    
    # D. Top face at z=z_top (poly_top difference glyphs)
    if glyph_polys:
        poly_top_diff = poly_top.difference(unary_union(glyph_polys))
    else:
        poly_top_diff = poly_top
        
    diff_polys = [poly_top_diff] if isinstance(poly_top_diff, Polygon) else list(poly_top_diff.geoms)
    for dp in diff_polys:
        vt, ft = triangulate_shapely_poly(dp)
        add_mesh_data(np.hstack([vt, np.full((len(vt), 1), z_top)]), ft)
        
    # E. Cavity floor & walls
    for gp in glyph_polys:
        # Cavity floor (z_cavity, normal +Z)
        vcav, fcav = triangulate_shapely_poly(gp)
        add_mesh_data(np.hstack([vcav, np.full((len(vcav), 1), z_cavity)]), fcav)
        
        # Cavity exterior ring wall
        ext_c = np.array(gp.exterior.coords)[:-1]
        n_e = len(ext_c)
        v_cw, f_cw = [], []
        for i in range(n_e):
            pc = ext_c[i]
            pn = ext_c[(i + 1) % n_e]
            idx = len(v_cw)
            v_cw.extend([
                [pc[0], pc[1], z_cavity],
                [pn[0], pn[1], z_cavity],
                [pn[0], pn[1], z_top],
                [pc[0], pc[1], z_top]
            ])
            f_cw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
        add_mesh_data(np.array(v_cw), np.array(f_cw))
        
        # Cavity interior hole walls (islands in glyphs)
        for interior in gp.interiors:
            hole_c = np.array(interior.coords)[:-1]
            n_h = len(hole_c)
            v_hw, f_hw = [], []
            for i in range(n_h):
                pc = hole_c[i]
                pn = hole_c[(i + 1) % n_h]
                idx = len(v_hw)
                v_hw.extend([
                    [pc[0], pc[1], z_cavity],
                    [pn[0], pn[1], z_cavity],
                    [pn[0], pn[1], z_top],
                    [pc[0], pc[1], z_top]
                ])
                f_hw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
            add_mesh_data(np.array(v_hw), np.array(f_hw))
            
    mesh_base = trimesh.Trimesh(vertices=np.vstack(verts_list), faces=np.vstack(faces_list), process=True)
    mesh_base.merge_vertices(digits_vertex=4)
    mesh_base.fix_normals()
    
    return mesh_base, mesh_text


def export_multimaterial_3mf(filepath, parts_dict):
    """
    Export multiple meshes into a single native multi-part 3MF package.
    Automatically configured for multi-extruder / toolhead changer assignment.
    """
    content_types_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""

    model_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
        '  <resources>'
    ]
    
    obj_id = 1
    comp_ids = []
    
    for name, mesh in parts_dict.items():
        if mesh is None or len(mesh.vertices) == 0:
            continue
        model_lines.append(f'    <object id="{obj_id}" name="{name}" type="model">')
        model_lines.append('      <mesh>')
        model_lines.append('        <vertices>')
        for v in mesh.vertices:
            model_lines.append(f'          <vertex x="{v[0]:.4f}" y="{v[1]:.4f}" z="{v[2]:.4f}"/>')
        model_lines.append('        </vertices>')
        model_lines.append('        <triangles>')
        for f in mesh.faces:
            model_lines.append(f'          <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>')
        model_lines.append('        </triangles>')
        model_lines.append('      </mesh>')
        model_lines.append('    </object>')
        comp_ids.append(obj_id)
        obj_id += 1
        
    assembly_id = obj_id
    model_lines.append(f'    <object id="{assembly_id}" name="Hex_Tile_Assembly" type="model">')
    model_lines.append('      <components>')
    for cid in comp_ids:
        model_lines.append(f'        <component objectid="{cid}"/>')
    model_lines.append('      </components>')
    model_lines.append('    </object>')
    model_lines.append('  </resources>')
    model_lines.append('  <build>')
    model_lines.append(f'    <item objectid="{assembly_id}"/>')
    model_lines.append('  </build>')
    model_lines.append('</model>')
    
    model_xml = '\n'.join(model_lines)
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', rels_xml)
        zf.writestr('3D/3dmodel.model', model_xml)


def export_stl_pair(base_path, text_path, mesh_base, mesh_text):
    """Export co-located STL files sharing the exact same coordinate origin."""
    if mesh_base is not None:
        os.makedirs(os.path.dirname(os.path.abspath(base_path)), exist_ok=True)
        mesh_base.export(base_path)
    if mesh_text is not None:
        os.makedirs(os.path.dirname(os.path.abspath(text_path)), exist_ok=True)
        mesh_text.export(text_path)


def generate_preview_image(mesh_base, mesh_text, output_path, label="Tile"):
    """
    Generate an attractive 2-view preview render (Top View and Angled 3D Isometric View)
    showing realistic Ivory/Cream tile base and Dark Slate/Black text with dynamic bounding framing.
    """
    fig = plt.figure(figsize=(11, 5.5), dpi=150, facecolor='#181818')
    
    # Calculate bounding box with margin
    bounds = mesh_base.bounds
    min_xy = min(bounds[0][0], bounds[0][1])
    max_xy = max(bounds[1][0], bounds[1][1])
    span = max(max_xy - min_xy, 44.0)
    center_x = (bounds[0][0] + bounds[1][0]) / 2.0
    center_y = (bounds[0][1] + bounds[1][1]) / 2.0
    half_span = span * 0.58
    
    # 1. Angled 3D View
    ax1 = fig.add_subplot(1, 2, 1, projection='3d', facecolor='#181818')
    ax1.view_init(elev=50, azim=-55)
    ax1.set_box_aspect([1, 1, 0.35])
    
    base_polys = mesh_base.vertices[mesh_base.faces]
    col_base = Poly3DCollection(base_polys, facecolors='#FAF6EE', edgecolors='#D8D0C0', linewidths=0.15, alpha=0.98)
    ax1.add_collection3d(col_base)
    
    if mesh_text is not None:
        text_polys = mesh_text.vertices[mesh_text.faces]
        col_text = Poly3DCollection(text_polys, facecolors='#181818', edgecolors='#000000', linewidths=0.08, alpha=1.0)
        ax1.add_collection3d(col_text)
        
    ax1.set_xlim(center_x - half_span, center_x + half_span)
    ax1.set_ylim(center_y - half_span, center_y + half_span)
    ax1.set_zlim(0, 10)
    ax1.axis('off')
    ax1.set_title(f"{label} - 3D Isometric", color='#E8E8E8', fontsize=12, pad=12, weight='bold')
    
    # 2. Top-Down Orthographic View
    ax2 = fig.add_subplot(1, 2, 2, projection='3d', facecolor='#181818')
    ax2.view_init(elev=90, azim=-90)
    ax2.set_box_aspect([1, 1, 0.15])
    
    col_base_top = Poly3DCollection(base_polys, facecolors='#F6F1E6', edgecolors='#CEC4B2', linewidths=0.15, alpha=1.0)
    ax2.add_collection3d(col_base_top)
    
    if mesh_text is not None:
        col_text_top = Poly3DCollection(text_polys, facecolors='#111111', edgecolors='#000000', linewidths=0.08, alpha=1.0)
        ax2.add_collection3d(col_text_top)
        
    ax2.set_xlim(center_x - half_span, center_x + half_span)
    ax2.set_ylim(center_y - half_span, center_y + half_span)
    ax2.set_zlim(0, 10)
    ax2.axis('off')
    ax2.set_title(f"{label} - Top View (1.5\" / 38.1 mm)", color='#E8E8E8', fontsize=12, pad=12, weight='bold')
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)


def build_batch_plate(tile_specs, flat_to_flat=38.1, height=4.8, chamfer=0.8,
                      inlay_depth=0.8, emboss_height=0.6, spacing=4.0, cols=4, font_path=None):
    """
    Arranges multiple tiles into an interlocking hexagonal grid for batch printing.
    """
    all_base_meshes = []
    all_text_meshes = []
    
    # Honeycomb pitch
    r = flat_to_flat / 2.0
    R = r / np.cos(np.deg2rad(30))
    dx = (1.5 * R) + spacing
    dy = flat_to_flat + spacing
    
    for idx, (letter, score) in enumerate(tile_specs):
        col = idx % cols
        row = idx // cols
        
        offset_x = col * dx
        offset_y = row * dy + (col % 2) * (dy / 2.0)
        
        mb, mt = build_tile_pair(
            letter=letter, score=score, flat_to_flat=flat_to_flat,
            height=height, chamfer=chamfer, inlay_depth=inlay_depth,
            emboss_height=emboss_height, font_path=font_path
        )
        
        mb.apply_translation([offset_x, offset_y, 0])
        all_base_meshes.append(mb)
        
        if mt is not None:
            mt.apply_translation([offset_x, offset_y, 0])
            all_text_meshes.append(mt)
            
    plate_base = trimesh.util.concatenate(all_base_meshes)
    plate_text = trimesh.util.concatenate(all_text_meshes) if all_text_meshes else None
    
    # Center the entire plate around origin (0, 0)
    center = (plate_base.bounds[0] + plate_base.bounds[1]) / 2.0
    center[2] = 0.0 # keep Z on bed
    plate_base.apply_translation(-center)
    if plate_text is not None:
        plate_text.apply_translation(-center)
        
    return plate_base, plate_text


def generate_honeycomb_positions(n_tiles, flat_to_flat=38.1, spacing=3.5):
    """
    Generate mathematically verified collision-free hexagonal coordinates
    for a 256mm x 256mm build plate with guaranteed top/rear clearance for wipe towers.
    """
    r = flat_to_flat / 2.0
    R = r / np.cos(np.deg2rad(30))
    dx = (1.5 * R) + spacing
    dy = flat_to_flat + spacing
    
    positions = []
    if n_tiles == 25:
        # 5 cols x 5 rows = 25 tiles
        for c in range(-2, 3):
            for row in range(-2, 3):
                x = c * dx
                y = row * dy + (abs(c) % 2) * (dy / 2.0)
                positions.append((x, y))
    elif n_tiles == 24:
        # 5 cols: [5, 5, 4, 5, 5] = 24 tiles
        row_counts = [5, 5, 4, 5, 5]
        for c, count in zip(range(-2, 3), row_counts):
            r_start = -(count // 2)
            for r_idx in range(count):
                row = r_start + r_idx
                x = c * dx
                y = row * dy + (abs(c) % 2) * (dy / 2.0)
                positions.append((x, y))
    elif n_tiles == 26:
        # 6 cols: [4, 5, 4, 5, 4, 4] = 26 tiles
        row_counts = [4, 5, 4, 5, 4, 4]
        for c, count in zip(range(-3, 3), row_counts):
            r_start = -(count // 2)
            for r_idx in range(count):
                row = r_start + r_idx
                x = (c + 0.5) * dx
                y = row * dy + (abs(c) % 2) * (dy / 2.0)
                positions.append((x, y))
    else:
        cols = 5
        for idx in range(n_tiles):
            c = (idx % cols) - (cols // 2)
            row = (idx // cols) - 2
            x = c * dx
            y = row * dy + (abs(c) % 2) * (dy / 2.0)
            positions.append((x, y))
            
    # Center and shift down slightly (12mm) to give ample top wipe tower clearance
    pts = np.array(positions)
    c_y = (pts[:, 1].min() + pts[:, 1].max()) / 2.0
    c_x = (pts[:, 0].min() + pts[:, 0].max()) / 2.0
    final_pos = [(x - c_x, y - c_y - 12.0) for (x, y) in positions]
    
    # Sort top-to-bottom, left-to-right for clean reading order
    def sort_key(pt):
        row_band = round(-pt[1] / (dy / 2.0))
        return (row_band, pt[0])
        
    return sorted(final_pos, key=sort_key)


def build_256mm_plate(tile_specs, flat_to_flat=38.1, height=4.8, chamfer=0.8,
                      inlay_depth=0.8, emboss_height=0.6, spacing=3.5, font_path=None):
    """
    Arranges tiles onto a 256mm x 256mm build plate with guaranteed >= 3.5mm spacing
    and ample clearance for the wipe tower anywhere along the top.
    """
    positions = generate_honeycomb_positions(len(tile_specs), flat_to_flat=flat_to_flat, spacing=spacing)
    
    all_base_meshes = []
    all_text_meshes = []
    
    for (letter, score), (px, py) in zip(tile_specs, positions):
        letter_sz = 22.0 if score == "" and len(letter) > 0 and (letter.isdigit() or letter in '+-x/=?!') else 18.5
        mb, mt = build_tile_pair(
            letter=letter, score=score, flat_to_flat=flat_to_flat,
            height=height, chamfer=chamfer, inlay_depth=inlay_depth,
            emboss_height=emboss_height,
            font_path=font_path, letter_size=letter_sz, score_size=7.0
        )
        mb.apply_translation([px, py, 0])
        all_base_meshes.append(mb)
        if mt is not None:
            mt.apply_translation([px, py, 0])
            all_text_meshes.append(mt)
            
    plate_base = trimesh.util.concatenate(all_base_meshes)
    plate_text = trimesh.util.concatenate(all_text_meshes) if all_text_meshes else None
    
    return plate_base, plate_text


def main():
    parser = argparse.ArgumentParser(description="Dual-Color Hexagonal Scrabble 3D Tile Generator")
    parser.add_argument("--letter", type=str, help="Generate a single letter tile (e.g. 'A')")
    parser.add_argument("--score", type=str, default=None, help="Custom score number (default: official Scrabble score)")
    parser.add_argument("--number", type=str, help="Generate a single number tile (e.g. '7')")
    parser.add_argument("--word", type=str, help="Generate tiles for a specific word (e.g. 'SCRABBLE')")
    parser.add_argument("--all", action="store_true", help="Generate complete A-Z, 0-9, and special character sets")
    parser.add_argument("--plates", action="store_true", help="Generate ready-to-slice batch build plates")
    parser.add_argument("--size", type=float, default=38.1, help="Tile flat-to-flat diameter in mm (default: 38.1 = 1.5 in)")
    parser.add_argument("--height", type=float, default=4.8, help="Tile height in mm (default: 4.8)")
    parser.add_argument("--chamfer", type=float, default=0.8, help="Top perimeter chamfer in mm (default: 0.8)")
    parser.add_argument("--inlay-depth", type=float, default=0.8, help="Inlay depth in mm (default: 0.8)")
    parser.add_argument("--embossed", type=float, default=0.6, help="Raised text height above tile in mm (default: 0.6 = tactile embossed)")
    parser.add_argument("--font", type=str, default=None, help="Path to custom TTF font")
    parser.add_argument("--outdir", type=str, default="output", help="Output directory path")
    
    args = parser.parse_args()
    
    outdir = os.path.abspath(args.outdir)
    dir_3mf = os.path.join(outdir, "3mf")
    dir_stl = os.path.join(outdir, "stl")
    dir_plates = os.path.join(outdir, "plates")
    dir_previews = os.path.join(outdir, "previews")
    
    os.makedirs(dir_3mf, exist_ok=True)
    os.makedirs(dir_stl, exist_ok=True)
    os.makedirs(dir_plates, exist_ok=True)
    os.makedirs(dir_previews, exist_ok=True)
    
    font_path = args.font or find_default_font()
    print(f"[CAD] Using font: {font_path}")
    print(f"[CAD] Tile dimensions: Diameter={args.size:.1f}mm (1.5in), Height={args.height:.1f}mm, Chamfer={args.chamfer:.1f}mm, Inlay={args.inlay_depth:.1f}mm")
    
    # 1. Single Letter Tile
    if args.letter:
        let = args.letter.upper()
        sc = args.score if args.score is not None else SCRABBLE_POINTS.get(let, "")
        print(f"Generating Tile '{let}' (Score: {sc})...")
        mb, mt = build_tile_pair(
            letter=let, score=sc, flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed,
            font_path=font_path
        )
        
        name = f"tile_{let}_score{sc if sc else 'none'}"
        mf_path = os.path.join(dir_3mf, f"{name}.3mf")
        stl_b = os.path.join(dir_stl, f"{name}_base.stl")
        stl_t = os.path.join(dir_stl, f"{name}_text.stl")
        img_path = os.path.join(dir_previews, f"{name}.png")
        
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, "Tile_Text": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        generate_preview_image(mb, mt, img_path, label=f"Tile '{let}' ({sc} pts)")
        print(f" -> Saved 3MF: {mf_path}")
        print(f" -> Saved STL: {stl_b} & {stl_t}")
        print(f" -> Saved Preview: {img_path}")
        return

    # 2. Single Number Tile
    if args.number:
        num = args.number
        print(f"Generating Number Tile '{num}'...")
        mb, mt = build_tile_pair(
            letter=num, score="", flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed,
            font_path=font_path, letter_size=19.0
        )
        name = f"tile_num_{num}"
        mf_path = os.path.join(dir_3mf, f"{name}.3mf")
        stl_b = os.path.join(dir_stl, f"{name}_base.stl")
        stl_t = os.path.join(dir_stl, f"{name}_text.stl")
        img_path = os.path.join(dir_previews, f"{name}.png")
        
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, "Tile_Text": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        generate_preview_image(mb, mt, img_path, label=f"Number Tile '{num}'")
        print(f" -> Saved 3MF: {mf_path}")
        print(f" -> Saved Preview: {img_path}")
        return

    # 3. Word Tiles
    if args.word:
        w = args.word.upper()
        print(f"Generating tiles for word: '{w}'...")
        for i, char in enumerate(w):
            sc = SCRABBLE_POINTS.get(char, "")
            mb, mt = build_tile_pair(
                letter=char, score=sc, flat_to_flat=args.size, height=args.height,
                chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed,
                font_path=font_path
            )
            name = f"word_{w}_pos{i+1}_{char}"
            mf_path = os.path.join(dir_3mf, f"{name}.3mf")
            export_multimaterial_3mf(mf_path, {"Tile_Base": mb, "Tile_Text": mt})
            export_stl_pair(os.path.join(dir_stl, f"{name}_base.stl"), os.path.join(dir_stl, f"{name}_text.stl"), mb, mt)
        print(f" -> Generated {len(w)} tiles for '{w}' in {dir_3mf}")
        return

    # 4. Generate Full Set & Plates
    print("\n--- Generating Complete English Scrabble Alphabet (A-Z + Blank) ---")
    letters_list = [chr(c) for c in range(ord('A'), ord('Z') + 1)] + ['BLANK']
    for let in letters_list:
        sc = SCRABBLE_POINTS.get(let, '0')
        disp_let = "" if let == "BLANK" else let
        disp_sc = "" if let == "BLANK" else sc
        mb, mt = build_tile_pair(
            letter=disp_let, score=disp_sc, flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed,
            font_path=font_path
        )
        name = f"tile_{let}_score{sc}"
        mf_path = os.path.join(dir_3mf, f"{name}.3mf")
        stl_b = os.path.join(dir_stl, f"{name}_base.stl")
        stl_t = os.path.join(dir_stl, f"{name}_text.stl")
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, "Tile_Text": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        
        if let in ['A', 'B', 'H', 'Q', 'Z', 'BLANK']:
            generate_preview_image(mb, mt, os.path.join(dir_previews, f"{name}.png"), label=f"Tile '{let}' ({sc} pts)")
            
    print(f" -> Saved {len(letters_list)} letter tiles to {dir_3mf}")
    
    print("\n--- Generating Number Set (0-9) & Math Symbols (+, -, x, /, =, ?, !) ---")
    numbers_and_syms = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '-', 'x', '/', '=', '?', '!']
    for sym in numbers_and_syms:
        clean_name = {'+': 'plus', '-': 'minus', 'x': 'multiply', '/': 'divide', '=': 'equals', '?': 'question', '!': 'exclamation'}.get(sym, f"num_{sym}")
        mb, mt = build_tile_pair(
            letter=sym, score="", flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed,
            font_path=font_path, letter_size=19.0
        )
        name = f"tile_{clean_name}"
        mf_path = os.path.join(dir_3mf, f"{name}.3mf")
        stl_b = os.path.join(dir_stl, f"{name}_base.stl")
        stl_t = os.path.join(dir_stl, f"{name}_text.stl")
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, "Tile_Text": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        
        if sym in ['7', '8', '?', '+']:
            generate_preview_image(mb, mt, os.path.join(dir_previews, f"{name}.png"), label=f"Tile '{sym}'")
            
    print(f" -> Saved {len(numbers_and_syms)} number/symbol tiles to {dir_3mf}")
    
    print("\n--- Generating Honeycomb Batch Print Plates ---")
    # Plate 1: Letters A to M (13 tiles)
    plate_am_specs = [(chr(c), SCRABBLE_POINTS[chr(c)]) for c in range(ord('A'), ord('N'))]
    p1_b, p1_t = build_batch_plate(plate_am_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, cols=4, font_path=font_path)
    export_multimaterial_3mf(os.path.join(dir_plates, "plate_letters_A_M.3mf"), {"Plate_Base": p1_b, "Plate_Text": p1_t})
    generate_preview_image(p1_b, p1_t, os.path.join(dir_previews, "plate_letters_A_M.png"), label="Batch Plate: Letters A to M")
    print(" -> Saved Batch Plate: plate_letters_A_M.3mf (13 tiles)")

    # Plate 2: Letters N to Z + Blank (14 tiles)
    plate_nz_specs = [(chr(c), SCRABBLE_POINTS[chr(c)]) for c in range(ord('N'), ord('Z') + 1)] + [("", "0")]
    p2_b, p2_t = build_batch_plate(plate_nz_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, cols=4, font_path=font_path)
    export_multimaterial_3mf(os.path.join(dir_plates, "plate_letters_N_Z_Blank.3mf"), {"Plate_Base": p2_b, "Plate_Text": p2_t})
    generate_preview_image(p2_b, p2_t, os.path.join(dir_previews, "plate_letters_N_Z_Blank.png"), label="Batch Plate: Letters N to Z + Blank")
    print(" -> Saved Batch Plate: plate_letters_N_Z_Blank.3mf (14 tiles)")

    # Plate 3: Numbers 0 to 9 + Symbols (17 tiles)
    plate_num_specs = [(sym, "") for sym in numbers_and_syms]
    p3_b, p3_t = build_batch_plate(plate_num_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, cols=4, font_path=font_path)
    export_multimaterial_3mf(os.path.join(dir_plates, "plate_numbers_and_symbols.3mf"), {"Plate_Base": p3_b, "Plate_Text": p3_t})
    generate_preview_image(p3_b, p3_t, os.path.join(dir_previews, "plate_numbers_and_symbols.png"), label="Batch Plate: Numbers 0-9 & Math Symbols")
    print(" -> Saved Batch Plate: plate_numbers_and_symbols.3mf (17 tiles)")

    # -------------------------------------------------------------------------
    # Full 256mm Build Plates (Bambu Lab X1/P1/A1 / Prusa XL / Voron 250+ Bed)
    # -------------------------------------------------------------------------
    print("\n--- Generating Full 256mm x 256mm Build Plates (with Guaranteed Zero-Overlap Spacing) ---")
    
    # 256mm Reference Plate: Complete Alphabet (A through Z - 26 Tiles)
    plate_256_az_specs = [(chr(c), SCRABBLE_POINTS[chr(c)]) for c in range(ord('A'), ord('Z') + 1)]
    p256_az_b, p256_az_t = build_256mm_plate(plate_256_az_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, font_path=font_path)
    export_multimaterial_3mf(os.path.join(dir_plates, "plate_full_256_alphabet_A_Z_26tiles.3mf"), {"Plate_Base": p256_az_b, "Plate_Text": p256_az_t})
    generate_preview_image(p256_az_b, p256_az_t, os.path.join(dir_previews, "plate_full_256_alphabet_A_Z.png"), label="Full 256mm Bed: Alphabet A to Z (26 Tiles + Wipe Tower Zone)")
    print(" -> Saved 256mm Plate: plate_full_256_alphabet_A_Z_26tiles.3mf (26 tiles)")

    # 256mm Reference Plate: Numbers 0-9, Math Symbols, Extra Vowels, & 2 Blanks (26 Tiles)
    plate_256_extra_specs = [
        ('0', ''), ('1', ''), ('2', ''), ('3', ''), ('4', ''),
        ('5', ''), ('6', ''), ('7', ''), ('8', ''), ('9', ''),
        ('+', ''), ('-', ''), ('x', ''), ('/', ''), ('=', ''),
        ('?', ''), ('!', ''),
        ('A', '1'), ('E', '1'), ('I', '1'), ('O', '1'), ('U', '1'), ('Y', '4'),
        ('', '0'), ('', '0'), ('E', '1')
    ]
    p256_extra_b, p256_extra_t = build_256mm_plate(plate_256_extra_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, font_path=font_path)
    export_multimaterial_3mf(os.path.join(dir_plates, "plate_full_256_numbers_and_extras_26tiles.3mf"), {"Plate_Base": p256_extra_b, "Plate_Text": p256_extra_t})
    generate_preview_image(p256_extra_b, p256_extra_t, os.path.join(dir_previews, "plate_full_256_numbers_and_extras.png"), label="Full 256mm Bed: Numbers, Symbols, Extras (26 Tiles)")
    print(" -> Saved 256mm Plate: plate_full_256_numbers_and_extras_26tiles.3mf (26 tiles)")

    # -------------------------------------------------------------------------
    # Proportional Scrabble Master Set (100 Tiles = 4 Plates of 25 on 256mm Bed)
    # -------------------------------------------------------------------------
    print("\n--- Generating Official 100-Tile Scrabble Set (4 Plates of 25 Tiles on 256mm Bed) ---")
    scrabble_dist = {
        'E': 12, 'A': 9, 'I': 9, 'O': 8, 'N': 6, 'R': 6, 'T': 6,
        'D': 4, 'L': 4, 'S': 4, 'U': 4, 'G': 3,
        'B': 2, 'C': 2, 'F': 2, 'H': 2, 'M': 2, 'P': 2, 'V': 2, 'W': 2, 'Y': 2, 'BLANK': 2,
        'J': 1, 'K': 1, 'Q': 1, 'X': 1, 'Z': 1
    }
    scrabble_pool = []
    for k in sorted(scrabble_dist.keys()):
        disp_k = "" if k == 'BLANK' else k
        sc = SCRABBLE_POINTS.get(k, '0')
        scrabble_pool.extend([(disp_k, sc)] * scrabble_dist[k])
        
    for p_idx in range(4):
        p_specs = scrabble_pool[p_idx * 25 : (p_idx + 1) * 25]
        p_b, p_t = build_256mm_plate(p_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, font_path=font_path)
        p_filename = f"plate_256_scrabble_100set_plate{p_idx+1}_of_4_25tiles.3mf"
        export_multimaterial_3mf(os.path.join(dir_plates, p_filename), {"Plate_Base": p_b, "Plate_Text": p_t})
        generate_preview_image(p_b, p_t, os.path.join(dir_previews, f"plate_256_scrabble_100set_plate{p_idx+1}.png"), label=f"Scrabble Set (Plate {p_idx+1}/4 - 25 Tiles)")
        print(f" -> Saved Scrabble Plate {p_idx+1}/4: {p_filename}")

    # -------------------------------------------------------------------------
    # Proportional Bananagrams / Hive-Swarm Master Set (144 Tiles = 6 Plates of 24 on 256mm Bed)
    # WITH OFFICIAL SCRABBLE POINT VALUES ON ALL TILES (Universal Multi-Game Use)
    # -------------------------------------------------------------------------
    print("\n--- Generating Official 144-Tile Universal Hive-Swarm / Bananagrams Set (6 Plates of 24 Tiles with Point Values) ---")
    banana_dist = {
        'E': 18, 'A': 13, 'I': 12, 'O': 11, 'T': 9, 'R': 9, 'N': 8,
        'D': 6, 'S': 6, 'U': 6, 'L': 5, 'G': 4,
        'B': 3, 'C': 3, 'F': 3, 'H': 3, 'M': 3, 'P': 3, 'V': 3, 'W': 3, 'Y': 3,
        'J': 2, 'K': 2, 'Q': 2, 'X': 2, 'Z': 2
    }
    banana_pool = []
    for k in sorted(banana_dist.keys()):
        sc = SCRABBLE_POINTS.get(k, '1')
        banana_pool.extend([(k, sc)] * banana_dist[k])
        
    for p_idx in range(6):
        p_specs = banana_pool[p_idx * 24 : (p_idx + 1) * 24]
        p_b, p_t = build_256mm_plate(p_specs, flat_to_flat=args.size, height=args.height, emboss_height=args.embossed, font_path=font_path)
        p_filename = f"plate_256_hiveswarm_144set_plate{p_idx+1}_of_6_24tiles.3mf"
        export_multimaterial_3mf(os.path.join(dir_plates, p_filename), {"Plate_Base": p_b, "Plate_Text": p_t})
        generate_preview_image(p_b, p_t, os.path.join(dir_previews, f"plate_256_hiveswarm_144set_plate{p_idx+1}.png"), label=f"Universal Hive-Swarm / Scrabble Set (Plate {p_idx+1}/6 - 24 Tiles)")
        print(f" -> Saved Hive-Swarm Plate {p_idx+1}/6: {p_filename}")

    print("\n[SUCCESS] All 3MF, STL, batch plates, and preview renders generated successfully!")


if __name__ == "__main__":
    main()

