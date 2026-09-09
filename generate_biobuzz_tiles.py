#!/usr/bin/env python3
"""
Double-Sided BioBuzz Branded Hexagonal Tile Generator
-----------------------------------------------------
Generates dual-color 3MF tiles with:
- Front Face: Bold embossed letter + Scrabble subscript score (+0.60mm raised)
- Back Face: Flush inlaid BioBuzz Honeycomb Rosette Logo (Single-color black line art & accents)
- Single Filament Color for both Top Letter and Bottom BioBuzz Logo!
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union, orient
from shapely.affinity import scale, translate, rotate
import math
import trimesh

from generate_tiles import (
    make_hex_points_2d, triangulate_shapely_poly, char_to_polygons,
    SCRABBLE_POINTS, find_default_font, export_multimaterial_3mf,
    generate_honeycomb_positions
)

def make_flat_hex(cx, cy, radius):
    angles = np.linspace(0, 360, 7)[:-1]
    pts = [(cx + radius * np.cos(np.deg2rad(a)), cy + radius * np.sin(np.deg2rad(a))) for a in angles]
    return Polygon(pts)


def create_biobuzz_logo_vector(target_size=28.5, wall_width=1.65, bracket_size=3.4, bracket_thick=1.30):
    r_outer = 5.2
    r_inner = r_outer - wall_width / 2.0
    pitch_y = r_outer * math.sqrt(3)
    pitch_x = 1.5 * r_outer

    centers = [
        (0, 0),                    # 0: center
        (0, pitch_y),              # 1: top
        (0, -pitch_y),             # 2: bottom
        (-pitch_x, pitch_y / 2.0), # 3: top-left
        (-pitch_x, -pitch_y / 2.0),# 4: bottom-left
        (pitch_x, pitch_y / 2.0),  # 5: top-right
        (pitch_x, -pitch_y / 2.0), # 6: bottom-right
    ]

    outer_hexes = [make_flat_hex(cx, cy, r_outer + wall_width / 2.0) for cx, cy in centers]
    rosette_outer = unary_union(outer_hexes)
    inner_hexes = [make_flat_hex(cx, cy, r_inner) for cx, cy in centers]
    inner_union = unary_union(inner_hexes)
    lattice_grid = rosette_outer.difference(inner_union)

    # Stylized reflection chevrons (Bold L-brackets)
    def make_bracket(cx, cy, angle_deg, size=bracket_size, thickness=bracket_thick):
        p1 = Polygon([(-size/2, -thickness/2), (size/2, -thickness/2), (size/2, thickness/2), (-size/2, thickness/2)])
        p2 = Polygon([(size/2 - thickness, -thickness/2), (size/2, -thickness/2), (size/2, size*0.8), (size/2 - thickness, size*0.8)])
        bracket = unary_union([p1, p2])
        bracket_rot = rotate(bracket, angle_deg, origin=(0, 0))
        return translate(bracket_rot, xoff=cx, yoff=cy)

    t_topleft = make_bracket(-pitch_x + 0.4, pitch_y / 2.0 + 1.4, 140)
    t_topright = make_bracket(pitch_x - 0.4, pitch_y / 2.0 + 1.4, -40)
    t_center = make_bracket(-0.4, -1.4, 50)
    t_botright = make_bracket(pitch_x - 0.4, -pitch_y / 2.0 - 1.4, 50)

    combined = unary_union([lattice_grid, t_topleft, t_topright, t_center, t_botright])
    
    bounds = combined.bounds
    raw_size = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    scale_f = target_size / raw_size
    scaled = scale(combined, xfact=scale_f, yfact=scale_f, origin=(0, 0))
    
    polys = [scaled] if isinstance(scaled, Polygon) else list(scaled.geoms)
    return [orient(p, sign=1.0) for p in polys]

def build_doublesided_biobuzz_tile(letter="A", score=None, logo_polys=None,
                                   flat_to_flat=33.02, height=4.8, chamfer=0.7,
                                   inlay_depth=0.8, emboss_height=0.0,
                                   font_path=None, letter_size=18.5, score_size=7.0):
    if font_path is None:
        font_path = find_default_font()
    if logo_polys is None:
        logo_polys = create_biobuzz_logo_vector(28.5)
        
    z_bot = 0.0
    z_bot_cavity = inlay_depth
    z_chamfer = height - chamfer
    z_top = height
    z_top_cavity = height - inlay_depth
    z_text_top = height + emboss_height
    
    # 1. Top Text Glyphs
    has_score = (score is not None and str(score).strip() and str(score) != '0')
    l_polys = []
    if letter and letter.strip():
        l_raw = char_to_polygons(letter, font_path, size=letter_size)
        if l_raw:
            l_u = l_raw[0] if len(l_raw) == 1 else unary_union(l_raw)
            minx, miny, maxx, maxy = l_u.bounds
            cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
            shift_x = -1.9 if has_score else 0.0
            shift_y = 0.8 if has_score else 0.0
            l_polys = [translate(p, xoff=-cx + shift_x, yoff=-cy + shift_y) for p in l_raw]
            
    s_polys = []
    if has_score:
        s_raw = char_to_polygons(str(score), font_path, size=score_size)
        if s_raw:
            s_u = s_raw[0] if len(s_raw) == 1 else unary_union(s_raw)
            minx, miny, maxx, maxy = s_u.bounds
            target_x = 8.1
            target_y = -7.5
            s_polys = [translate(p, xoff=target_x - (minx + maxx) / 2.0, yoff=target_y - (miny + maxy) / 2.0) for p in s_raw]
            
    top_glyphs = l_polys + s_polys
    top_glyph_polys = []
    if top_glyphs:
        gu = top_glyphs[0] if len(top_glyphs) == 1 else unary_union(top_glyphs)
        top_glyph_polys = [gu] if isinstance(gu, Polygon) else list(gu.geoms)
        top_glyph_polys = [orient(gp, sign=1.0) for gp in top_glyph_polys]
        
    # 2. Build Graphics Mesh (Bottom BioBuzz Logo + Top Text)
    graphics_meshes = []
    
    # Bottom logo mesh (from z=0 to z=z_bot_cavity)
    if logo_polys:
        for lp in logo_polys:
            m = trimesh.creation.extrude_polygon(lp, height=inlay_depth)
            graphics_meshes.append(m)
            
    # Top text mesh (from z=z_top_cavity to z=z_text_top)
    text_total_h = inlay_depth + emboss_height
    for gp in top_glyph_polys:
        m = trimesh.creation.extrude_polygon(gp, height=text_total_h)
        m.apply_translation([0, 0, z_top_cavity])
        graphics_meshes.append(m)
        
    mesh_graphics = trimesh.util.concatenate(graphics_meshes) if graphics_meshes else None
    if mesh_graphics is not None:
        mesh_graphics.merge_vertices(digits_vertex=4)
        mesh_graphics.fix_normals()
        
    # 3. Build Base Mesh with cavities on Top and Bottom
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
        
    # A. Bottom Face at z=0
    if logo_polys:
        poly_bot_diff = poly_base.difference(unary_union(logo_polys))
    else:
        poly_bot_diff = poly_base
        
    b_diff_polys = [poly_bot_diff] if isinstance(poly_bot_diff, Polygon) else list(poly_bot_diff.geoms)
    for bp in b_diff_polys:
        vb, fb = triangulate_shapely_poly(bp)
        vb3 = np.hstack([vb, np.zeros((len(vb), 1))])
        fb_flip = np.column_stack([fb[:, 0], fb[:, 2], fb[:, 1]])
        add_mesh_data(vb3, fb_flip)
        
    # B. Bottom Cavity Floor & Walls
    if logo_polys:
        for lp in logo_polys:
            vc, fc = triangulate_shapely_poly(lp)
            vc3 = np.hstack([vc, np.full((len(vc), 1), z_bot_cavity)])
            add_mesh_data(vc3, fc)
            
            ext_c = np.array(lp.exterior.coords)[:-1]
            n_e = len(ext_c)
            v_cw, f_cw = [], []
            for i in range(n_e):
                p1 = ext_c[i]
                p2 = ext_c[(i + 1) % n_e]
                idx = len(v_cw)
                v_cw.extend([
                    [p1[0], p1[1], 0.0],
                    [p2[0], p2[1], 0.0],
                    [p2[0], p2[1], z_bot_cavity],
                    [p1[0], p1[1], z_bot_cavity]
                ])
                f_cw.extend([[idx, idx + 2, idx + 1], [idx, idx + 3, idx + 2]])
            add_mesh_data(np.array(v_cw), np.array(f_cw))
            
            for interior in lp.interiors:
                hole_c = np.array(interior.coords)[:-1]
                n_h = len(hole_c)
                v_hw, f_hw = [], []
                for i in range(n_h):
                    p1 = hole_c[i]
                    p2 = hole_c[(i + 1) % n_h]
                    idx = len(v_hw)
                    v_hw.extend([
                        [p1[0], p1[1], 0.0],
                        [p2[0], p2[1], 0.0],
                        [p2[0], p2[1], z_bot_cavity],
                        [p1[0], p1[1], z_bot_cavity]
                    ])
                    f_hw.extend([[idx, idx + 2, idx + 1], [idx, idx + 3, idx + 2]])
                add_mesh_data(np.array(v_hw), np.array(f_hw))
                
    # C. Lower side walls (z=0 to z=z_chamfer)
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
    
    # D. Chamfer side walls (z=z_chamfer to z=z_top)
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
    
    # E. Top Face at z=z_top
    if top_glyph_polys:
        poly_top_diff = poly_top.difference(unary_union(top_glyph_polys))
    else:
        poly_top_diff = poly_top
        
    t_diff_polys = [poly_top_diff] if isinstance(poly_top_diff, Polygon) else list(poly_top_diff.geoms)
    for tp in t_diff_polys:
        vt, ft = triangulate_shapely_poly(tp)
        add_mesh_data(np.hstack([vt, np.full((len(vt), 1), z_top)]), ft)
        
    # F. Top Cavity Floor & Walls
    for gp in top_glyph_polys:
        vcav, fcav = triangulate_shapely_poly(gp)
        add_mesh_data(np.hstack([vcav, np.full((len(vcav), 1), z_top_cavity)]), fcav)
        
        ext_c = np.array(gp.exterior.coords)[:-1]
        n_e = len(ext_c)
        v_cw, f_cw = [], []
        for i in range(n_e):
            p1 = ext_c[i]
            p2 = ext_c[(i + 1) % n_e]
            idx = len(v_cw)
            v_cw.extend([
                [p1[0], p1[1], z_top_cavity],
                [p2[0], p2[1], z_top_cavity],
                [p2[0], p2[1], z_top],
                [p1[0], p1[1], z_top]
            ])
            f_cw.extend([[idx, idx + 1, idx + 2], [idx, idx + 2, idx + 3]])
        add_mesh_data(np.array(v_cw), np.array(f_cw))
        
        for interior in gp.interiors:
            hole_c = np.array(interior.coords)[:-1]
            n_h = len(hole_c)
            v_hw, f_hw = [], []
            for i in range(n_h):
                p1 = hole_c[i]
                p2 = hole_c[(i + 1) % n_h]
                idx = len(v_hw)
                v_hw.extend([
                    [p1[0], p1[1], z_top_cavity],
                    [p2[0], p2[1], z_top_cavity],
                    [p2[0], p2[1], z_top],
                    [p1[0], p1[1], z_top]
                ])
                f_hw.extend([[idx, idx + 2, idx + 1], [idx, idx + 3, idx + 2]])
            add_mesh_data(np.array(v_hw), np.array(f_hw))
            
    mesh_base = trimesh.Trimesh(vertices=np.vstack(verts_list), faces=np.vstack(faces_list), process=True)
    mesh_base.merge_vertices(digits_vertex=4)
    mesh_base.fix_normals()
    
    return mesh_base, mesh_graphics


def build_doublesided_biobuzz_256mm_plate(tile_specs, logo_polys=None, flat_to_flat=33.02,
                                          height=4.8, chamfer=0.7, inlay_depth=0.8,
                                          emboss_height=0.0, spacing=3.5, font_path=None):
    if logo_polys is None:
        logo_polys = create_biobuzz_logo_vector(28.5)
        
    positions = generate_honeycomb_positions(len(tile_specs), flat_to_flat=flat_to_flat, spacing=spacing)
    
    all_base_meshes = []
    all_graphics_meshes = []
    
    for (letter, score), (px, py) in zip(tile_specs, positions):
        letter_sz = 19.5 if score == "" and len(letter) > 0 and (letter.isdigit() or letter in '+-x/=?!') else 18.5
        mb, mg = build_doublesided_biobuzz_tile(
            letter=letter, score=score, logo_polys=logo_polys,
            flat_to_flat=flat_to_flat, height=height, chamfer=chamfer,
            inlay_depth=inlay_depth, emboss_height=emboss_height,
            font_path=font_path, letter_size=letter_sz, score_size=7.0
        )
        mb.apply_translation([px, py, 0])
        all_base_meshes.append(mb)
        if mg is not None:
            mg.apply_translation([px, py, 0])
            all_graphics_meshes.append(mg)
            
    plate_base = trimesh.util.concatenate(all_base_meshes)
    plate_graphics = trimesh.util.concatenate(all_graphics_meshes) if all_graphics_meshes else None
    
    return plate_base, plate_graphics


def render_biobuzz_preview(mesh_base, mesh_graphics, logo_polys, letter='A', score='1', img_path='output/tiles/biobuzz/images/tile_doublesided_biobuzz_A.png'):
    fig = plt.figure(figsize=(15, 5), facecolor='#121212')
    
    # 1. Front View (Top)
    ax1 = fig.add_subplot(1, 3, 1, facecolor='#121212')
    ax1.set_title(f'FRONT FACE\n(Embossed Letter {letter}_{score})', color='white', fontsize=13, fontweight='bold', pad=12)
    
    h_pts = make_hex_points_2d(33.02)
    ax1.add_patch(plt.Polygon(h_pts, closed=True, facecolor='#e8e0d5', edgecolor='#998d7d', lw=1.5))
    h_top = make_hex_points_2d(33.02 - 1.6)
    ax1.add_patch(plt.Polygon(h_top, closed=True, facecolor='#fbf8f3', edgecolor='#c5b8a8', lw=1.0))
    
    font_path = find_default_font()
    l_raw = char_to_polygons(letter, font_path, size=18.5)
    s_raw = char_to_polygons(str(score), font_path, size=7.0)
    l_u = l_raw[0] if len(l_raw) == 1 else unary_union(l_raw)
    l_cx = (l_u.bounds[0] + l_u.bounds[2]) / 2.0
    l_cy = (l_u.bounds[1] + l_u.bounds[3]) / 2.0
    s_u = s_raw[0] if len(s_raw) == 1 else unary_union(s_raw)
    s_cx = (s_u.bounds[0] + s_u.bounds[2]) / 2.0
    s_cy = (s_u.bounds[1] + s_u.bounds[3]) / 2.0
    top_polys = [translate(p, xoff=-l_cx - 2.0, yoff=-l_cy + 1.2) for p in l_raw] + [translate(p, xoff=8.6 - s_cx, yoff=-8.2 - s_cy) for p in s_raw]

    for poly in top_polys:
        ax1.add_patch(plt.Polygon(poly.exterior.coords, closed=True, facecolor='#e69500', edgecolor='#800010', lw=1.2))
        for interior in poly.interiors:
            ax1.add_patch(plt.Polygon(interior.coords, closed=True, facecolor='#fbf8f3', edgecolor='#800010', lw=1.2))
            
    ax1.set_xlim(-22, 22)
    ax1.set_ylim(-22, 22)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # 2. Back View (Bottom)
    ax2 = fig.add_subplot(1, 3, 2, facecolor='#121212')
    ax2.set_title('BACK FACE\n(BioBuzz Honeycomb Rosette Inlay)', color='white', fontsize=13, fontweight='bold', pad=12)
    
    ax2.add_patch(plt.Polygon(h_pts, closed=True, facecolor='#fbf8f3', edgecolor='#998d7d', lw=1.5))
    for poly in logo_polys:
        ax2.add_patch(plt.Polygon(poly.exterior.coords, closed=True, facecolor='#e69500', edgecolor='#800010', lw=1.2))
        for interior in poly.interiors:
            ax2.add_patch(plt.Polygon(interior.coords, closed=True, facecolor='#fbf8f3', edgecolor='#800010', lw=1.2))
            
    ax2.set_xlim(-22, 22)
    ax2.set_ylim(-22, 22)
    ax2.set_aspect('equal')
    ax2.axis('off')
    
    # 3. 3D Isometric View
    ax3 = fig.add_subplot(1, 3, 3, projection='3d', facecolor='#121212')
    ax3.set_title('3D DUAL-COLOR MODEL', color='white', fontsize=13, fontweight='bold', pad=12)
    
    b_verts = mesh_base.vertices
    b_faces = mesh_base.faces
    ax3.plot_trisurf(b_verts[:,0], b_verts[:,1], b_verts[:,2], triangles=b_faces, color='#fbf8f3', alpha=0.9, shade=True)
    
    g_verts = mesh_graphics.vertices
    g_faces = mesh_graphics.faces
    ax3.plot_trisurf(g_verts[:,0], g_verts[:,1], g_verts[:,2], triangles=g_faces, color='#e69500', alpha=0.95, shade=True)
    
    ax3.view_init(elev=35, azim=-55)
    ax3.set_axis_off()
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(img_path)), exist_ok=True)
    plt.savefig(img_path, dpi=180, bbox_inches='tight', facecolor='#121212')
    plt.close(fig)
    print(f'Rendered preview to {img_path}')


def main():
    parser = argparse.ArgumentParser(description="Double-Sided BioBuzz Branded Hexagonal Tile Generator")
    parser.add_argument("--letter", type=str, help="Generate single letter tile (e.g. 'A')")
    parser.add_argument("--score", type=str, default=None, help="Custom score")
    parser.add_argument("--plates", action="store_true", help="Generate complete 256mm double-sided build plates")
    parser.add_argument("--individuals", action="store_true", help="Export A-Z and blank as individual color 3MF files only")
    parser.add_argument("--outdir", type=str, default="output/tiles/biobuzz", help="Output directory")
    
    args = parser.parse_args()
    
    outdir = os.path.abspath(args.outdir)
    dir_3mf = os.path.join(outdir, "3mf")
    dir_plates = os.path.join(outdir, "plates")
    dir_previews = os.path.join(outdir, "images")
    
    os.makedirs(dir_3mf, exist_ok=True)
    os.makedirs(dir_plates, exist_ok=True)
    os.makedirs(dir_previews, exist_ok=True)
    
    print("[BIOBUZZ] Generating CAD-precision BioBuzz honeycomb rosette vector...")
    logo_polys = create_biobuzz_logo_vector(28.5)
    print(f" -> Generated {len(logo_polys)} vector components")

    if args.individuals:
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ ':
            score = str(SCRABBLE_POINTS.get(letter, 0))
            name = letter.strip() or 'BLANK'
            base, graphics = build_doublesided_biobuzz_tile(letter.strip(), score, logo_polys=logo_polys)
            path = os.path.join(dir_3mf, f'tile_doublesided_biobuzz_{name}_score{score}.3mf')
            export_multimaterial_3mf(path, {'Tile_Base': base, 'Tile_Graphics': graphics})
            print(f'Saved {name}', flush=True)
        return
    
    # 1. Standalone BioBuzz Medallion / Coaster Token
    print("\n--- Generating BioBuzz Emblem Medallion Tile ---")
    mb_med, mg_med = build_doublesided_biobuzz_tile(
        letter="", score="", logo_polys=logo_polys,
        flat_to_flat=33.02, height=4.8
    )
    mf_med = os.path.join(dir_3mf, "tile_biobuzz_token.3mf")
    export_multimaterial_3mf(mf_med, {"Tile_Base": mb_med, "Tile_Graphics": mg_med})
    print(f" -> Saved BioBuzz Token 3MF: {mf_med}")
    
    # 2. Single Letter Tile 'A' Preview
    mb_a, mg_a = build_doublesided_biobuzz_tile('A', '1', logo_polys=logo_polys)
    mf_a = os.path.join(dir_3mf, "tile_doublesided_biobuzz_A_score1.3mf")
    export_multimaterial_3mf(mf_a, {"Tile_Base": mb_a, "Tile_Graphics": mg_a})
    render_biobuzz_preview(mb_a, mg_a, logo_polys, 'A', '1', os.path.join(dir_previews, "tile_doublesided_biobuzz_A.png"))
    
    # 3. Generate Complete 256mm Build Plates (Scrabble 100-set & Hive-Swarm 144-set with BioBuzz Logo on Back)
    print("\n--- Generating Double-Sided 256mm Build Plates (BioBuzz Logo on Back) ---")
    
    # Scrabble 100-Tile Set (4 Plates of 25)
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
        pb, pg = build_doublesided_biobuzz_256mm_plate(p_specs, logo_polys=logo_polys)
        p_name = f"plate_256_biobuzz_scrabble_100set_plate{p_idx+1}_of_4_25tiles.3mf"
        export_multimaterial_3mf(os.path.join(dir_plates, p_name), {"Plate_Base": pb, "Plate_Graphics": pg})
        print(f" -> Saved Double-Sided Scrabble Plate {p_idx+1}/4: {p_name}")

    # Hive-Swarm 144-Tile Set (6 Plates of 24)
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
        pb, pg = build_doublesided_biobuzz_256mm_plate(p_specs, logo_polys=logo_polys)
        p_name = f"plate_256_biobuzz_hiveswarm_144set_plate{p_idx+1}_of_6_24tiles.3mf"
        export_multimaterial_3mf(os.path.join(dir_plates, p_name), {"Plate_Base": pb, "Plate_Graphics": pg})
        print(f" -> Saved Double-Sided Hive-Swarm Plate {p_idx+1}/6: {p_name}")

    print("\n[SUCCESS] Double-sided BioBuzz branded tiles and plates generated successfully!")


if __name__ == "__main__":
    main()
