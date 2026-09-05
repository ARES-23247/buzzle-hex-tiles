"""217-cell BUZZLE board: 33.02 mm (1.3 inch) tiles, 270 mm bed, four colors.

Run python generate_board_270.py. Historical smaller-board exports are untouched.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.affinity import rotate, translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

from generate_tiles import char_to_polygons, find_default_font
from generate_buzzle_rosette_board import extrude_poly, export_multimaterial_3mf
from render_new_buzzle_board import get_buzzle_multiplier, make_flat_hex_pts

OUTPUT = Path(__file__).resolve().parent / "output/boards/buzzle"
TILE_FLAT = 33.02
POCKET_FLAT = TILE_FLAT + 0.78
PITCH = POCKET_FLAT + 1.4
BED = 270.0
MARGIN = 5.0
TOWER = 40.0
TOWER_GAP = 5.0
WIDTH = BED - 2*MARGIN - TOWER - TOWER_GAP
HEIGHT = BED - 2*MARGIN
JOINT_CLEARANCE = 0.20
COLORS = ["#23272B", "#F2EADB", "#2C7A73", "#E3AF45"]
NAMES = ["Charcoal", "Ivory", "Teal", "Gold"]


def clean(p):
    return set_precision(p, 0.00001)


def union(polys):
    return clean(unary_union(polys))


def strengthen_outer_rim(sections, extra=0.7):
    """Thicken only exposed edges; shared seams and pocket sizes stay fixed."""
    board = union([s['original'] for s in sections])
    assigned = Polygon()
    for s in sections:
        extension = clean(s['original'].buffer(extra, quad_segs=4)).difference(board).difference(assigned)
        s['original'] = union([s['original'], extension])
        assigned = union([assigned, extension])


def make_cells():
    cells = []
    for x in range(-8, 9):
        for y in range(max(-8, -x-8), min(8, -x+8)+1):
            z = -x-y
            cx, cy = -z*PITCH*math.sqrt(3)/2, (y-x)*PITCH/2
            angle = round(math.degrees(math.atan2(cy, cx)) % 360, 8) % 360
            section = 0 if max(abs(x), abs(y), abs(z)) <= 3 else 1+int(angle//60)
            cells.append(dict(coord=(x, y, z), cx=cx, cy=cy, section=section,
                              desc=get_buzzle_multiplier(x, y, z)[3],
                              outer=clean(Polygon(make_flat_hex_pts(cx, cy, PITCH))),
                              pocket=clean(Polygon(make_flat_hex_pts(cx, cy, POCKET_FLAT)))))
    return cells


def tongue_between(inner, outer):
    a = np.array([inner["cx"], inner["cy"]])
    b = np.array([outer["cx"], outer["cy"]])
    center = (a+b)/2
    normal = (a-b)/np.linalg.norm(a-b)
    tangent = np.array([-normal[1], normal[0]])
    # 10 mm neck / 14 mm head / 6 mm engagement, anchored 0.8 mm into wedge.
    return clean(Polygon([center+tangent*t+normal*n for t, n in
                          [(-5, -0.8), (-5, 0), (-7, 6), (7, 6), (5, 0), (5, -0.8)]]))


def make_sections(cells):
    sections = []
    for i in range(7):
        group = [c for c in cells if c["section"] == i]
        footprint = union([c["outer"] for c in group])
        sections.append(dict(index=i, cells=group, original=footprint, sockets=[], tongues=[]))
    strengthen_outer_rim(sections)
    for wedge in sections[1:]:
        candidates = []
        for inner in sections[0]["cells"]:
            for outer in wedge["cells"]:
                if abs(math.hypot(inner["cx"]-outer["cx"], inner["cy"]-outer["cy"])-PITCH) > 1e-5:
                    continue
                tongue = tongue_between(inner, outer)
                socket = clean(tongue.buffer(JOINT_CLEARANCE, join_style=2))
                if socket.difference(union([inner["outer"], outer["outer"]])).area < 1e-5:
                    candidates.append((inner, outer, tongue, socket))
        if not candidates:
            raise ValueError(f"No hub connection for section {wedge['index']}")
        inner, outer, tongue, socket = candidates[len(candidates)//2]
        sections[0]["sockets"].append(socket)
        wedge["tongues"].append(tongue)
        wedge["connection"] = (inner, outer)
    for section in sections:
        section["footprint"] = union([section["original"]]+section["tongues"]).difference(union(section["sockets"]))
        if not isinstance(section["footprint"], Polygon) or not section["footprint"].is_valid:
            raise ValueError("Disconnected or invalid section")
    return sections


def label(text, cx, cy, size):
    p = union(char_to_polygons(text, find_default_font(), size=size))
    if p.is_empty:
        raise ValueError(f"Unable to render {text}")
    x0, y0, x1, y1 = p.bounds
    return clean(translate(p, cx-(x0+x1)/2, cy-(y0+y1)/2))


def make_layers(section):
    inks = {1: [], 2: [], 3: []}
    labels = []
    for c in section["cells"]:
        desc = c["desc"]
        if desc == "BLANK":
            continue
        color = 3 if desc == "TRIPLE WORD" else 2 if "LETTER" in desc else 1
        inks[color].append(c["pocket"])
        text = {"START": "★", "TRIPLE WORD": "TW", "DOUBLE WORD": "DW",
                "TRIPLE LETTER": "TL", "DOUBLE LETTER": "DL"}.get(desc)
        if desc == "START":
            # A geometric star prints consistently even if the local font lacks ★.
            p = clean(Polygon([(c["cx"] + radius*math.cos(math.pi/2+i*math.pi/5),
                                c["cy"] + radius*math.sin(math.pi/2+i*math.pi/5))
                               for i in range(10) for radius in [7.5 if i % 2 == 0 else 3.2]]))
        elif desc == "KEY WILD (DW)":
            p = union([label("DW", c["cx"], c["cy"]+3, 8), label("KEY", c["cx"], c["cy"]-4, 6)])
        else:
            p = label(text, c["cx"], c["cy"], 15 if desc == "START" else 8)
        if p.difference(c["pocket"]).area > 1e-6:
            raise ValueError("Text outside pocket")
        labels.append(p)
    footprint = section["footprint"]
    inks = {i: union(polys).intersection(footprint) for i, polys in inks.items()}
    text = union(labels).intersection(footprint)
    ribs = section["original"].difference(union([c["pocket"] for c in section["cells"]])).difference(union(section["sockets"]))
    # Disjoint solids in each Z interval: base, colored inlay, and flush text.
    layers = [(0, "Foundation", footprint, 0, 1.2),
              (0, "Pocket floors", footprint.difference(union(list(inks.values()))), 1.2, 2),
              (0, "Divider ribs", ribs, 2, 3.6),
              (1, "Ivory grid caps", ribs, 3.6, 4), (0, "Flush labels", text, 1.6, 2)]
    for color, ink in inks.items():
        layers += [(color, "Inlay backing", ink, 1.2, 1.6),
                   (color, "Inlay face", ink.difference(text), 1.6, 2)]
    return [layer for layer in layers if not layer[2].is_empty]


def placement(footprint):
    candidates = []
    for angle in range(180):
        x0, y0, x1, y1 = rotate(footprint, angle, origin=(0, 0)).bounds
        w, h = x1-x0, y1-y0
        if w <= WIDTH and h <= HEIGHT:
            candidates.append((max(w, h), angle, w, h, x0, y0))
    if not candidates:
        # A broad hub can use the empty corner around the tower instead of a strip.
        from shapely.geometry import box
        tower = box(225, 225, 265, 265)
        for angle in range(180):
            rotated = rotate(footprint, angle, origin=(0, 0))
            x0, y0, x1, y1 = rotated.bounds
            w, h = x1-x0, y1-y0
            if w > HEIGHT or h > HEIGHT:
                continue
            dx, dy = MARGIN-x0, MARGIN-y0
            if translate(rotated, dx, dy).distance(tower) >= TOWER_GAP:
                candidates.append((max(w, h), angle, w, h, x0, y0))
        if not candidates:
            raise ValueError("Cannot fit bed with margins and tower clearance")
        _, angle, w, h, x0, y0 = min(candidates)
        return dict(rotation_deg=angle, translation_mm=[MARGIN-x0, MARGIN-y0],
                    width_mm=round(w, 3), height_mm=round(h, 3))
    _, angle, w, h, x0, y0 = min(candidates)
    return dict(rotation_deg=angle, translation_mm=[MARGIN+(WIDTH-w)/2-x0, MARGIN+(HEIGHT-h)/2-y0],
                width_mm=round(w, 3), height_mm=round(h, 3))


def placed(poly, record):
    return translate(rotate(poly, record["rotation_deg"], origin=(0, 0)), *record["translation_mm"])


def parts_for(section, record):
    return [(f"[Slot {color+1} - {NAMES[color]}] {name}", extrude_poly(placed(poly, record), z0, z1), color)
            for color, name, poly, z0, z1 in make_layers(section)]


def preview(sections, records):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch, Rectangle
    from shapely.geometry.polygon import orient
    def draw(ax, geom, color):
        if geom.is_empty:
            return
        for p in [geom] if isinstance(geom, Polygon) else geom.geoms:
            p = orient(p)
            vertices, codes = [], []
            for ring in [p.exterior]+list(p.interiors):
                xy = list(ring.coords)
                vertices += xy
                codes += [MplPath.MOVETO]+[MplPath.LINETO]*(len(xy)-2)+[MplPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor=color, edgecolor="none"))
    fig, axes = plt.subplots(1, 2, figsize=(15, 10), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.set_facecolor("#101116")
    for ax in axes:
        ax.set_facecolor("#101116")
        ax.set_aspect("equal")
        ax.axis("off")
    for section in sections:
        i = section["index"]
        a = math.radians((i-1)*60+30)
        dx, dy = (0, 0) if i == 0 else (4*math.cos(a), 4*math.sin(a))
        for color, _, poly, _, _ in sorted(make_layers(section), key=lambda layer: layer[4]):
            draw(axes[0], translate(poly, dx, dy), COLORS[color])
        if i:
            axes[0].text(345*math.cos(a), 345*math.sin(a), f"{i+1:02}", color="#BBBBBB", ha="center", va="center")
    axes[0].set_xlim(-400, 400)
    axes[0].set_ylim(-410, 410)
    axes[0].set_title("BUZZLE · 217 CELLS · FOUR COLORS", color="white", fontsize=16)
    axes[0].text(0, -395, f"{TILE_FLAT:.2f} mm (1.3 inch) tiles / {POCKET_FLAT:.2f} mm pockets\n7 sections · small gaps shown for assembly", ha="center", color="#CCCCCC", fontsize=11)
    i = max(range(len(records)), key=lambda i: records[i]["width_mm"]*records[i]["height_mm"])
    record = records[i]
    axes[1].add_patch(Rectangle((0, 0), BED, BED, facecolor="#24262C", edgecolor="#AAAAAA"))
    for color, _, poly, _, _ in sorted(make_layers(sections[i]), key=lambda layer: layer[4]):
        draw(axes[1], placed(poly, record), COLORS[color])
    axes[1].add_patch(Rectangle((225, 225), 40, 40, facecolor="none", edgecolor="white", linestyle="--"))
    axes[1].text(245, 245, "40 mm\ntower", color="white", ha="center", va="center", fontsize=8)
    axes[1].set_xlim(-5, 275)
    axes[1].set_ylim(-75, 310)
    axes[1].set_title("270 × 270 mm PRINT BED", color="white", fontsize=14)
    axes[1].text(135, -18, f"Largest section: {record['width_mm']:.1f} × {record['height_mm']:.1f} mm\n5 mm bed margins + reserved tower space", color="#CCCCCC", ha="center", va="top", fontsize=11)
    for i, (name, color) in enumerate(zip(NAMES, COLORS)):
        axes[1].add_patch(Rectangle((15+i*65, -60), 10, 10, facecolor=color, edgecolor="#999999"))
        axes[1].text(28+i*65, -55, name, color="white", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT/"images/board_and_bed_preview.png", dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


def generate():
    (OUTPUT/"plates").mkdir(parents=True, exist_ok=True)
    (OUTPUT/"images").mkdir(parents=True, exist_ok=True)
    cells = make_cells()
    sections = make_sections(cells)
    records = []
    for s in sections:
        i = s["index"]
        name = "Center_Hub" if i == 0 else f"Sector_{(i-1)*60:03}_{i*60:03}"
        record = dict(file=f"plates/Plate_{i+1:02}_{name}.3mf", cells=len(s["cells"]),
                      coordinates=[c["coord"] for c in s["cells"]], **placement(s["footprint"]))
        export_multimaterial_3mf(OUTPUT/record["file"], parts_for(s, record), name, palette=COLORS)
        records.append(record)
        print(f"{record['file']}: {record['cells']} cells, {record['width_mm']} x {record['height_mm']} mm", flush=True)
    board = union([s["original"] for s in sections])
    x0, y0, x1, y1 = board.bounds
    manifest = dict(tile_flat_mm=TILE_FLAT, pocket_flat_mm=POCKET_FLAT, pitch_mm=PITCH,
                    board_size_mm=[round(x1-x0, 3), round(y1-y0, 3)], bed_size_mm=BED,
                    margin_mm=MARGIN, tower_region_mm=[225, 225, 265, 265], colors=COLORS, plates=records)
    (OUTPUT/"print_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    # Print-first test: two separated, full-size pockets with the actual joint.
    inner, outer = sections[1]["connection"]
    socket, tongue = sections[0]["sockets"][0], sections[1]["tongues"][0]
    parts = []
    for i, cell in enumerate([inner, outer]):
        sample = dict(cells=[cell], original=cell["outer"], sockets=[socket] if i == 0 else [],
                      footprint=cell["outer"].difference(socket) if i == 0 else union([cell["outer"], tongue]))
        record = dict(rotation_deg=0, translation_mm=[30+i*65-cell["cx"], 35-cell["cy"]])
        parts.extend(parts_for(sample, record))
    export_multimaterial_3mf(OUTPUT/"plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf", parts, "Pocket & joint test", palette=COLORS)
    preview(sections, records)
    print(f"Assembled: {x1-x0:.1f} x {y1-y0:.1f} mm. Output: {OUTPUT}")


if __name__ == "__main__":
    generate()
