"""91-cell, four-section BUZZELLO board for existing 1.3-inch pieces."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, Point

from generate_board_270 import clean, union, tongue_between, placement, placed, strengthen_outer_rim, thickness_preview
from generate_buzzle_rosette_board import extrude_poly, export_multimaterial_3mf
from render_new_buzzle_board import make_flat_hex_pts

OUTPUT = Path(__file__).resolve().parent / 'output/boards/othello'
COLORS = ['#000000', '#FFFF00']
NAMES = ['Black', 'Yellow']
SOURCE = Path(__file__).resolve().parent / 'assets/artwork/ares_23247_underside.geojson'
TILE_FLAT, POCKET_FLAT = 33.02, 33.50
DIVIDER_WIDTH = 2.2
FLOOR_HEIGHT = 2.8
POCKET_DEPTH = 2.4
TOTAL_HEIGHT = round(FLOOR_HEIGHT + POCKET_DEPTH, 2)
INLAY_DEPTH = 0.8
JOINT_CLEARANCE = 0.40  # Offset around the full male profile, in mm.
SEAM_GAP = 0.30  # Total assembled gap; each section gives up half.
REVISION = 'v5_black_floors_yellow_dividers'
BOARD_RADIUS = 5
CELL_COUNT = 1 + 3 * BOARD_RADIUS * (BOARD_RADIUS + 1)
PITCH = POCKET_FLAT + DIVIDER_WIDTH


def make_cells():
    cells = []
    for x in range(-BOARD_RADIUS, BOARD_RADIUS+1):
        for y in range(max(-BOARD_RADIUS, -x-BOARD_RADIUS), min(BOARD_RADIUS, -x+BOARD_RADIUS)+1):
            z = -x-y
            cx, cy = -z*PITCH*math.sqrt(3)/2, (y-x)*PITCH/2
            section = (0 if cx <= 0 else 1)+(0 if cy >= 0 else 2)
            cells.append(dict(coord=(x,y,z), cx=cx, cy=cy, section=section,
                              outer=clean(Polygon(make_flat_hex_pts(cx, cy, PITCH))),
                              pocket=clean(Polygon(make_flat_hex_pts(cx, cy, POCKET_FLAT)))))
    return cells


def make_sections(cells):
    sections=[]
    for i in range(4):
        group=[c for c in cells if c['section']==i]
        sections.append(dict(index=i,cells=group,original=union([c['outer'] for c in group]),sockets=[],tongues=[]))
    strengthen_outer_rim(sections)
    for first,second in [(0,1),(0,2),(1,3),(2,3)]:
        a,b=sections[first],sections[second]
        candidates=[]
        for inner in a['cells']:
            for outer in b['cells']:
                if abs(math.hypot(inner['cx']-outer['cx'],inner['cy']-outer['cy'])-PITCH)>1e-5:
                    continue
                tongue=tongue_between(inner,outer)
                socket=clean(tongue.buffer(JOINT_CLEARANCE,join_style=2))
                if socket.difference(union([inner['outer'],outer['outer']])).area<1e-4:
                    candidates.append((inner,outer,tongue,socket))
        # Spread two joints along each shared seam, away from the underside logo.
        candidates.sort(key=lambda item: math.hypot(item[0]['cx'],item[0]['cy']),reverse=True)
        chosen=[]
        for candidate in candidates:
            if all(candidate[2].centroid.distance(old[2].centroid)>PITCH for old in chosen):
                chosen.append(candidate)
            if len(chosen)==2:break
        if not chosen:raise ValueError('No usable seam joint')
        for inner,outer,tongue,socket in chosen:
            a['sockets'].append(socket);b['tongues'].append(tongue)
            b.setdefault('connections',[]).append((inner,outer,socket,tongue))
    # Relieve only shared boundaries. Keep the outer perimeter and pocket
    # geometry fixed; adding tongues afterwards preserves their engagement.
    originals=[s['original'] for s in sections]
    for s in sections:
        neighbors=union([p for i,p in enumerate(originals) if i!=s['index']])
        s['original']=clean(s['original'].difference(neighbors.buffer(SEAM_GAP/2,join_style=2)))
        s['footprint']=union([s['original']]+s['tongues']).difference(union(s['sockets']))
        if not isinstance(s['footprint'],Polygon):raise ValueError('Disconnected board section')
    return sections


def fit_samples(sections):
    """Use the production seam relief and socket for the two-cell fit test."""
    inner,outer,socket,tongue=sections[1]['connections'][0]
    samples=[]
    for i,cell in enumerate([inner,outer]):
        original=clean(cell['outer'].intersection(sections[cell['section']]['original']))
        samples.append(dict(cells=[cell],original=original,sockets=[socket] if i==0 else [],
                            footprint=original.difference(socket) if i==0 else union([original,tongue])))
    return samples


def underside_logo():
    """Original ARES artwork preserved as portable vector geometry."""
    from shapely.geometry import shape
    return clean(shape(json.loads(SOURCE.read_text(encoding='utf-8'))))


def layers(s,logo):
    footprint=s['footprint'];sockets=union(s['sockets'])
    pockets=union([c['pocket'] for c in s['cells']]).intersection(footprint)
    walls=s['original'].difference(pockets).difference(sockets)
    anchors=[];starts=[]
    for c in s['cells']:
        coord=c['coord'];dist=max(map(abs,coord));center=Point(c['cx'],c['cy'])
        if dist==BOARD_RADIUS and 0 in coord:
            anchors.append(center.buffer(9,quad_segs=24).difference(center.buffer(7.8,quad_segs=24)))
        if dist==1:
            # Alternating filled/hollow yellow circles identify the starting sides.
            angle=round(math.degrees(math.atan2(c['cy'],c['cx'])))%360
            disc=center.buffer(4.5,quad_segs=24)
            starts.append(disc if angle in (90,210,330) else disc.difference(center.buffer(3.3,quad_segs=24)))
    anchors=union(anchors).intersection(pockets);starts=union(starts).intersection(pockets)
    logo=logo.intersection(footprint)
    return [(color,name,p,z0,z1) for color,name,p,z0,z1 in [
        (0,'Foundation',footprint.difference(logo),0,.8),
        (1,'ARES 23247 underside inlay',logo,0,.8),
        (0,'Solid middle floor',footprint,.8,round(FLOOR_HEIGHT-INLAY_DEPTH,2)),
        (1,'Honeycomb walls',walls,round(FLOOR_HEIGHT-INLAY_DEPTH,2),TOTAL_HEIGHT),
        (0,'Joint tops',footprint.difference(s['original']),round(FLOOR_HEIGHT-INLAY_DEPTH,2),FLOOR_HEIGHT),
        (0,'Pocket floors',pockets.difference(union([anchors,starts])),round(FLOOR_HEIGHT-INLAY_DEPTH,2),FLOOR_HEIGHT),
        (1,'Starting side markers',starts,round(FLOOR_HEIGHT-INLAY_DEPTH,2),FLOOR_HEIGHT),
        (1,'Six corner anchors',anchors,round(FLOOR_HEIGHT-INLAY_DEPTH,2),FLOOR_HEIGHT)] if not p.is_empty]


def parts(s,record,logo):
    return [(f'[Slot {color+1} - {NAMES[color]}] {name}',extrude_poly(placed(p,record),z0,z1),color)
            for color,name,p,z0,z1 in layers(s,logo)]


def preview(sections,records,logo):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch, Rectangle
    fig,axes=plt.subplots(1,2,figsize=(13,8));fig.set_facecolor('#141619')
    for ax in axes:ax.set_aspect('equal');ax.axis('off');ax.set_facecolor('#141619')
    def draw(ax,p,color):
        if p.is_empty:return
        for g in [p] if isinstance(p,Polygon) else p.geoms:
            ax.add_patch(Patch(g.exterior.coords,facecolor=color,edgecolor='none'))
            for hole in g.interiors:ax.add_patch(Patch(hole.coords,facecolor=COLORS[0],edgecolor='none'))
    for s in sections:
        draw(axes[0],s['footprint'],COLORS[0])
        for color,name,p,z0,z1 in layers(s,logo):
            if z1>=FLOOR_HEIGHT:draw(axes[0],p,COLORS[color])
        p=s['original'].representative_point()
        axes[0].text(p.x,p.y,str(s['index']+1),color='#777777',fontsize=14,ha='center')
    x0,y0,x1,y1=union([s['footprint'] for s in sections]).bounds
    axes[0].set_xlim(x0-20,x1+20);axes[0].set_ylim(y0-42,y1+20)
    axes[0].set_title(f'BUZZELLO · {CELL_COUNT} CELLS · FOUR SECTIONS',color='white',fontsize=13)
    axes[0].text(0,y0-30,'1.3-inch pieces unchanged · 33.5 mm pockets\nFilled / hollow markers: the two starting sides',color='white',ha='center',fontsize=10)
    i=max(range(4),key=lambda i:records[i]['width_mm']*records[i]['height_mm']);r=records[i]
    axes[1].add_patch(Rectangle((0,0),270,270,facecolor='#292D32',edgecolor='white'))
    draw(axes[1],placed(sections[i]['footprint'],r),COLORS[0])
    for color,name,p,z0,z1 in layers(sections[i],logo):
        if z1>=FLOOR_HEIGHT:draw(axes[1],placed(p,r),COLORS[color])
    axes[1].add_patch(Rectangle((225,225),40,40,fill=False,edgecolor='white',linestyle='--'))
    axes[1].text(245,245,'Purge\ntower',color='white',ha='center',va='center',fontsize=8)
    axes[1].set_xlim(-5,275);axes[1].set_ylim(-35,290)
    axes[1].set_title('270 × 270 mm BED',color='white',fontsize=13)
    axes[1].text(135,-15,f"Largest section: {r['width_mm']:.1f} × {r['height_mm']:.1f} mm",color='white',ha='center')
    fig.tight_layout();fig.savefig(OUTPUT/'images/board_and_bed_preview.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)


def joint_preview(sections):
    """Dimensioned plan view of the production joint, before and after relief."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch
    from shapely.affinity import translate, rotate
    inner,outer,_,tongue=sections[1]['connections'][0]
    mx,my=(inner['cx']+outer['cx'])/2,(inner['cy']+outer['cy'])/2
    angle=math.degrees(math.atan2(inner['cy']-outer['cy'],inner['cx']-outer['cx']))
    old=[inner['outer'].difference(tongue.buffer(.2,join_style=2)),union([outer['outer'],tongue])]
    current=[sample['footprint'] for sample in fit_samples(sections)]
    fig,axes=plt.subplots(1,2,figsize=(11,6),layout='constrained')
    for ax,shapes,title,note in zip(axes,[old,current],
            ['Previous joint','Revised joint · v3'],
            ['0.20 mm socket clearance · seams touch',
             f'{JOINT_CLEARANCE:.2f} mm socket clearance · {SEAM_GAP:.2f} mm seam gap']):
        for p,color in zip(shapes,['#41464D','#E4B928']):
            p=rotate(translate(p,xoff=-mx,yoff=-my),-angle,origin=(0,0))
            ax.add_patch(Patch(p.exterior.coords,facecolor=color,edgecolor='#181B20',linewidth=.7))
        ax.set(xlim=(-8,10),ylim=(-11,11),aspect='equal',xlabel='mm',ylabel='mm')
        ax.set_title(title,fontweight='bold',pad=14)
        ax.text(.5,-.17,note,transform=ax.transAxes,ha='center',fontsize=10)
        ax.annotate('Seam',xy=(0,9),xytext=(3,9.5),arrowprops=dict(arrowstyle='->',color='white'),color='white',fontsize=10)
        ax.annotate('Tab / socket gap',xy=(4,6.65),xytext=(1,8),arrowprops=dict(arrowstyle='->',color='white'),color='white',fontsize=9)
    fig.suptitle('BUZZELLO / OTHELLO · JOINT FIT\nTop view of the base; colors distinguish the two sections',fontsize=14)
    fig.savefig(OUTPUT/'images/joint_clearance_comparison.png',dpi=160)
    plt.close(fig)


