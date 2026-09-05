import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon
from shapely.ops import unary_union
from PIL import Image

# Exact cell dimensions
POCKET_FLAT = 33.80
WALL_RIB = 1.40
CELL_FLAT = POCKET_FLAT + WALL_RIB # 35.20 mm
r = CELL_FLAT / 2.0
R = r / math.cos(math.radians(30))

def make_flat_hex_pts(cx, cy, flat_val):
    r_sub = flat_val / 2.0
    R_sub = r_sub / math.cos(math.radians(30))
    s_half = r_sub * math.tan(math.radians(30))
    return np.array([
        [cx + s_half, cy + r_sub],
        [cx - s_half, cy + r_sub],
        [cx - R_sub,  cy],
        [cx - s_half, cy - r_sub],
        [cx + s_half, cy - r_sub],
        [cx + R_sub,  cy]
    ])

# 60-deg CCW rotation in cubic coordinates:
def rot_ccw(p):
    return (-p[1], -p[2], -p[0])

# Approved layout definitions:
cur_apex = (-8, 8, 0)
cur_dw1 = (-7, 6, 1)
cur_dw2 = (-6, 7, -1)
cur_tl = (-8, 4, 4)
cur_key = (-4, 2, 2)
cur_dl1 = (-6, 4, 2)
cur_dl2 = (-4, 6, -2)
cur_dl_mid = (-4, 4, 0)
cur_dl_inner = (-1, 2, -1)

# 4-Color AMS Filament Palette:
# Slot 1: Charcoal Black (#1F212B) -> Base, pocket floor, embossed text
# Slot 2: Neon Lime (#AEEA00) -> Grid ribs, outer rim, TW
# Slot 3: Hot Pink (#E91E63) -> DW, DW Key, Start Star
# Slot 4: Cyan Blue (#00E5FF) -> TL, DL
COLOR_BASE = "#1F212B"
COLOR_LIME = "#AEEA00"
COLOR_PINK = "#E91E63"
COLOR_BLUE = "#00E5FF"

mult_map = {}
for _ in range(6):
    mult_map[cur_apex] = ("TW", COLOR_LIME, COLOR_BASE, "TRIPLE WORD")
    mult_map[cur_dw1] = ("DW", COLOR_PINK, "#FFFFFF", "DOUBLE WORD")
    mult_map[cur_dw2] = ("DW", COLOR_PINK, "#FFFFFF", "DOUBLE WORD")
    mult_map[cur_tl] = ("TL", COLOR_BLUE, COLOR_BASE, "TRIPLE LETTER")
    mult_map[cur_key] = ("DW\n🔑", COLOR_PINK, COLOR_LIME, "KEY WILD (DW)")
    mult_map[cur_dl1] = ("DL", COLOR_BLUE, COLOR_BASE, "DOUBLE LETTER")
    mult_map[cur_dl2] = ("DL", COLOR_BLUE, COLOR_BASE, "DOUBLE LETTER")
    mult_map[cur_dl_mid] = ("DL", COLOR_BLUE, COLOR_BASE, "DOUBLE LETTER")
    mult_map[cur_dl_inner] = ("DL", COLOR_BLUE, COLOR_BASE, "DOUBLE LETTER")
    
    cur_apex = rot_ccw(cur_apex)
    cur_dw1 = rot_ccw(cur_dw1)
    cur_dw2 = rot_ccw(cur_dw2)
    cur_tl = rot_ccw(cur_tl)
    cur_key = rot_ccw(cur_key)
    cur_dl1 = rot_ccw(cur_dl1)
    cur_dl2 = rot_ccw(cur_dl2)
    cur_dl_mid = rot_ccw(cur_dl_mid)
    cur_dl_inner = rot_ccw(cur_dl_inner)

mult_map[(0, 0, 0)] = ("★", COLOR_PINK, "#FFFFFF", "START")

def get_buzzle_multiplier(x, y, z):
    return mult_map.get((x, y, z), ("", COLOR_BASE, "#FFFFFF", "BLANK"))

