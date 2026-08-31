"""
Dual-Color & 4-Color Hexagonal "Hive" 3D Printable Tile Generator
=================================================================
Generates 1.5 inch (38.1 mm) diameter hexagonal game tiles for the board game "Hive".
Includes complete base game and official expansions:
  - Queen Bee
  - Spider
  - Beetle
  - Grasshopper
  - Soldier Ant
  - Mosquito (Expansion)
  - Ladybug (Expansion)
  - Pillbug (Expansion)

Specifically includes 4-color multi-material plates (max 1 base color + 3 insect colors per plate)
for 4-color 3D printers and toolhead changers (Bambu AMS, Prusa XL, Voron, IDEX).
"""

import os
import sys
import argparse
import zipfile
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon, Point, box, LineString
from shapely.ops import unary_union
from shapely.affinity import rotate, scale, translate
from shapely.geometry.polygon import orient
import mapbox_earcut
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# Official Hive piece counts per player
HIVE_BASE_COUNTS = {
    'queen_bee': 1,
    'spider': 2,
    'beetle': 2,
    'grasshopper': 3,
    'ant': 3
}

HIVE_EXPANSION_COUNTS = {
    'mosquito': 1,
    'ladybug': 1,
    'pillbug': 1
}

HIVE_FULL_COUNTS = {**HIVE_BASE_COUNTS, **HIVE_EXPANSION_COUNTS}

INSECT_DISPLAY_NAMES = {
    'queen_bee': 'Queen Bee',
    'spider': 'Spider',
    'beetle': 'Beetle',
    'grasshopper': 'Grasshopper',
    'ant': 'Soldier Ant',
    'mosquito': 'Mosquito',
    'ladybug': 'Ladybug',
    'pillbug': 'Pillbug'
}

OFFICIAL_INSECT_HEX_COLORS = {
    'queen_bee': '#FFD600',    # Vibrant Yellow / Gold
    'spider': '#E65100',       # Brown / Burnt Orange
    'beetle': '#8E24AA',       # Purple / Violet
    'grasshopper': '#43A047',  # Green
    'ant': '#1E88E5',          # Blue
    'mosquito': '#9E9E9E',     # Silver / Gray
    'ladybug': '#E53935',      # Crimson Red
    'pillbug': '#00ACC1'       # Cyan / Teal
}


# ========================================================================
# 2D Geometry Primitives & Helpers
# ========================================================================

def make_circle(center, radius, num_points=36):
    angles = np.linspace(0, 2*np.pi, num_points, endpoint=False)
    pts = [[center[0] + radius*np.cos(a), center[1] + radius*np.sin(a)] for a in angles]
    return Polygon(pts)


def make_ellipse(center, rx, ry, num_points=36):
    angles = np.linspace(0, 2*np.pi, num_points, endpoint=False)
    pts = [[center[0] + rx*np.cos(a), center[1] + ry*np.sin(a)] for a in angles]
    return Polygon(pts)


def make_poly_line(pts, width):
    line = LineString(pts)
    return line.buffer(width / 2.0, cap_style=1, join_style=1)


def make_hex_points_2d(flat_to_flat):
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


def triangulate_shapely_poly(poly):
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


# ========================================================================
# Vector Silhouettes for Hive Insects
# ========================================================================

def build_queen_bee():
    head = make_circle((0, 4.8), 1.8)
    crown = Polygon([(-2.0, 5.2), (-2.0, 8.0), (-1.0, 6.6), (0, 8.6), (1.0, 6.6), (2.0, 8.0), (2.0, 5.2)])
    thorax = make_ellipse((0, 1.8), 2.5, 2.0)
    ab_outer = Polygon([(0, -7.5), (-3.0, -1.0), (3.0, -1.0)]).buffer(0.8, join_style=1)
    s1 = box(-4, -2.4, 4, -1.7)
    s2 = box(-3.5, -4.3, 3.5, -3.6)
    s3 = box(-2.5, -6.0, 2.5, -5.4)
    abdomen = ab_outer.difference(unary_union([s1, s2, s3]))
    wing_l = rotate(make_ellipse((-5.8, 3.0), 5.0, 1.8), -35, origin=(-5.8, 3.0))
    wing_r = rotate(make_ellipse((5.8, 3.0), 5.0, 1.8), 35, origin=(5.8, 3.0))
    wing_l2 = rotate(make_ellipse((-5.0, 1.0), 3.8, 1.4), -55, origin=(-5.0, 1.0))
    wing_r2 = rotate(make_ellipse((5.0, 1.0), 3.8, 1.4), 55, origin=(5.0, 1.0))
    ant_l = make_poly_line([(-0.8, 6.2), (-2.0, 8.2), (-3.2, 8.2)], 0.7)
    ant_r = make_poly_line([(0.8, 6.2), (2.0, 8.2), (3.2, 8.2)], 0.7)
    return unary_union([head, crown, thorax, abdomen, wing_l, wing_r, wing_l2, wing_r2, ant_l, ant_r])


