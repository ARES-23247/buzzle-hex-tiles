import os
import math
import zipfile
from xml.sax.saxutils import quoteattr
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import translate, rotate

from generate_tiles import (
    char_to_polygons, find_default_font,
    triangulate_shapely_poly
)
from render_new_buzzle_board import (
    POCKET_FLAT, WALL_RIB, CELL_FLAT, r, R,
    make_flat_hex_pts, get_buzzle_multiplier
)

OUTPUT_DIR = "archive/legacy-outputs/output/board"
DIR_3MF = os.path.join(OUTPUT_DIR, "3mf")
os.makedirs(DIR_3MF, exist_ok=True)

# 3D Board Heights
TOTAL_HEIGHT = 4.00       # 4.0mm total board thickness
BASE_FLOOR = 2.00         # 2.0mm solid bottom base
POCKET_DEPTH = 2.00       # 2.0mm deep pocket
INLAY_THICKNESS = 0.80    # 0.8mm inlay depth (Z: 1.2 to 2.0)
TEXT_THICKNESS = 0.40     # 0.4mm flush contrast text (Z: 1.6 to 2.0)

# Dovetail Interlocking Specs
DOVETAIL_NECK = 12.0
DOVETAIL_HEAD = 18.0
DOVETAIL_LEN = 8.0
DOVETAIL_TOL = 0.20       # 0.20mm clearance on each mating surface

def extrude_poly(poly, z_min, z_max):
    if poly is None or poly.is_empty:
        return None
    polys = [poly] if isinstance(poly, Polygon) else list(poly.geoms)
    meshes = []
    for polygon in polys:
        if not isinstance(polygon, Polygon) or polygon.area < 1e-7:
            continue
        vertices, faces = triangulate_shapely_poly(polygon)
        mesh = trimesh.creation.extrude_triangulation(vertices, faces, z_max - z_min)
        mesh.apply_translation([0, 0, z_min])
        if not mesh.is_volume:
            # Earcut can leave coincident bridge edges along aligned hex holes.
            # Constrained triangulation preserves every polygon boundary edge.
            from shapely import constrained_delaunay_triangles
            vertices, faces, indices = [], [], {}
            for triangle in constrained_delaunay_triangles(polygon).geoms:
                face = []
                for xy in list(triangle.exterior.coords)[:3]:
                    if xy not in indices:
                        indices[xy] = len(vertices)
                        vertices.append(xy)
                    face.append(indices[xy])
                faces.append(face)
            mesh = trimesh.creation.extrude_triangulation(np.array(vertices), np.array(faces), z_max-z_min)
            mesh.apply_translation([0, 0, z_min])
        if not mesh.is_volume:
            raise ValueError("Extrusion must be a closed, consistently oriented solid")
        meshes.append(mesh)
    return trimesh.util.concatenate(meshes) if meshes else None


def make_dovetail_polygon(cx, cy, angle_deg, is_male=True):
    tol = 0.0 if is_male else DOVETAIL_TOL
    w_n = DOVETAIL_NECK - tol * 2.0 if is_male else DOVETAIL_NECK + tol * 2.0
    w_h = DOVETAIL_HEAD - tol * 2.0 if is_male else DOVETAIL_HEAD + tol * 2.0
    l_d = DOVETAIL_LEN - tol if is_male else DOVETAIL_LEN + tol
    
    pts = [
        [-w_n / 2.0, 0.0],
        [-w_h / 2.0, l_d],
        [w_h / 2.0, l_d],
        [w_n / 2.0, 0.0]
    ]
    p = Polygon(pts)
    p_rot = rotate(p, angle_deg, origin=(0, 0))
    return translate(p_rot, xoff=cx, yoff=cy)