def render_board_and_assembly():
    from pathlib import Path
    Path("archive/legacy-outputs/output/board").mkdir(parents=True, exist_ok=True)
    cells = []
    for x in range(-8, 9):
        for y in range(max(-8, -x-8), min(8, -x+8) + 1):
            z = -x - y
            cx = -z * r * math.sqrt(3.0)
            cy = (y - x) * r
            label, bg_col, txt_col, desc = get_buzzle_multiplier(x, y, z)
            cells.append((x, y, z, cx, cy, label, bg_col, txt_col, desc))

    # 1. Master Assembled Board Render (with 7-tile diameter Rosette boundary)
    fig, ax = plt.subplots(figsize=(14, 14), dpi=300)
    fig.patch.set_facecolor("#0F1015")
    ax.set_facecolor("#0F1015")

    all_hexes = [Polygon(make_flat_hex_pts(cx, cy, CELL_FLAT)) for _, _, _, cx, cy, _, _, _, _ in cells]
    board_poly = unary_union(all_hexes)
    rim_poly = board_poly.buffer(8.0, resolution=16)

    bx, by = rim_poly.exterior.xy
    ax.plot(bx, by, color="#2D2F3E", linewidth=14, zorder=0)
    ax.fill(bx, by, color="#161720", zorder=0)

    for x, y, z, cx, cy, label, bg_col, txt_col, desc in cells:
        pts_outer = make_flat_hex_pts(cx, cy, CELL_FLAT)
        pts_inner = make_flat_hex_pts(cx, cy, POCKET_FLAT)
        ax.add_patch(MplPolygon(pts_outer, closed=True, facecolor="#14151C", edgecolor=COLOR_LIME, linewidth=1.2, zorder=1))
        ax.add_patch(MplPolygon(pts_inner, closed=True, facecolor=bg_col, edgecolor="#37474F" if desc=="BLANK" else "#FFFFFF", linewidth=0.6, zorder=2))
        
        if label:
            if "🔑" in label:
                ax.text(cx, cy + 2.5, "DW", color="#FFFFFF", fontsize=8.0, ha="center", va="center", fontweight="bold", zorder=3)
                ax.text(cx, cy - 4.5, "KEY", color=COLOR_LIME, fontsize=6.5, ha="center", va="center", fontweight="bold", zorder=3)
            elif label == "★":
                ax.text(cx, cy, "★", color="#FFD600", fontsize=16.0, ha="center", va="center", fontweight="bold", zorder=3)
            else:
                ax.text(cx, cy, label, color=txt_col, fontsize=8.5, ha="center", va="center", fontweight="bold", zorder=3)

    # Highlight 7-Tile Diameter Central Rosette Hub (Radius 3 = 37 Cells)
    hub_hexes = [p for i, p in enumerate(all_hexes) if max(abs(cells[i][0]), abs(cells[i][1]), abs(cells[i][2])) <= 3]
    u_hub = unary_union(hub_hexes).buffer(0.05).buffer(-0.05)
    geoms = [u_hub] if isinstance(u_hub, Polygon) else list(u_hub.geoms)
    for g in geoms:
        hx, hy = g.exterior.xy
        ax.plot(hx, hy, color="#FFFFFF", linewidth=3.5, linestyle="-", zorder=5)

    # Modular Seam Lines: from outer boundary of Hub (radius 3) to the 6 apexes
    apex_angles = [90, 150, 210, 270, 330, 30]
    for a_deg in apex_angles:
        rad_a = math.radians(a_deg)
        ax.plot([math.cos(rad_a)*CELL_FLAT*3.5, math.cos(rad_a)*CELL_FLAT*8.0],
                [math.sin(rad_a)*CELL_FLAT*3.5, math.sin(rad_a)*CELL_FLAT*8.0],
                color="#FFFFFF", linewidth=2.0, linestyle="--", alpha=0.9, zorder=5)

    ax.set_xlim(-16 * r * 1.15, 16 * r * 1.15)
    ax.set_ylim(-16 * r * 1.15, 16 * r * 1.15)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(0, 16 * r * 1.08, "BUZZLE™ BOARD — 4-COLOR MULTI-MATERIAL ARCHITECTURE", color="#FFFFFF", fontsize=15, ha="center", va="bottom", fontweight="bold")
    ax.text(0, -16 * r * 1.08, "Plate 1: 7-Tile Rosette Hub (37 Cells)  |  Plates 2–7: 6 Outer Wedges (30 Cells each)", color=COLOR_LIME, fontsize=11, ha="center", va="top", fontweight="bold")

    plt.tight_layout()
    plt.savefig("archive/legacy-outputs/output/board/buzzle_master_4color_board.png", dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print("Saved 4-color master board render.")

    # 2. Exploded Modular Assembly Render (7-Tile Hub + 6 Wedges)
    cells_hub = []
    cells_wedges = [[] for _ in range(6)]

    for x, y, z, cx, cy, label, bg_col, txt_col, desc in cells:
        dist = max(abs(x), abs(y), abs(z))
        if dist <= 3:
            cells_hub.append((cx, cy, label, bg_col, txt_col, desc))
        else:
            ang = (math.degrees(math.atan2(cy, cx)) + 360) % 360
            sector_idx = int(((ang - 60 + 360) % 360) // 60)
            cells_wedges[sector_idx].append((cx, cy, label, bg_col, txt_col, desc))

    fig2, ax2 = plt.subplots(figsize=(14, 14), dpi=300)
    fig2.patch.set_facecolor("#0F1015")
    ax2.set_facecolor("#0F1015")

    for cx, cy, label, bg_col, txt_col, desc in cells_hub:
        ax2.add_patch(MplPolygon(make_flat_hex_pts(cx, cy, CELL_FLAT), closed=True, facecolor="#14151C", edgecolor=COLOR_LIME, linewidth=1.2, zorder=2))
        ax2.add_patch(MplPolygon(make_flat_hex_pts(cx, cy, POCKET_FLAT), closed=True, facecolor=bg_col, edgecolor="#FFFFFF" if desc!="BLANK" else "#37474F", linewidth=0.6, zorder=3))
        if label == "★":
            ax2.text(cx, cy, "★", color="#FFD600", fontsize=15.0, ha="center", va="center", fontweight="bold", zorder=4)
        elif label:
            ax2.text(cx, cy, label, color=txt_col, fontsize=8.0, ha="center", va="center", fontweight="bold", zorder=4)

    ax2.text(0, -CELL_FLAT * 3.7, "Central Rosette Hub (Plate 1)\n37 Cells — 7 Tiles Diameter (224 x 246mm)", color="#FFE066", fontsize=10.0, ha="center", va="top", fontweight="bold")

    EXPLODE_DIST = 26.0
    wedge_colors = ["#FF5252", "#FF7A00", "#FFD600", "#00E676", "#00B0FF", "#E040FB"]

    for i in range(6):
        rad_s = math.radians(apex_angles[i])
        shift_x = EXPLODE_DIST * math.cos(rad_s)
        shift_y = EXPLODE_DIST * math.sin(rad_s)
        
        for cx, cy, label, bg_col, txt_col, desc in cells_wedges[i]:
            wx = cx + shift_x
            wy = cy + shift_y
            
            ax2.add_patch(MplPolygon(make_flat_hex_pts(wx, wy, CELL_FLAT), closed=True, facecolor="#14151C", edgecolor=COLOR_LIME, linewidth=1.1, zorder=2))
            ax2.add_patch(MplPolygon(make_flat_hex_pts(wx, wy, POCKET_FLAT), closed=True, facecolor=bg_col, edgecolor="#FFFFFF" if desc!="BLANK" else "#37474F", linewidth=0.5, zorder=3))
            
            if label:
                if "🔑" in label:
                    ax2.text(wx, wy + 2.0, "DW", color="#FFFFFF", fontsize=7.5, ha="center", va="center", fontweight="bold", zorder=4)
                    ax2.text(wx, wy - 4.0, "KEY", color=COLOR_LIME, fontsize=6.0, ha="center", va="center", fontweight="bold", zorder=4)
                else:
                    ax2.text(wx, wy, label, color=txt_col, fontsize=8.0, ha="center", va="center", fontweight="bold", zorder=4)
                    
        label_dist = 16 * r * 1.10
        lx = label_dist * math.cos(rad_s)
        ly = label_dist * math.sin(rad_s)
        ax2.text(lx, ly, f"Outer Wedge #{i+1} (Plate {i+2})\n30 Cells (Print x6)", color=wedge_colors[i], fontsize=9.0, ha="center", va="center", fontweight="bold")

    ax2.set_xlim(-16 * r * 1.25, 16 * r * 1.25)
    ax2.set_ylim(-16 * r * 1.25, 16 * r * 1.25)
    ax2.set_aspect("equal")
    ax2.axis("off")

    ax2.text(0, 16 * r * 1.22, "BUZZLE™ — 7-TILE ROSETTE + 6 SMALLER WEDGES ASSEMBLY", color="#FFFFFF", fontsize=15, ha="center", va="bottom", fontweight="bold")
    ax2.text(0, -16 * r * 1.20, "Every plate fits standard 256x256mm build volume  |  Rigid Interlocking Dovetails", color="#90A4AE", fontsize=10.5, ha="center", va="top")

    plt.tight_layout()
    plt.savefig("archive/legacy-outputs/output/board/buzzle_exploded_7tile_hub.png", dpi=300, facecolor=fig2.get_facecolor(), bbox_inches="tight")
    plt.close()
    print("Saved exploded 7-tile hub assembly render.")

    # 3. Print Bed Fit Visualization (Bambu 256 x 256 mm)
    fig3, axes3 = plt.subplots(1, 2, figsize=(14, 7), dpi=250)
    fig3.patch.set_facecolor("#0F1015")

    # Bed 1: Center Rosette Hub
    ax_b1 = axes3[0]
    ax_b1.set_facecolor("#181A24")
    # Draw 256 x 256 bed:
    bed_box = plt.Rectangle((-128, -128), 256, 256, facecolor="#10121A", edgecolor="#78909C", linewidth=2.0, linestyle="--")
    ax_b1.add_patch(bed_box)

    for cx, cy, label, bg_col, txt_col, desc in cells_hub:
        ax_b1.add_patch(MplPolygon(make_flat_hex_pts(cx, cy, CELL_FLAT), closed=True, facecolor="#14151C", edgecolor=COLOR_LIME, linewidth=1.0))
        ax_b1.add_patch(MplPolygon(make_flat_hex_pts(cx, cy, POCKET_FLAT), closed=True, facecolor=bg_col, edgecolor="#37474F" if desc=="BLANK" else "#FFFFFF", linewidth=0.5))

    ax_b1.set_xlim(-140, 140)
    ax_b1.set_ylim(-140, 140)
    ax_b1.set_aspect("equal")
    ax_b1.set_title("Plate 1: Central Rosette Hub (37 Cells)\nDimensions: 223.6 x 246.4 mm (Fits 256x256mm Bed)", color="#FFFFFF", fontsize=11, fontweight="bold", pad=10)
    ax_b1.axis("off")

    # Bed 2: Single Outer Wedge (Rotated for optimal bed placement)
    ax_b2 = axes3[1]
    ax_b2.set_facecolor("#181A24")
    bed_box2 = plt.Rectangle((-128, -128), 256, 256, facecolor="#10121A", edgecolor="#78909C", linewidth=2.0, linestyle="--")
    ax_b2.add_patch(bed_box2)

    # Center wedge #0 around (0, 0)
    pts_w0 = [(c[0], c[1]) for c in cells_wedges[0]]
    cx_mid = np.mean([p[0] for p in pts_w0])
    cy_mid = np.mean([p[1] for p in pts_w0])

    for cx, cy, label, bg_col, txt_col, desc in cells_wedges[0]:
        wx = cx - cx_mid
        wy = cy - cy_mid
        ax_b2.add_patch(MplPolygon(make_flat_hex_pts(wx, wy, CELL_FLAT), closed=True, facecolor="#14151C", edgecolor=COLOR_LIME, linewidth=1.0))
        ax_b2.add_patch(MplPolygon(make_flat_hex_pts(wx, wy, POCKET_FLAT), closed=True, facecolor=bg_col, edgecolor="#37474F" if desc=="BLANK" else "#FFFFFF", linewidth=0.5))
        if label:
            ax_b2.text(wx, wy, label.split("\n")[0], color=txt_col, fontsize=7.0, ha="center", va="center", fontweight="bold")

    ax_b2.set_xlim(-140, 140)
    ax_b2.set_ylim(-140, 140)
    ax_b2.set_aspect("equal")
    ax_b2.set_title("Plates 2–7: Outer Wedge (30 Cells, Print x6)\nDimensions: 254.0 x 211.2 mm (Fits 256x256mm Bed)", color="#FFFFFF", fontsize=11, fontweight="bold", pad=10)
    ax_b2.axis("off")

    plt.tight_layout()
    plt.savefig("archive/legacy-outputs/output/board/buzzle_bed_fit_256mm.png", dpi=250, facecolor=fig3.get_facecolor(), bbox_inches="tight")
    plt.close()
    print("Saved 256mm bed fit visualization.")

if __name__ == "__main__":
    render_board_and_assembly()