def build_spider():
    head = make_circle((0, 3.0), 1.7)
    abdomen = make_ellipse((0, -2.5), 3.2, 4.2)
    legs = [
        make_poly_line([(1.0, 2.8), (4.5, 6.2), (7.5, 8.8)], 0.9),
        make_poly_line([(-1.0, 2.8), (-4.5, 6.2), (-7.5, 8.8)], 0.9),
        make_poly_line([(1.2, 1.8), (6.5, 3.8), (9.5, 4.2)], 0.9),
        make_poly_line([(-1.2, 1.8), (-6.5, 3.8), (-9.5, 4.2)], 0.9),
        make_poly_line([(1.2, 0.5), (6.8, -1.0), (9.0, -3.5)], 0.9),
        make_poly_line([(-1.2, 0.5), (-6.8, -1.0), (-9.0, -3.5)], 0.9),
        make_poly_line([(1.0, -1.0), (5.5, -4.5), (7.0, -8.5)], 0.9),
        make_poly_line([(-1.0, -1.0), (-5.5, -4.5), (-7.0, -8.5)], 0.9)
    ]
    palp_l = make_poly_line([(-0.6, 4.2), (-1.8, 6.0)], 0.7)
    palp_r = make_poly_line([(0.6, 4.2), (1.8, 6.0)], 0.7)
    return unary_union([head, abdomen, palp_l, palp_r] + legs)


def build_beetle():
    head = make_circle((0, 4.8), 1.6)
    pronotum = make_ellipse((0, 2.8), 3.4, 1.8)
    elytra = make_ellipse((0, -2.5), 4.2, 5.0)
    split_line = box(-0.35, -8.0, 0.35, 3.0)
    elytra_split = elytra.difference(split_line)
    ant_l = make_poly_line([(-0.8, 5.8), (-2.5, 7.8), (-4.2, 7.2)], 0.7)
    ant_r = make_poly_line([(0.8, 5.8), (2.5, 7.8), (4.2, 7.2)], 0.7)
    legs = [
        make_poly_line([(2.5, 3.2), (6.5, 5.8), (8.5, 4.8)], 0.85),
        make_poly_line([(-2.5, 3.2), (-6.5, 5.8), (-8.5, 4.8)], 0.85),
        make_poly_line([(3.5, 0.8), (7.5, 1.2), (9.0, -0.8)], 0.85),
        make_poly_line([(-3.5, 0.8), (-7.5, 1.2), (-9.0, -0.8)], 0.85),
        make_poly_line([(3.5, -2.5), (7.0, -4.5), (8.0, -7.5)], 0.85),
        make_poly_line([(-3.5, -2.5), (-7.0, -4.5), (-8.0, -7.5)], 0.85)
    ]
    return unary_union([head, pronotum, elytra_split, ant_l, ant_r] + legs)


def build_grasshopper():
    body = make_ellipse((0, -1.0), 2.2, 6.2)
    body = rotate(body, 15, origin=(0, -1.0))
    head = make_circle((-1.8, 4.8), 1.8)
    ant_l = make_poly_line([(-2.2, 6.0), (-4.0, 8.8), (-5.5, 9.5)], 0.7)
    ant_r = make_poly_line([(-1.2, 6.2), (-1.5, 9.2), (-2.0, 10.2)], 0.7)
    femur_r = make_poly_line([(1.2, -1.0), (4.8, 3.2), (6.5, 6.2)], 1.5)
    tibia_r = make_poly_line([(6.5, 6.2), (7.5, -1.0), (8.0, -7.5)], 0.9)
    femur_l = make_poly_line([(-0.8, -2.0), (-3.5, 2.0), (-5.0, 4.8)], 1.3)
    tibia_l = make_poly_line([(-5.0, 4.8), (-6.0, -2.0), (-6.5, -7.5)], 0.85)
    front_legs = [
        make_poly_line([(-2.0, 3.2), (-5.5, 3.8), (-7.0, 2.2)], 0.8),
        make_poly_line([(-1.5, 1.2), (-4.5, 0.2), (-5.5, -1.8)], 0.8)
    ]
    return unary_union([body, head, ant_l, ant_r, femur_r, tibia_r, femur_l, tibia_l] + front_legs)


