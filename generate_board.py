import os
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union, orient
from shapely.affinity import scale, translate, rotate
import shutil

from generate_tiles import (
    make_hex_points_2d, char_to_polygons, find_default_font,
    triangulate_shapely_poly, export_multimaterial_3mf
)

OUTPUT_DIR = "archive/legacy-outputs/output/board"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "3mf"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "previews"), exist_ok=True)

TILE_FLAT = 33.02
POCKET_FLAT = 33.80       # +0.78mm total clearance (+0.39mm per side)
WALL_THICKNESS = 2.20     # Heavy-duty 2.2mm structural rib dividers
POCKET_DEPTH = 2.00       # 2.0mm deep pocket
BASE_FLOOR = 2.00         # 2.0mm solid bottom base
TOTAL_HEIGHT = 4.00       # 4.00mm total board thickness
INLAY_TEXT_DEPTH = 0.80   # 0.80mm text inlay depth

PITCH_X = POCKET_FLAT + WALL_THICKNESS # 36.00 mm
PITCH_Y = PITCH_X * math.sqrt(3) / 2.0  # 31.18 mm

def extrude_poly(poly, z_min, z_max):
    if poly is None or poly.is_empty:
        return trimesh.Trimesh()
        
    polys = [poly] if isinstance(poly, Polygon) else list(poly.geoms)
    sub_meshes = []
    
    for p in polys:
        verts_2d, faces_2d = triangulate_shapely_poly(p)
        if len(verts_2d) == 0:
            continue
            
        n_v = len(verts_2d)
        v_bot = np.column_stack([verts_2d, np.full(n_v, z_min)])
        v_top = np.column_stack([verts_2d, np.full(n_v, z_max)])
        vertices = np.vstack([v_bot, v_top])
        
        f_bot = faces_2d[:, ::-1]
        f_top = faces_2d + n_v
        wall_faces = []
        
        ext_coords = np.array(p.exterior.coords)[:-1]
        ext_len = len(ext_coords)
        for i in range(ext_len):
            i_next = (i + 1) % ext_len
            wall_faces.append([i, i_next + n_v, i_next])
            wall_faces.append([i, i + n_v, i_next + n_v])
            
        curr = ext_len
        for interior in p.interiors:
            int_coords = np.array(interior.coords)[:-1]
            int_len = len(int_coords)
            for i in range(int_len):
                i_next = (i + 1) % int_len
                wall_faces.append([curr + i, curr + i_next, curr + i_next + n_v])
                wall_faces.append([curr + i, curr + i_next + n_v, curr + i + n_v])
            curr += int_len
            
        faces = np.vstack([f_bot, f_top, np.array(wall_faces, dtype=np.int64)])
        m = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
        sub_meshes.append(m)
        
    if not sub_meshes:
        return trimesh.Trimesh()
    return trimesh.util.concatenate(sub_meshes) if len(sub_meshes) > 1 else sub_meshes[0]

def get_cell_multiplier(q, r):
    dist = max(abs(q), abs(r), abs(-q-r))
    if dist == 0:
        return 1, "★"
    if dist == 6 and (abs(q) == 6 or abs(r) == 6 or abs(-q-r) == 6 or (q % 3 == 0 and r % 3 == 0)):
        return 2, "3W"
    if dist == 4 and (q == 0 or r == 0 or q+r == 0):
        return 4, "3L"
    if dist == 3:
        return 3, "2W"
    if dist == 2 and (q == 0 or r == 0 or q+r == 0):
        return 5, "2L"
    if dist == 5 and (abs(q) == 5 or abs(r) == 5 or abs(-q-r) == 5):
        return 5, "2L"
    return 0, ""

def generate_all_cells(radius=7):
    cells = []
    for q in range(-radius+1, radius):
        r1 = max(-radius+1, -q - radius + 1)
        r2 = min(radius - 1, -q + radius - 1)
        for r in range(r1, r2 + 1):
            px = PITCH_X * (q + r / 2.0)
            py = PITCH_Y * r * (2.0 / math.sqrt(3))
            mult_type, label = get_cell_multiplier(q, r)
            cells.append({
                'q': q, 'r': r, 'dist': max(abs(q), abs(r), abs(-q-r)),
                'px': px, 'py': py,
                'type': mult_type, 'label': label
            })
    return cells

def make_dovetail_key(cx, cy, angle_deg=0, w_neck=14.0, w_head=22.0, length=12.0, tol=0.0):
    pts = [
        [-w_neck/2.0 + tol, 0.0],
        [-w_head/2.0 + tol, length - tol],
        [w_head/2.0 - tol, length - tol],
        [w_neck/2.0 - tol, 0.0]
    ]
    p = Polygon(pts)
    p_rot = rotate(p, angle_deg, origin=(0, 0))
    return translate(p_rot, xoff=cx, yoff=cy)

all_cells = generate_all_cells(radius=7)