def export_multimaterial_3mf(filepath, parts_list, assembly_name="BUZZLE_Assembly", palette=None):
    """
    Exports a 4-color multi-material 3MF package with embedded 3MF Material Extension (m:colorgroup)
    and Snapmaker Orca / OrcaSlicer optimized object labels.
    
    parts_list is a list of tuples: (part_name, mesh, color_index)
      color_index:
        0 = Slot 1: Charcoal Black (#1F212B)
        1 = Slot 2: Neon Lime      (#AEEA00)
        2 = Slot 3: Hot Pink       (#E91E63)
        3 = Slot 4: Cyan Blue      (#00E5FF)
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
        '<model unit="millimeter" xml:lang="en-US"',
        '       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"',
        '       xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
        '  <resources>',
        '    <m:colorgroup id="100">',
        '      <m:color color="#1F212BFF"/> <!-- Slot 1: Charcoal Black -->',
        '      <m:color color="#AEEA00FF"/> <!-- Slot 2: Neon Lime -->',
        '      <m:color color="#E91E63FF"/> <!-- Slot 3: Hot Pink -->',
        '      <m:color color="#00E5FFFF"/> <!-- Slot 4: Cyan Blue -->',
        '    </m:colorgroup>'
    ]
    
    if palette is not None:
        if len(palette) != 4:
            raise ValueError("Palette must contain exactly four colors")
        for index, color in enumerate(palette):
            if len(color) != 7 or color[0] != "#" or any(c not in "0123456789abcdefABCDEF" for c in color[1:]):
                raise ValueError("Palette colors must be #RRGGBB values")
            model_lines[6 + index] = f'      <m:color color="{color}FF"/>'

    obj_id = 1
    comp_ids = []
    
    for name, mesh, c_idx in parts_list:
        if mesh is None or len(mesh.vertices) == 0:
            continue
        if c_idx not in range(4):
            raise ValueError("Only four material slots are supported")
        model_lines.append(f'    <object id="{obj_id}" name={quoteattr(name)} type="model" pid="100" pindex="{c_idx}">')
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
    model_lines.append(f'    <object id="{assembly_id}" name={quoteattr(assembly_name)} type="model">')
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

def generate_all_7_plates():
    font_path = find_default_font()
    print("Using font:", font_path)
    
    # 1. Build All Cells in Global Coordinates
    cells = []
    for x in range(-8, 9):
        for y in range(max(-8, -x-8), min(8, -x+8) + 1):
            z = -x - y
            cx = -z * r * math.sqrt(3.0)
            cy = (y - x) * r
            label, bg_col, txt_col, desc = get_buzzle_multiplier(x, y, z)
            dist = max(abs(x), abs(y), abs(z))
            cells.append({
                "coord": (x, y, z), "dist": dist,
                "cx": cx, "cy": cy,
                "label": label, "desc": desc
            })

    # =========================================================================
    # PLATE 1: Central Rosette Hub (37 Cells, 7-Tile Diameter)
    # =========================================================================
    print("\n=======================================================")
    print("PLATE 1: Central Rosette Hub (37 Cells, 7-Tile Dia)")
    print("=======================================================")
    hub_cells = [c for c in cells if c["dist"] <= 3]
    
    hub_outer_hexes = [Polygon(make_flat_hex_pts(c["cx"], c["cy"], CELL_FLAT)) for c in hub_cells]
    hub_poly = unary_union(hub_outer_hexes).buffer(0.01).buffer(-0.01)
    
    # Dovetail sockets on outer flats (6 flats at 0, 60, 120, 180, 240, 300 deg)
    dovetail_sockets = []
    for i in range(6):
        a_deg = i * 60
        rad_a = math.radians(a_deg)
        for offset_perp in [-CELL_FLAT * 0.75, CELL_FLAT * 0.75]:
            dist_flat = 3.5 * CELL_FLAT - 1.0
            sx = dist_flat * math.cos(rad_a) - offset_perp * math.sin(rad_a)
            sy = dist_flat * math.sin(rad_a) + offset_perp * math.cos(rad_a)
            sock = make_dovetail_polygon(sx, sy, a_deg - 90, is_male=False)
            dovetail_sockets.append(sock)
            
    hub_poly_with_sockets = hub_poly.difference(unary_union(dovetail_sockets)) if dovetail_sockets else hub_poly
    mesh_hub_base = extrude_poly(hub_poly_with_sockets, 0.0, BASE_FLOOR)
    
    hub_pockets = [Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT)) for c in hub_cells]
    ribs_poly = hub_poly.difference(unary_union(hub_pockets))
    if dovetail_sockets:
        ribs_poly = ribs_poly.difference(unary_union(dovetail_sockets))
    mesh_hub_ribs = extrude_poly(ribs_poly, BASE_FLOOR, TOTAL_HEIGHT)
    
    pink_inlays = []
    blue_inlays = []
    text_emboss = []
    
    for c in hub_cells:
        if c["desc"] == "START":
            pink_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
            for sp in char_to_polygons("★", font_path, size=15):
                text_emboss.append(translate(sp, c["cx"], c["cy"]))
        elif c["desc"] == "DOUBLE LETTER":
            blue_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
            for dp in char_to_polygons("DL", font_path, size=8):
                text_emboss.append(translate(dp, c["cx"], c["cy"]))

    mesh_hub_pink = extrude_poly(unary_union(pink_inlays), BASE_FLOOR - INLAY_THICKNESS, BASE_FLOOR)
    mesh_hub_blue = extrude_poly(unary_union(blue_inlays), BASE_FLOOR - INLAY_THICKNESS, BASE_FLOOR)
    mesh_hub_text = extrude_poly(unary_union(text_emboss), BASE_FLOOR - TEXT_THICKNESS, BASE_FLOOR)
    
    # Snapmaker Orca optimized names with explicit slot numbers and color names:
    hub_parts_list = [
        ("[Slot 1 - Charcoal] Base Floor & Pockets", mesh_hub_base, 0),
        ("[Slot 2 - Neon Lime] Honeycomb Divider Ribs", mesh_hub_ribs, 1),
        ("[Slot 3 - Hot Pink] Center Start Star Inlay", mesh_hub_pink, 2),
        ("[Slot 4 - Cyan Blue] DL Letter Inlays", mesh_hub_blue, 3),
        ("[Slot 1 - Charcoal] Embossed Contrast Text", mesh_hub_text, 0)
    ]
    
    path_hub_3mf = os.path.join(DIR_3MF, "Plate_1_Center_Rosette_Hub_7_Tile.3mf")
    export_multimaterial_3mf(path_hub_3mf, hub_parts_list, assembly_name="Plate_1_Center_Hub_Assembly")
    print(f" -> Exported Plate 1: {path_hub_3mf}")
    print(f"    Dimensions: {mesh_hub_base.extents[0]:.1f} x {mesh_hub_base.extents[1]:.1f} x 4.0 mm")

    # =========================================================================
    # PLATES 2–7: 6 Dedicated Outer Wedges
    # =========================================================================
    outer_cells = [c for c in cells if c["dist"] > 3]
    
    wedge_configs = [
        (0, "Plate_2_Wedge_North", 90, 60, 120),
        (1, "Plate_3_Wedge_NorthEast", 30, 0, 60),
        (2, "Plate_4_Wedge_SouthEast", 330, 300, 360),
        (3, "Plate_5_Wedge_South", 270, 240, 300),
        (4, "Plate_6_Wedge_SouthWest", 210, 180, 240),
        (5, "Plate_7_Wedge_NorthWest", 150, 120, 180),
    ]

    for s_idx, w_name, apex_deg, ang_min, ang_max in wedge_configs:
        print(f"\n-------------------------------------------------------")
        print(f"{w_name} (Apex on board at {apex_deg} deg)")
        print(f"-------------------------------------------------------")
        
        w_cells = []
        for c in outer_cells:
            ang = (math.degrees(math.atan2(c["cy"], c["cx"])) + 360) % 360
            if ang_min <= ang < ang_max:
                w_cells.append(c)
            elif ang_min == 0 and ang >= 359.99:
                w_cells.append(c)
                
        print(f"  Cells in wedge: {len(w_cells)}")
        
        w_hexes = [Polygon(make_flat_hex_pts(c["cx"], c["cy"], CELL_FLAT)) for c in w_cells]
        w_poly = unary_union(w_hexes).buffer(0.01).buffer(-0.01)
        
        dovetail_keys = []
        flat_ang_deg = round(apex_deg / 60) * 60
        rad_fa = math.radians(flat_ang_deg)
        for offset_perp in [-CELL_FLAT * 0.75, CELL_FLAT * 0.75]:
            dist_flat = 3.5 * CELL_FLAT - 1.0
            kx = dist_flat * math.cos(rad_fa) - offset_perp * math.sin(rad_fa)
            ky = dist_flat * math.sin(rad_fa) + offset_perp * math.cos(rad_fa)
            dkey = make_dovetail_polygon(kx, ky, flat_ang_deg + 90, is_male=True)
            dovetail_keys.append(dkey)
            
        w_poly_with_keys = unary_union([w_poly] + dovetail_keys)
        mesh_w_base = extrude_poly(w_poly_with_keys, 0.0, BASE_FLOOR)
        
        w_pockets = [Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT)) for c in w_cells]
        w_ribs_poly = w_poly.difference(unary_union(w_pockets))
        mesh_w_ribs = extrude_poly(w_ribs_poly, BASE_FLOOR, TOTAL_HEIGHT)
        
        w_lime_inlays = []
        w_pink_inlays = []
        w_blue_inlays = []
        w_text_emboss = []
        
        for c in w_cells:
            if c["desc"] == "TRIPLE WORD":
                w_lime_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
                for tp in char_to_polygons("TW", font_path, size=8):
                    w_text_emboss.append(translate(tp, c["cx"], c["cy"]))
            elif c["desc"] == "DOUBLE WORD":
                w_pink_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
                for dp in char_to_polygons("DW", font_path, size=8):
                    w_text_emboss.append(translate(dp, c["cx"], c["cy"]))
            elif c["desc"] == "KEY WILD (DW)":
                w_pink_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
                for dp in char_to_polygons("DW", font_path, size=7):
                    w_text_emboss.append(translate(dp, c["cx"], c["cy"] + 2.0))
                for kp in char_to_polygons("KEY", font_path, size=5):
                    w_text_emboss.append(translate(kp, c["cx"], c["cy"] - 3.5))
            elif c["desc"] == "TRIPLE LETTER":
                w_blue_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
                for tp in char_to_polygons("TL", font_path, size=8):
                    w_text_emboss.append(translate(tp, c["cx"], c["cy"]))
            elif c["desc"] == "DOUBLE LETTER":
                w_blue_inlays.append(Polygon(make_flat_hex_pts(c["cx"], c["cy"], POCKET_FLAT - 0.2)))
                for dp in char_to_polygons("DL", font_path, size=8):
                    w_text_emboss.append(translate(dp, c["cx"], c["cy"]))

        mesh_w_lime = extrude_poly(unary_union(w_lime_inlays), BASE_FLOOR - INLAY_THICKNESS, BASE_FLOOR) if w_lime_inlays else None
        mesh_w_pink = extrude_poly(unary_union(w_pink_inlays), BASE_FLOOR - INLAY_THICKNESS, BASE_FLOOR) if w_pink_inlays else None
        mesh_w_blue = extrude_poly(unary_union(w_blue_inlays), BASE_FLOOR - INLAY_THICKNESS, BASE_FLOOR) if w_blue_inlays else None
        mesh_w_text = extrude_poly(unary_union(w_text_emboss), BASE_FLOOR - TEXT_THICKNESS, BASE_FLOOR) if w_text_emboss else None
        
        center_pt = (mesh_w_base.bounds[0] + mesh_w_base.bounds[1]) / 2.0
        center_pt[2] = 0.0
        
        rot_bed_deg = 90 - apex_deg
        rot_matrix = trimesh.transformations.rotation_matrix(math.radians(rot_bed_deg), [0, 0, 1], [0, 0, 0])
        
        wedge_submeshes = [mesh_w_base, mesh_w_ribs, mesh_w_lime, mesh_w_pink, mesh_w_blue, mesh_w_text]
        for m in wedge_submeshes:
            if m is not None:
                m.apply_translation(-center_pt)
                m.apply_transform(rot_matrix)
                
        # Snapmaker Orca labeled parts list with color indices:
        wedge_parts_list = [
            ("[Slot 1 - Charcoal] Base Floor & Pockets", mesh_w_base, 0),
            ("[Slot 2 - Neon Lime] Honeycomb Divider Ribs", mesh_w_ribs, 1),
            ("[Slot 2 - Neon Lime] TW Triple Word Inlays", mesh_w_lime, 1),
            ("[Slot 3 - Hot Pink] DW & Key Wild Inlays", mesh_w_pink, 2),
            ("[Slot 4 - Cyan Blue] TL & DL Letter Inlays", mesh_w_blue, 3),
            ("[Slot 1 - Charcoal] Embossed Contrast Text", mesh_w_text, 0)
        ]
        
        path_w_3mf = os.path.join(DIR_3MF, f"{w_name}.3mf")
        export_multimaterial_3mf(path_w_3mf, wedge_parts_list, assembly_name=f"{w_name}_Assembly")
        print(f"  -> Exported: {path_w_3mf}")
        print(f"     Print Bed Bounding Box: {mesh_w_base.extents[0]:.1f} x {mesh_w_base.extents[1]:.1f} x 4.0 mm")

if __name__ == "__main__":
    generate_all_7_plates()