def build_ant():
    head = make_circle((0, 5.0), 1.9)
    mandible_l = make_poly_line([(-0.8, 6.2), (-1.5, 8.2), (-0.5, 9.0)], 0.7)
    mandible_r = make_poly_line([(0.8, 6.2), (1.5, 8.2), (0.5, 9.0)], 0.7)
    ant_l = make_poly_line([(-1.2, 5.5), (-3.2, 7.2), (-4.8, 6.2)], 0.65)
    ant_r = make_poly_line([(1.2, 5.5), (3.2, 7.2), (4.8, 6.2)], 0.65)
    thorax = make_ellipse((0, 1.8), 1.6, 2.2)
    petiole = make_circle((0, -0.6), 0.9)
    gaster = make_ellipse((0, -4.5), 3.0, 4.0)
    legs = [
        make_poly_line([(1.0, 2.8), (4.8, 5.0), (7.5, 4.0)], 0.85),
        make_poly_line([(-1.0, 2.8), (-4.8, 5.0), (-7.5, 4.0)], 0.85),
        make_poly_line([(1.2, 1.8), (6.0, 2.0), (8.5, 0.5)], 0.85),
        make_poly_line([(-1.2, 1.8), (-6.0, 2.0), (-8.5, 0.5)], 0.85),
        make_poly_line([(1.0, 0.8), (5.5, -1.5), (7.5, -4.5)], 0.85),
        make_poly_line([(-1.0, 0.8), (-5.5, -1.5), (-7.5, -4.5)], 0.85)
    ]
    return unary_union([head, mandible_l, mandible_r, ant_l, ant_r, thorax, petiole, gaster] + legs)


def build_mosquito():
    head = make_circle((0, 4.2), 1.4)
    proboscis = make_poly_line([(0, 5.2), (0, 9.6)], 0.65)
    ant_l = make_poly_line([(-0.6, 4.8), (-2.2, 6.8)], 0.55)
    ant_r = make_poly_line([(0.6, 4.8), (2.2, 6.8)], 0.55)
    thorax = make_ellipse((0, 2.0), 1.8, 2.2)
    abdomen = make_ellipse((0, -3.5), 1.3, 4.5)
    wing_l = rotate(make_ellipse((-5.8, 3.0), 5.5, 1.4), -30, origin=(-5.8, 3.0))
    wing_r = rotate(make_ellipse((5.8, 3.0), 5.5, 1.4), 30, origin=(5.8, 3.0))
    legs = [
        make_poly_line([(1.0, 2.8), (5.0, 5.8), (8.0, 8.2)], 0.7),
        make_poly_line([(-1.0, 2.8), (-5.0, 5.8), (-8.0, 8.2)], 0.7),
        make_poly_line([(1.2, 1.8), (6.5, 2.2), (9.0, -0.2)], 0.7),
        make_poly_line([(-1.2, 1.8), (-6.5, 2.2), (-9.0, -0.2)], 0.7),
        make_poly_line([(1.0, 0.8), (5.5, -2.5), (8.5, -7.5)], 0.7),
        make_poly_line([(-1.0, 0.8), (-5.5, -2.5), (-8.5, -7.5)], 0.7)
    ]
    return unary_union([head, proboscis, ant_l, ant_r, thorax, abdomen, wing_l, wing_r] + legs)


def build_ladybug():
    head = make_circle((0, 5.0), 1.8)
    pronotum = make_ellipse((0, 3.4), 3.5, 1.6)
    elytra = make_circle((0, -1.8), 5.2)
    split_line = box(-0.35, -8.0, 0.35, 3.0)
    spots = [
        make_circle((-2.4, 0.5), 1.0), make_circle((2.4, 0.5), 1.0),
        make_circle((-3.0, -2.2), 1.0), make_circle((3.0, -2.2), 1.0),
        make_circle((-1.8, -4.5), 0.9), make_circle((1.8, -4.5), 0.9)
    ]
    elytra_spotted = elytra.difference(unary_union([split_line] + spots))
    ant_l = make_poly_line([(-0.8, 6.0), (-2.5, 7.8)], 0.7)
    ant_r = make_poly_line([(0.8, 6.0), (2.5, 7.8)], 0.7)
    legs = [
        make_poly_line([(2.5, 3.5), (6.2, 6.0), (8.0, 5.2)], 0.85),
        make_poly_line([(-2.5, 3.5), (-6.2, 6.0), (-8.0, 5.2)], 0.85),
        make_poly_line([(3.8, 0.5), (7.5, 0.8), (8.8, -0.8)], 0.85),
        make_poly_line([(-3.8, 0.5), (-7.5, 0.8), (-8.8, -0.8)], 0.85),
        make_poly_line([(3.5, -2.8), (7.0, -4.5), (8.0, -6.8)], 0.85),
        make_poly_line([(-3.5, -2.8), (-7.0, -4.5), (-8.0, -6.8)], 0.85)
    ]
    return unary_union([head, pronotum, elytra_spotted, ant_l, ant_r] + legs)


