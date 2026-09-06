"""BUZZHEX: an 11 x 11 Hex board for the unchanged Buzzello reversible tiles."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, box

from generate_board_270 import clean, union, tongue_between, placement, placed, strengthen_outer_rim
from generate_buzzle_rosette_board import extrude_poly, export_multimaterial_3mf
from generate_othello_board_270 import fit_samples
from render_new_buzzle_board import make_flat_hex_pts

OUTPUT = Path(__file__).resolve().parent / 'output/boards/buzzhex'
SIZE = 11
SECTION_COUNT = 6
TILE_FLAT, POCKET_FLAT = 33.02, 33.50
DIVIDER_WIDTH, FLOOR_HEIGHT, POCKET_DEPTH = 2.2, 2.8, 2.4
TOTAL_HEIGHT, INLAY_DEPTH = 5.2, 0.8
JOINT_CLEARANCE, SEAM_GAP, RIM_EXTRA = 0.40, 0.30, 6.0
PITCH = POCKET_FLAT + DIVIDER_WIDTH
COLORS, NAMES = ['#000000', '#FFFF00', '#FFFFFF'], ['Black', 'Yellow', 'White']
NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def make_cells():
    cells = []
    for q in range(SIZE):
        for r in range(SIZE):
            cx = (q+r-(SIZE-1))*PITCH*math.sqrt(3)/2
            cy = (r-q)*PITCH/2
            cells.append(dict(coord=(q, r), cx=cx, cy=cy,
                              section=q//4+3*int(r >= 6),
                              outer=clean(Polygon(make_flat_hex_pts(cx, cy, PITCH))),
                              pocket=clean(Polygon(make_flat_hex_pts(cx, cy, POCKET_FLAT)))))
    return cells


def make_sections(cells):
    sections = []
    for i in range(SECTION_COUNT):
        group = [c for c in cells if c['section'] == i]
        sections.append(dict(index=i, cells=group, original=union([c['outer'] for c in group]),
                             sockets=[], tongues=[]))
    strengthen_outer_rim(sections, extra=RIM_EXTRA)
    for first, second in [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]:
        a, b = sections[first], sections[second]
        candidates = []
        for inner in a['cells']:
            for outer in b['cells']:
                if abs(math.hypot(inner['cx']-outer['cx'], inner['cy']-outer['cy'])-PITCH) > 1e-5:
                    continue
                tongue = tongue_between(inner, outer)
                socket = clean(tongue.buffer(JOINT_CLEARANCE, join_style=2))
                if socket.difference(union([inner['outer'], outer['outer']])).area < 1e-4:
                    candidates.append((inner, outer, tongue, socket))
        candidates.sort(key=lambda c: (c[0]['coord'], c[1]['coord']))
        chosen = []
        for candidate in candidates:
            if all(candidate[2].centroid.distance(old[2].centroid) > PITCH for old in chosen):
                chosen.append(candidate)
            if len(chosen) == 2:
                break
        if not chosen:
            raise ValueError('No usable seam joint')
        for inner, outer, tongue, socket in chosen:
            a['sockets'].append(socket)
            b['tongues'].append(tongue)
            b.setdefault('connections', []).append((inner, outer, socket, tongue))
    originals = [s['original'] for s in sections]
    for s in sections:
        neighbors = union([p for i, p in enumerate(originals) if i != s['index']])
        s['original'] = clean(s['original'].difference(neighbors.buffer(SEAM_GAP/2, join_style=2)))
        s['footprint'] = union([s['original']]+s['tongues']).difference(union(s['sockets']))
        if not isinstance(s['footprint'], Polygon) or not s['footprint'].is_valid:
            raise ValueError('Disconnected or invalid board section')
    return sections


def goal_rails(cells):
    grid = union([c['outer'] for c in cells])
    rim = clean(grid.buffer(RIM_EXTRA, quad_segs=4)).difference(grid)
    # q=0/10: upper-left/lower-right. r=0/10: lower-left/upper-right.
    # The four rhombus corner cells touch BOTH incident goal edges.
    black = rim.intersection(union([box(-1000, 0, 0, 1000), box(0, -1000, 1000, 0)]))
    return black, rim.difference(black)


def layers(section, rails):
    footprint = section['footprint']
    pockets = union([c['pocket'] for c in section['cells']]).intersection(footprint)
    walls = section['original'].difference(pockets).difference(union(section['sockets']))
    black, yellow = [p.intersection(walls) for p in rails]
    return [layer for layer in [
        (0, 'Solid foundation', footprint, 0, 2.0),
        (2, 'White pocket floors and joint tops', footprint.difference(walls), 2.0, FLOOR_HEIGHT),
        (0, 'Honeycomb walls', walls, 2.0, 4.8),
        (0, 'Black grid caps', walls.difference(union([black, yellow])), 4.8, TOTAL_HEIGHT),
        (0, 'Black goal rails q0 q10', black, 4.8, TOTAL_HEIGHT),
        (1, 'Yellow goal rails r0 r10', yellow, 4.8, TOTAL_HEIGHT),
    ] if not layer[2].is_empty]


def parts(section, record, rails):
    return [(f'[Slot {color+1} - {NAMES[color]}] {name}', extrude_poly(placed(p, record), z0, z1), color)
            for color, name, p, z0, z1 in layers(section, rails)]


def preview(cells, sections, records, rails):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch, Rectangle
    fig, axes = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={'width_ratios': [1.45, 1]})
    fig.set_facecolor('#181B20')
    for ax in axes:
        ax.set_aspect('equal'); ax.axis('off')
    def draw(ax, p, color):
        if p.is_empty:
            return
        for g in [p] if isinstance(p, Polygon) else p.geoms:
            if not isinstance(g, Polygon):
                continue
            ax.add_patch(Patch(g.exterior.coords, facecolor=color, edgecolor='none'))
            for hole in g.interiors:
                ax.add_patch(Patch(hole.coords, facecolor='#181B20', edgecolor='none'))
    def top(ax, s, record=None):
        project = (lambda p: placed(p, record)) if record else (lambda p: p)
        draw(ax, project(s['footprint']), '#000000')
        for color, name, p, z0, z1 in layers(s, rails):
            if z1 == TOTAL_HEIGHT:
                draw(ax, project(p), COLORS[color])
        for c in s['cells']:
            draw(ax, project(c['pocket']), COLORS[2])
    for s in sections:
        top(axes[0], s)
    for c in cells:
        q, r = c['coord']
        axes[0].text(c['cx'], c['cy'], f'{chr(65+q)}{r+1}', ha='center', va='center', fontsize=7, color='#555555')
    # Assembly labels sit within each section; cell labels are diagram-only.
    for s in sections:
        x = sum(c['cx'] for c in s['cells'])/len(s['cells'])
        y = sum(c['cy'] for c in s['cells'])/len(s['cells'])
        axes[0].text(x, y+8, f"SECTION {s['index']+1}", ha='center', fontsize=8, color='#222222', weight='bold',
                     bbox=dict(facecolor=COLORS[2], edgecolor='none', pad=2))
    axes[0].set(xlim=(-355, 355), ylim=(-270, 270))
    axes[0].set_title('BUZZHEX / 11 x 11 / 121 CELLS', color='white', fontsize=20, loc='left', pad=15)
    axes[0].text(0, 235, 'BLACK: A to K  /  YELLOW: 1 to 11', color='white', ha='center', fontsize=11)
    axes[0].text(0, -235, '121 reversible Buzzello tiles / same 33.02 mm size\nSix sections / shared-edge connections / opening swap rule', color='#C5CBD2', ha='center', fontsize=10)
    i = max(range(SECTION_COUNT), key=lambda i: records[i]['width_mm']*records[i]['height_mm'])
    axes[1].add_patch(Rectangle((0, 0), 270, 270, facecolor='#30353C', edgecolor='#838C97'))
    top(axes[1], sections[i], records[i])
    axes[1].add_patch(Rectangle((225, 225), 40, 40, fill=False, edgecolor='white', linestyle='--'))
    axes[1].text(245, 245, 'Purge\ntower', color='white', ha='center', va='center', fontsize=8)
    axes[1].set(xlim=(-5, 275), ylim=(-35, 290))
    axes[1].set_title('270 x 270 mm PRINT BED', color='white', fontsize=13, pad=15)
    axes[1].text(135, -19, f"Largest plate: {records[i]['width_mm']:.1f} x {records[i]['height_mm']:.1f} mm", color='#C5CBD2', ha='center', fontsize=10)
    fig.tight_layout()
    fig.savefig(OUTPUT/'images/board_and_bed_preview.png', dpi=160, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=.25)
    plt.close(fig)


def generate():
    for name in ['plates', 'images']:
        (OUTPUT/name).mkdir(parents=True, exist_ok=True)
    cells = make_cells(); sections = make_sections(cells); rails = goal_rails(cells)
    records = []
    for s in sections:
        record = dict(file=f"plates/Plate_{s['index']+1:02}_Section.3mf", cells=len(s['cells']),
                      **placement(s['footprint']))
        export_multimaterial_3mf(OUTPUT/record['file'], parts(s, record, rails),
                                f"BUZZHEX section {s['index']+1}", palette=COLORS)
        records.append(record)
        print(record['file'], record['width_mm'], record['height_mm'], flush=True)
    coupon = []
    for i, sample in enumerate(fit_samples(sections)):
        cell = sample['cells'][0]
        record = dict(rotation_deg=0, translation_mm=[30+i*60-cell['cx'], 35-cell['cy']])
        coupon.extend(parts(sample, record, (Polygon(), Polygon())))
    export_multimaterial_3mf(OUTPUT/'plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf', coupon, 'BUZZHEX fit test', palette=COLORS)
    x0, y0, x1, y1 = union([s['footprint'] for s in sections]).bounds
    manifest = dict(revision='v2_buzzhex_white_board', game='BUZZHEX', size=SIZE, cell_count=len(cells),
                    tile_flat_mm=TILE_FLAT, pocket_flat_mm=POCKET_FLAT, pitch_mm=PITCH,
                    divider_width_mm=DIVIDER_WIDTH, floor_height_mm=FLOOR_HEIGHT,
                    pocket_depth_mm=POCKET_DEPTH, total_height_mm=TOTAL_HEIGHT,
                    joint_clearance_mm=JOINT_CLEARANCE, seam_gap_mm=SEAM_GAP,
                    outer_rim_extension_mm=RIM_EXTRA, bed_mm=270,
                    board_size_mm=[round(x1-x0, 3), round(y1-y0, 3)], colors=COLORS, plates=records,
                    shared_tile='../../tiles/othello/3mf/hex_othello_piece_single.3mf',
                    pieces_required=121, extra_pieces_required_from_60_set=61)
    (OUTPUT/'print_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    spec = dict(name='BUZZHEX', size=SIZE, cell_count=121, board_background='#FFFFFF',
                tile_colors=dict(black='#000000', yellow='#FFFF00'),
                coordinates='axial q,r; 0 through 10 inclusive',
                neighbors=NEIGHBORS, black_goal=dict(axis='q', edges=[0, 10]),
                yellow_goal=dict(axis='r', edges=[0, 10]), first_color='black', swap_rule=True,
                swap_semantics='Exchange player color assignments only. Keep the opening tile black and in place. Original opener plays yellow next.',
                world_position_mm=dict(x='(q+r-10)*35.7*sqrt(3)/2', y='(r-q)*35.7/2'),
                screen_position='Use world x and NEGATIVE world y; flat-top hexagons.',
                cells=[dict(q=c['coord'][0], r=c['coord'][1], label=f"{chr(65+c['coord'][0])}{c['coord'][1]+1}",
                            cx_mm=round(c['cx'], 6), cy_mm=round(c['cy'], 6), section=c['section']+1) for c in cells])
    (OUTPUT/'game_spec.json').write_text(json.dumps(spec, indent=2)+'\n', encoding='utf-8')
    preview(cells, sections, records, rails)


if __name__ == '__main__':
    generate()