def generate():
    (OUTPUT/'plates').mkdir(parents=True,exist_ok=True)
    (OUTPUT/'images').mkdir(parents=True,exist_ok=True)
    cells=make_cells();sections=make_sections(cells);logo=underside_logo();records=[]
    for s,name in zip(sections,['Top_Left','Top_Right','Bottom_Left','Bottom_Right']):
        r=dict(file=f"plates/Plate_{s['index']+1:02}_{name}.3mf",cells=len(s['cells']),**placement(s['footprint']))
        export_multimaterial_3mf(OUTPUT/r['file'],parts(s,r,logo),name,palette=COLORS)
        records.append(r);print(r['file'],r['width_mm'],r['height_mm'],flush=True)
    x0,y0,x1,y1=union([s['original'] for s in sections]).bounds
    manifest=dict(revision=REVISION,board_radius=BOARD_RADIUS,cell_count=len(cells),tile_flat_mm=TILE_FLAT,pocket_flat_mm=POCKET_FLAT,pitch_mm=PITCH,bed_mm=270,
                  divider_width_mm=DIVIDER_WIDTH,floor_height_mm=FLOOR_HEIGHT,
                  pocket_depth_mm=POCKET_DEPTH,total_height_mm=TOTAL_HEIGHT,
                  joint_clearance_mm=JOINT_CLEARANCE,seam_gap_mm=SEAM_GAP,
                  board_size_mm=[round(x1-x0,3),round(y1-y0,3)],colors=COLORS,
                  color_roles={'Black':'Foundation, pocket floors and joint tops',
                               'Yellow':'Raised dividers, starting markers, corner rings and underside artwork'},
                  plates=records)
    (OUTPUT/'print_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    coupon=[]
    for i,sample in enumerate(fit_samples(sections)):
        cell=sample['cells'][0]
        record=dict(rotation_deg=0,translation_mm=[30+i*60-cell['cx'],35-cell['cy']])
        coupon.extend(parts(sample,record,Polygon()))
    export_multimaterial_3mf(OUTPUT/'plates/PRINT_FIRST_Pocket_and_Joint_Test.3mf',coupon,'Othello fit test',palette=COLORS)
    preview(sections,records,logo)
    joint_preview(sections)
    thickness_preview(OUTPUT,'OTHELLO',POCKET_FLAT,DIVIDER_WIDTH,FLOOR_HEIGHT,POCKET_DEPTH,
                      previous=(1.4,2.4,.8))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size',choices=['classic','large','both'],default='large')
    args=parser.parse_args()
    for edition in (['classic','large'] if args.size=='both' else [args.size]):
        BOARD_RADIUS=4 if edition=='classic' else 5
        CELL_COUNT=1+3*BOARD_RADIUS*(BOARD_RADIUS+1)
        REVISION='v5_black_floors_yellow_dividers'
        OUTPUT=Path(__file__).resolve().parent/('output/boards/othello-classic' if edition=='classic' else 'output/boards/othello')
        generate()