def build_pillbug():
    head = make_ellipse((0, 5.2), 3.2, 1.8)
    ant_l = make_poly_line([(-1.2, 6.2), (-2.8, 8.2), (-4.2, 8.2)], 0.7)
    ant_r = make_poly_line([(1.2, 6.2), (2.8, 8.2), (4.2, 8.2)], 0.7)
    plates = []
    y_centers = [3.8, 2.2, 0.6, -1.0, -2.6, -4.2, -5.8]
    rxs = [4.2, 4.6, 4.8, 4.8, 4.6, 4.0, 3.0]
    for yc, rx in zip(y_centers, rxs):
        p = make_ellipse((0, yc), rx, 1.4)
        plates.append(p)
    gaps = [box(-6, yc - 0.25, 6, yc + 0.25) for yc in [3.0, 1.4, -0.2, -1.8, -3.4, -5.0]]
    body = unary_union(plates).difference(unary_union(gaps))
    legs = [
        make_poly_line([(3.5, 3.0), (6.5, 4.2), (7.5, 3.5)], 0.75),
        make_poly_line([(-3.5, 3.0), (-6.5, 4.2), (-7.5, 3.5)], 0.75),
        make_poly_line([(4.0, 1.0), (7.0, 1.5), (8.0, 0.5)], 0.75),
        make_poly_line([(-4.0, 1.0), (-7.0, 1.5), (-8.0, 0.5)], 0.75),
        make_poly_line([(4.0, -1.5), (7.0, -1.5), (8.0, -2.5)], 0.75),
        make_poly_line([(-4.0, -1.5), (-7.0, -1.5), (-8.0, -2.5)], 0.75),
        make_poly_line([(3.5, -4.0), (6.5, -4.5), (7.2, -6.0)], 0.75),
        make_poly_line([(-3.5, -4.0), (-6.5, -4.5), (-7.2, -6.0)], 0.75)
    ]
    return unary_union([head, ant_l, ant_r, body] + legs)


INSECT_BUILDERS = {
    'queen_bee': build_queen_bee,
    'spider': build_spider,
    'beetle': build_beetle,
    'grasshopper': build_grasshopper,
    'ant': build_ant,
    'mosquito': build_mosquito,
    'ladybug': build_ladybug,
    'pillbug': build_pillbug
}


# ========================================================================
# 3D Mesh Generation & Multi-Part Slicing
# ========================================================================

def build_tile_pair(insect_poly, flat_to_flat=38.1, height=4.8,
                     chamfer=0.8, inlay_depth=0.8, emboss_height=0.0):
    if insect_poly is not None and not insect_poly.is_empty:
        glyph_polys = [insect_poly] if isinstance(insect_poly, Polygon) else list(insect_poly.geoms)
        glyph_polys = [orient(gp, sign=1.0) for gp in glyph_polys]
    else:
        glyph_polys = []
        
    z_cavity = height - inlay_depth
    z_top = height
    z_chamfer = height - chamfer
    z_bottom = 0.0
    text_total_height = inlay_depth + emboss_height
    
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
        
    vb, fb = triangulate_shapely_poly(poly_base)
    vb3 = np.hstack([vb, np.zeros((len(vb), 1))])
    fb_flip = np.column_stack([fb[:, 0], fb[:, 2], fb[:, 1]])
    add_mesh_data(vb3, fb_flip)
    
    vw, fw = [], []
    for i in range(6):
        p1 = hex_base_2d[i]
        p2 = hex_base_2d[(i + 1) % 6]
        idx = len(vw)
        vw.extend([[p1[0], p1[1], 0.0], [p2[0], p2[1], 0.0], [p2[0], p2[1], z_chamfer], [p1[0], p1[1], z_chamfer]])
        fw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
    add_mesh_data(np.array(vw), np.array(fw))
    
    vc, fc = [], []
    for i in range(6):
        p1b = hex_base_2d[i]
        p2b = hex_base_2d[(i + 1) % 6]
        p1t = hex_top_2d[i]
        p2t = hex_top_2d[(i + 1) % 6]
        idx = len(vc)
        vc.extend([[p1b[0], p1b[1], z_chamfer], [p2b[0], p2b[1], z_chamfer], [p2t[0], p2t[1], z_top], [p1t[0], p1t[1], z_top]])
        fc.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
    add_mesh_data(np.array(vc), np.array(fc))
    
    if glyph_polys:
        poly_top_diff = poly_top.difference(unary_union(glyph_polys))
    else:
        poly_top_diff = poly_top
        
    diff_polys = [poly_top_diff] if isinstance(poly_top_diff, Polygon) else list(poly_top_diff.geoms)
    for dp in diff_polys:
        vt, ft = triangulate_shapely_poly(dp)
        add_mesh_data(np.hstack([vt, np.full((len(vt), 1), z_top)]), ft)
        
    for gp in glyph_polys:
        vcav, fcav = triangulate_shapely_poly(gp)
        add_mesh_data(np.hstack([vcav, np.full((len(vcav), 1), z_cavity)]), fcav)
        
        ext_c = np.array(gp.exterior.coords)[:-1]
        n_e = len(ext_c)
        v_cw, f_cw = [], []
        for i in range(n_e):
            pc = ext_c[i]
            pn = ext_c[(i + 1) % n_e]
            idx = len(v_cw)
            v_cw.extend([[pc[0], pc[1], z_cavity], [pn[0], pn[1], z_cavity], [pn[0], pn[1], z_top], [pc[0], pc[1], z_top]])
            f_cw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
        add_mesh_data(np.array(v_cw), np.array(f_cw))
        
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
                f_hw.extend([[idx, idx + 1, idx + 2], [idx, idx + 3, idx + 2]])
            add_mesh_data(np.array(v_hw), np.array(f_hw))
            
    mesh_base = trimesh.Trimesh(vertices=np.vstack(verts_list), faces=np.vstack(faces_list), process=True)
    mesh_base.merge_vertices(digits_vertex=4)
    mesh_base.fix_normals()
    
    return mesh_base, mesh_text


def export_multimaterial_3mf(filepath, parts_dict):
    """Export multiple meshes into a single native multi-part 3MF package."""
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
    model_lines.append(f'    <object id="{assembly_id}" name="Hive_Tile_Assembly" type="model">')
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
    if mesh_base is not None:
        os.makedirs(os.path.dirname(os.path.abspath(base_path)), exist_ok=True)
        mesh_base.export(base_path)
    if mesh_text is not None:
        os.makedirs(os.path.dirname(os.path.abspath(text_path)), exist_ok=True)
        mesh_text.export(text_path)


def generate_multi_color_preview(mesh_base, insect_meshes_dict, output_path, label="Hive 4-Color Plate", color_base='#F6F1E6'):
    """
    Generate an attractive preview render showing multi-color inlays (up to 4 colors total).
    """
    fig = plt.figure(figsize=(11, 5.5), dpi=150, facecolor='#181818')
    
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
    col_base = Poly3DCollection(base_polys, facecolors=color_base, edgecolors='#C8BFAD', linewidths=0.15, alpha=0.98)
    ax1.add_collection3d(col_base)
    
    for key, mesh in insect_meshes_dict.items():
        if mesh is not None and len(mesh.vertices) > 0:
            c = OFFICIAL_INSECT_HEX_COLORS.get(key, '#151515')
            text_polys = mesh.vertices[mesh.faces]
            col_text = Poly3DCollection(text_polys, facecolors=c, edgecolors='#000000', linewidths=0.08, alpha=1.0)
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
    
    col_base_top = Poly3DCollection(base_polys, facecolors=color_base, edgecolors='#CEC4B2', linewidths=0.15, alpha=1.0)
    ax2.add_collection3d(col_base_top)
    
    for key, mesh in insect_meshes_dict.items():
        if mesh is not None and len(mesh.vertices) > 0:
            c = OFFICIAL_INSECT_HEX_COLORS.get(key, '#111111')
            text_polys = mesh.vertices[mesh.faces]
            col_text_top = Poly3DCollection(text_polys, facecolors=c, edgecolors='#000000', linewidths=0.08, alpha=1.0)
            ax2.add_collection3d(col_text_top)
            
    ax2.set_xlim(center_x - half_span, center_x + half_span)
    ax2.set_ylim(center_y - half_span, center_y + half_span)
    ax2.set_zlim(0, 10)
    ax2.axis('off')
    ax2.set_title(f"{label} - Top View (Max 4 Colors)", color='#E8E8E8', fontsize=12, pad=12, weight='bold')
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)


def build_grouped_4color_plate(insect_keys_list, flat_to_flat=38.1, height=4.8,
                               chamfer=0.8, inlay_depth=0.8, cols=4, spacing=4.0):
    """
    Arranges a list of insects into an interlocking honeycomb grid.
    Separates the insect meshes into distinct groups by insect type / color
    so slicers can assign separate toolheads / filaments (max 1 base + 3 colors = 4 total).
    Returns (plate_base, dict_of_insects_by_color).
    """
    all_base_meshes = []
    insects_by_type = {}
    
    r = flat_to_flat / 2.0
    R = r / np.cos(np.deg2rad(30))
    dx = (1.5 * R) + spacing
    dy = flat_to_flat + spacing
    
    for idx, key in enumerate(insect_keys_list):
        col = idx % cols
        row = idx // cols
        
        offset_x = col * dx
        offset_y = row * dy + (col % 2) * (dy / 2.0)
        
        builder = INSECT_BUILDERS[key]
        insect_poly = builder()
        
        mb, mt = build_tile_pair(
            insect_poly=insect_poly, flat_to_flat=flat_to_flat,
            height=height, chamfer=chamfer, inlay_depth=inlay_depth
        )
        
        mb.apply_translation([offset_x, offset_y, 0])
        all_base_meshes.append(mb)
        
        if mt is not None:
            mt.apply_translation([offset_x, offset_y, 0])
            if key not in insects_by_type:
                insects_by_type[key] = []
            insects_by_type[key].append(mt)
            
    plate_base = trimesh.util.concatenate(all_base_meshes)
    
    # Center everything around origin
    center = (plate_base.bounds[0] + plate_base.bounds[1]) / 2.0
    center[2] = 0.0
    plate_base.apply_translation(-center)
    
    merged_insects = {}
    for key, mesh_list in insects_by_type.items():
        m_comb = trimesh.util.concatenate(mesh_list)
        m_comb.apply_translation(-center)
        merged_insects[key] = m_comb
        
    return plate_base, merged_insects


def main():
    parser = argparse.ArgumentParser(description="Dual-Color & 4-Color Hexagonal 'Hive' 3D Tile Generator")
    parser.add_argument("--insect", type=str, choices=list(INSECT_BUILDERS.keys()), help="Generate a single insect tile")
    parser.add_argument("--all", action="store_true", help="Generate all individual insect tiles (Base + Expansions)")
    parser.add_argument("--plates", action="store_true", help="Generate ready-to-slice batch build plates (including 4-color limited plates)")
    parser.add_argument("--size", type=float, default=38.1, help="Tile flat-to-flat diameter in mm (default: 38.1 = 1.5 in)")
    parser.add_argument("--height", type=float, default=4.8, help="Tile height in mm (default: 4.8)")
    parser.add_argument("--chamfer", type=float, default=0.8, help="Top perimeter chamfer in mm (default: 0.8)")
    parser.add_argument("--inlay-depth", type=float, default=0.8, help="Inlay depth in mm (default: 0.8)")
    parser.add_argument("--embossed", type=float, default=0.0, help="Raised text height above tile in mm (default: 0.0 = flush)")
    parser.add_argument("--outdir", type=str, default="output_hive", help="Output directory path")
    
    args = parser.parse_args()
    
    outdir = os.path.abspath(args.outdir)
    dir_3mf = os.path.join(outdir, "3mf")
    dir_stl = os.path.join(outdir, "stl")
    dir_plates = os.path.join(outdir, "plates")
    dir_4color = os.path.join(outdir, "plates_4color_limited")
    dir_previews = os.path.join(outdir, "previews")
    
    os.makedirs(dir_3mf, exist_ok=True)
    os.makedirs(dir_stl, exist_ok=True)
    os.makedirs(dir_plates, exist_ok=True)
    os.makedirs(dir_4color, exist_ok=True)
    os.makedirs(dir_previews, exist_ok=True)
    
    print(f"[HIVE CAD] Tile dimensions: Diameter={args.size:.1f}mm (1.5in), Height={args.height:.1f}mm, Chamfer={args.chamfer:.1f}mm, Inlay={args.inlay_depth:.1f}mm")
    
    # 1. Single Insect Tile
    if args.insect:
        key = args.insect
        name = INSECT_DISPLAY_NAMES[key]
        print(f"Generating single Hive tile: '{name}'...")
        builder = INSECT_BUILDERS[key]
        poly = builder()
        mb, mt = build_tile_pair(
            insect_poly=poly, flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed
        )
        
        mf_path = os.path.join(dir_3mf, f"tile_{key}.3mf")
        stl_b = os.path.join(dir_stl, f"tile_{key}_base.stl")
        stl_t = os.path.join(dir_stl, f"tile_{key}_insect.stl")
        img_path = os.path.join(dir_previews, f"tile_{key}.png")
        
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, f"Insect_{name.replace(' ', '_')}": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        generate_multi_color_preview(mb, {key: mt}, img_path, label=f"Hive - {name}")
        print(f" -> Saved 3MF: {mf_path}")
        print(f" -> Saved Preview: {img_path}")
        return

    # 2. Generate All Individual Tiles & Previews
    print("\n--- Generating All 8 Hive Insect Tiles (Base Game + Expansions) ---")
    for key, builder in INSECT_BUILDERS.items():
        name = INSECT_DISPLAY_NAMES[key]
        poly = builder()
        mb, mt = build_tile_pair(
            insect_poly=poly, flat_to_flat=args.size, height=args.height,
            chamfer=args.chamfer, inlay_depth=args.inlay_depth, emboss_height=args.embossed
        )
        mf_path = os.path.join(dir_3mf, f"tile_{key}.3mf")
        stl_b = os.path.join(dir_stl, f"tile_{key}_base.stl")
        stl_t = os.path.join(dir_stl, f"tile_{key}_insect.stl")
        img_path = os.path.join(dir_previews, f"tile_{key}.png")
        
        export_multimaterial_3mf(mf_path, {"Tile_Base": mb, f"Insect_{name.replace(' ', '_')}": mt})
        export_stl_pair(stl_b, stl_t, mb, mt)
        generate_multi_color_preview(mb, {key: mt}, img_path, label=f"Hive - {name}")
        print(f" -> Saved {name:15s} to {mf_path}")
        
    # 3. Generate 4-Color-Limited Build Plates (Max 1 Base + 3 Insect Colors = 4 Colors Total)
    print("\n--- Generating 4-Color-Limited Build Plates (Strictly <= 4 Colors per Plate) ---")
    
    # -------------------------------------------------------------
    # 4-COLOR SET 1: 1-PLAYER ARMY (3 Plates: Core Swarm, Crawlers, Expansions)
    # -------------------------------------------------------------
    # Plate A: Core Swarm (1x Queen Bee, 3x Grasshopper, 3x Soldier Ant = 7 tiles, 4 colors: Base + Yellow + Green + Blue)
    plate_a_keys = ['queen_bee'] + ['grasshopper']*3 + ['ant']*3
    pa_b, pa_insects = build_grouped_4color_plate(plate_a_keys, flat_to_flat=args.size, height=args.height, cols=3)
    parts_a = {"Plate_Base": pa_b}
    for k, m in pa_insects.items():
        parts_a[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pa = os.path.join(dir_4color, "plate_4color_A_core_swarm_7tiles.3mf")
    img_pa = os.path.join(dir_previews, "plate_4color_A_core_swarm.png")
    export_multimaterial_3mf(mf_pa, parts_a)
    generate_multi_color_preview(pa_b, pa_insects, img_pa, label="4-Color Plate A: Core Swarm (Queen, Ants, Grasshoppers)")
    print(f" -> Saved: {mf_pa} (4 colors: Base + Yellow + Green + Blue)")

    # Plate B: Crawlers (2x Spider, 2x Beetle = 4 tiles, 3 colors: Base + Brown/Orange + Purple)
    plate_b_keys = ['spider']*2 + ['beetle']*2
    pb_b, pb_insects = build_grouped_4color_plate(plate_b_keys, flat_to_flat=args.size, height=args.height, cols=2)
    parts_b = {"Plate_Base": pb_b}
    for k, m in pb_insects.items():
        parts_b[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pb = os.path.join(dir_4color, "plate_4color_B_crawlers_4tiles.3mf")
    img_pb = os.path.join(dir_previews, "plate_4color_B_crawlers.png")
    export_multimaterial_3mf(mf_pb, parts_b)
    generate_multi_color_preview(pb_b, pb_insects, img_pb, label="4-Color Plate B: Crawlers (Spiders & Beetles)")
    print(f" -> Saved: {mf_pb} (3 colors: Base + Brown + Purple)")

    # Plate C: Expansions Pack (1x Ladybug, 1x Mosquito, 1x Pillbug = 3 tiles, 4 colors: Base + Red + Silver/Gray + Cyan)
    plate_c_keys = ['ladybug', 'mosquito', 'pillbug']
    pc_b, pc_insects = build_grouped_4color_plate(plate_c_keys, flat_to_flat=args.size, height=args.height, cols=3)
    parts_c = {"Plate_Base": pc_b}
    for k, m in pc_insects.items():
        parts_c[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pc = os.path.join(dir_4color, "plate_4color_C_expansions_3tiles.3mf")
    img_pc = os.path.join(dir_previews, "plate_4color_C_expansions.png")
    export_multimaterial_3mf(mf_pc, parts_c)
    generate_multi_color_preview(pc_b, pc_insects, img_pc, label="4-Color Plate C: Expansions (Ladybug, Mosquito, Pillbug)")
    print(f" -> Saved: {mf_pc} (4 colors: Base + Red + Gray + Cyan)")

    # -------------------------------------------------------------
    # 4-COLOR SET 2: BOTH PLAYERS MASTER BATCHES (Print once for 2 complete armies!)
    # -------------------------------------------------------------
    # Both Players Plate 1: 2x Queen Bee, 6x Grasshopper, 6x Soldier Ant = 14 tiles (4 colors: Base + Yellow + Green + Blue)
    both_a_keys = ['queen_bee']*2 + ['grasshopper']*6 + ['ant']*6
    pba_b, pba_insects = build_grouped_4color_plate(both_a_keys, flat_to_flat=args.size, height=args.height, cols=4)
    parts_both_a = {"Plate_Base": pba_b}
    for k, m in pba_insects.items():
        parts_both_a[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pba = os.path.join(dir_4color, "plate_4color_2player_core_swarm_14tiles.3mf")
    img_pba = os.path.join(dir_previews, "plate_4color_2player_core_swarm.png")
    export_multimaterial_3mf(mf_pba, parts_both_a)
    generate_multi_color_preview(pba_b, pba_insects, img_pba, label="4-Color 2-Player Core Swarm (14 Tiles: 2 Queens, 6 Ants, 6 Hoppers)")
    print(f" -> Saved: {mf_pba} (14 tiles, 4 colors: Base + Yellow + Green + Blue)")

    # Both Players Plate 2: 4x Spider, 4x Beetle = 8 tiles (3 colors: Base + Brown + Purple)
    both_b_keys = ['spider']*4 + ['beetle']*4
    pbb_b, pbb_insects = build_grouped_4color_plate(both_b_keys, flat_to_flat=args.size, height=args.height, cols=4)
    parts_both_b = {"Plate_Base": pbb_b}
    for k, m in pbb_insects.items():
        parts_both_b[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pbb = os.path.join(dir_4color, "plate_4color_2player_crawlers_8tiles.3mf")
    img_pbb = os.path.join(dir_previews, "plate_4color_2player_crawlers.png")
    export_multimaterial_3mf(mf_pbb, parts_both_b)
    generate_multi_color_preview(pbb_b, pbb_insects, img_pbb, label="4-Color 2-Player Crawlers (8 Tiles: 4 Spiders, 4 Beetles)")
    print(f" -> Saved: {mf_pbb} (8 tiles, 3 colors: Base + Brown + Purple)")

    # Both Players Plate 3: 2x Ladybug, 2x Mosquito, 2x Pillbug = 6 tiles (4 colors: Base + Red + Gray + Cyan)
    both_c_keys = ['ladybug']*2 + ['mosquito']*2 + ['pillbug']*2
    pbc_b, pbc_insects = build_grouped_4color_plate(both_c_keys, flat_to_flat=args.size, height=args.height, cols=3)
    parts_both_c = {"Plate_Base": pbc_b}
    for k, m in pbc_insects.items():
        parts_both_c[f"Insects_{INSECT_DISPLAY_NAMES[k].replace(' ', '_')}"] = m
    mf_pbc = os.path.join(dir_4color, "plate_4color_2player_expansions_6tiles.3mf")
    img_pbc = os.path.join(dir_previews, "plate_4color_2player_expansions.png")
    export_multimaterial_3mf(mf_pbc, parts_both_c)
    generate_multi_color_preview(pbc_b, pbc_insects, img_pbc, label="4-Color 2-Player Expansions (6 Tiles: 2 Ladybugs, 2 Mosquitos, 2 Pillbugs)")
    print(f" -> Saved: {mf_pbc} (6 tiles, 4 colors: Base + Red + Gray + Cyan)")

    print("\n[SUCCESS] All 4-Color-limited 3MF plates and preview renders generated successfully!")


if __name__ == "__main__":
    main()
