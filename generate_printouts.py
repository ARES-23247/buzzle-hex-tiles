"""
Printable Game Boards, Rulebooks, and Score Sheets for 1.5" Hex Tiles
====================================================================
Generates high-resolution, vector-scaled printable PDFs:
  1. hex_game_board_1.5in.pdf       - Hexagonal board calibrated to exact 1.5" tiles with bonus multipliers
  2. hex_games_rulebook.pdf         - Illustrated 4-page rulebook for 5 original games
  3. score_sheets_and_tracker.pdf   - Printable score tracker & tile inventory reference
  4. number_hive_math_puzzles.pdf   - Printable math challenge sheets & rosette puzzles
"""

import os
import math
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ========================================================================
# Helper: Draw Regular Hexagon on Canvas
# ========================================================================

def draw_hexagon(c, center_x, center_y, flat_to_flat, fill_color=None, stroke_color=HexColor('#333333'), stroke_width=1):
    """Draw a flat-topped regular hexagon on a ReportLab canvas."""
    r = flat_to_flat / 2.0
    R = r / math.cos(math.radians(30))
    s_half = r * math.tan(math.radians(30))
    
    pts = [
        (center_x + s_half, center_y + r),
        (center_x - s_half, center_y + r),
        (center_x - R, center_y),
        (center_x - s_half, center_y - r),
        (center_x + s_half, center_y - r),
        (center_x + R, center_y)
    ]
    
    p = c.beginPath()
    p.moveTo(pts[0][0], pts[0][1])
    for pt in pts[1:]:
        p.lineTo(pt[0], pt[1])
    p.close()
    
    if fill_color:
        c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_width)
    
    c.drawPath(p, fill=(fill_color is not None), stroke=True)


# ========================================================================
# PDF 1: Exact 1.5" Hexagonal Game Board
# ========================================================================

def generate_hex_board_pdf(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    page_w, page_h = letter # 8.5 x 11 inches (612 x 792 points)
    
    tile_f2f = 1.5 * inch # Exact 1.5 inch
    r = tile_f2f / 2.0
    R = r / math.cos(math.radians(30))
    dx = 1.5 * R
    dy = tile_f2f
    
    center_page_x = page_w / 2.0
    center_page_y = (page_h / 2.0) - 0.2 * inch
    
    # Title Header
    c.setFillColor(HexColor('#1A1A1A'))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_w / 2.0, page_h - 0.55 * inch, "HEX-WORDS & NUMBER HIVE: OFFICIAL BOARD")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#555555'))
    c.drawCentredString(page_w / 2.0, page_h - 0.72 * inch, "Grid calibrated for 1.5\" (38.1 mm) Hexagonal 3D Printed Tiles • Standard 3-Axis Crossword Layout")
    
    # Define Board Layout Grid (-Q to +Q in axial coords)
    # Radius of hex board in tiles
    grid_radius = 3
    
    # Special multiplier cells: (q, r): ('type', 'label', bg_color, text_color)
    special_cells = {
        (0, 0): ('STAR', '★\nSTART', HexColor('#FFE082'), HexColor('#5D4037')),
        (0, -3): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        (0, 3): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        (3, 0): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        (-3, 0): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        (3, -3): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        (-3, 3): ('3W', '3x\nWORD', HexColor('#E57373'), HexColor('#B71C1C')),
        
        (1, -2): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        (-1, 2): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        (2, -1): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        (-2, 1): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        (1, 1): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        (-1, -1): ('2W', '2x\nWORD', HexColor('#FF8A80'), HexColor('#C62828')),
        
        (0, -2): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        (0, 2): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        (2, 0): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        (-2, 0): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        (2, -2): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        (-2, 2): ('3L', '3x\nLET', HexColor('#64B5F6'), HexColor('#0D47A1')),
        
        (1, -1): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B')),
        (-1, 1): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B')),
        (1, 0): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B')),
        (-1, 0): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B')),
        (0, 1): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B')),
        (0, -1): ('2L', '2x\nLET', HexColor('#81D4FA'), HexColor('#01579B'))
    }
    
    # Draw Hexagonal Board Grid
    for q in range(-grid_radius, grid_radius + 1):
        r1 = max(-grid_radius, -q - grid_radius)
        r2 = min(grid_radius, -q + grid_radius)
        for r_coord in range(r1, r2 + 1):
            # Axial to Pixel coordinates
            cx = center_page_x + (q * dx)
            cy = center_page_y + (r_coord * dy + q * (dy / 2.0))
            
            cell_info = special_cells.get((q, r_coord))
            if cell_info:
                _, label, bg_col, text_col = cell_info
                draw_hexagon(c, cx, cy, tile_f2f, fill_color=bg_col, stroke_color=HexColor('#8D6E63'), stroke_width=1.2)
                
                # Draw Label
                lines = label.split('\n')
                c.setFillColor(text_col)
                c.setFont("Helvetica-Bold", 8 if len(lines) > 1 else 10)
                if len(lines) == 1:
                    c.drawCentredString(cx, cy - 3, lines[0])
                else:
                    c.drawCentredString(cx, cy + 2, lines[0])
                    c.drawCentredString(cx, cy - 8, lines[1])
            else:
                # Regular Cell
                draw_hexagon(c, cx, cy, tile_f2f, fill_color=HexColor('#FAFAFA'), stroke_color=HexColor('#BDBDBD'), stroke_width=0.8)
                c.setFillColor(HexColor('#E0E0E0'))
                c.circle(cx, cy, 2, fill=1, stroke=0)
                
    # Footer & Legend
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor('#333333'))
    legend_y = 0.5 * inch
    c.drawString(0.8 * inch, legend_y, "BONUS LEGEND:")
    
    c.setFont("Helvetica", 8)
    items = [
        ("★ Start (Center)", HexColor('#FFE082')),
        ("2x Letter (2L)", HexColor('#81D4FA')),
        ("3x Letter (3L)", HexColor('#64B5F6')),
        ("2x Word (2W)", HexColor('#FF8A80')),
        ("3x Word (3W)", HexColor('#E57373'))
    ]
    
    cur_x = 2.0 * inch
    for lbl, col in items:
        c.setFillColor(col)
        c.rect(cur_x, legend_y - 2, 10, 10, fill=1, stroke=0)
        c.setFillColor(HexColor('#222222'))
        c.drawString(cur_x + 14, legend_y, lbl)
        cur_x += 1.25 * inch
        
    c.save()


# ========================================================================
# PDF 2: Official Games Rulebook (4 Pages, Printable Pamphlet)
# ========================================================================

def generate_rulebook_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.6*inch, bottomMargin=0.6*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontSize=20, leading=24, textColor=HexColor('#D84315'),
        alignment=1, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub', parent=styles['Normal'],
        fontSize=10, leading=14, textColor=HexColor('#5D4037'),
        alignment=1, spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading2'],
        fontSize=13, leading=16, textColor=HexColor('#BF360C'),
        spaceBefore=10, spaceAfter=4, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading3'],
        fontSize=10, leading=13, textColor=HexColor('#2E7D32'),
        spaceBefore=6, spaceAfter=2, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=8.5, leading=11.5, textColor=HexColor('#212121'),
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style,
        leftIndent=12, firstLineIndent=-8, spaceAfter=2
    )
    callout_style = ParagraphStyle(
        'Callout', parent=body_style,
        fontSize=8.5, leading=11.5, textColor=HexColor('#1B5E20'),
        backColor=HexColor('#E8F5E9'), borderColor=HexColor('#A5D6A7'),
        borderWidth=1, borderPadding=6, spaceBefore=4, spaceAfter=6
    )

    story = []
    
    # Title
    story.append(Paragraph("HEX-TILES: OFFICIAL COMPENDIUM OF GAMES", title_style))
    story.append(Paragraph("5 Original & Classic Games for 1.5\" Hexagonal Letter & Number 3D Printed Tiles", subtitle_style))
    
    # GAME 1
    story.append(Paragraph("GAME 1: HEX-WORDS (Free-form Tabletop Crossword)", h1_style))
    story.append(Paragraph("<b>Players:</b> 2–4 • <b>Time:</b> 30–45 min • <b>Components:</b> Letter Tiles with Point Subscripts", body_style))
    story.append(Paragraph("Hex-Words expands traditional crossword play into <b>3 continuous axes (0°, 60°, 120°)</b> without requiring a fixed board. Tiles connect edge-to-edge on any flat table.", body_style))
    story.append(Paragraph("<b>Gameplay & Rules:</b>", h2_style))
    story.append(Paragraph("• <b>Hand Size:</b> Each player draws 7 tiles from the face-down pool into their hand.", bullet_style))
    story.append(Paragraph("• <b>First Word:</b> Player 1 places a valid word of 2+ letters anywhere in the center of the table.", bullet_style))
    story.append(Paragraph("• <b>Turn Actions:</b> On your turn, place 1 or more tiles to form new connected words along any of the 3 hex axes. Every newly formed line of adjacent tiles must form a valid dictionary word.", bullet_style))
    story.append(Paragraph("• <b>The 3 Hex Axes:</b> Words are read straight in any of the 3 hexagonal grid directions (Left-to-Right, Top-Left to Bottom-Right, Bottom-Left to Top-Right).", bullet_style))
    story.append(Paragraph("• <b>Honeycomb Bonus (+15 Pts):</b> If your placed tiles complete a closed 6-tile hexagonal ring surrounding an open center (a 'Honeycomb Cell'), immediately score a +15 point bonus!", callout_style))
    story.append(Paragraph("• <b>Tri-Intersection Bonus (2x Total):</b> If a single placed tile simultaneously completes words along all 3 axes, double the entire turn's score.", bullet_style))
    
    story.append(Spacer(1, 6))
    
    # GAME 2
    story.append(Paragraph("GAME 2: HIVE-SWARM (Real-Time Speed Word Race)", h1_style))
    story.append(Paragraph("<b>Players:</b> 2–6 • <b>Time:</b> 10–15 min • <b>Components:</b> Complete Letter Pool", body_style))
    story.append(Paragraph("A high-octane, simultaneous speed race where players compete to build their own independent hexagonal honeycombs with zero turn waiting.", body_style))
    story.append(Paragraph("<b>Bee-Themed Rules & Terminology:</b>", h2_style))
    story.append(Paragraph("• <b>The Meadow:</b> Place all letter tiles face-down in the center of the table (the 'Meadow'). Each player draws 12 tiles.", bullet_style))
    story.append(Paragraph("• <b>The Launch:</b> Any player shouts <i>'SWARM!'</i>. All worker bees simultaneously flip their tiles and race to connect all letters into a continuous personal honeycomb.", bullet_style))
    story.append(Paragraph("• <b>Gathering Pollen (Foraging):</b> When a player successfully connects all their current tiles into valid words, they shout <i>'FORAGE!'</i> (or <i>'POLLEN!'</i>). Every player must immediately draw 1 additional tile from the Meadow.", bullet_style))
    story.append(Paragraph("• <b>Ejecting Bad Letters:</b> If a player gets stuck with difficult letters, they may shout <i>'EJECT!'</i>, discard 1 troublesome tile back into the Meadow, and draw 2 new random tiles.", bullet_style))
    story.append(Paragraph("• <b>Winning the Crown:</b> When fewer tiles remain in the Meadow than players, the first worker to lock all their tiles into valid connected words shouts <i>'QUEEN'S COMB!'</i> to freeze the round and win!", callout_style))
    
    story.append(Spacer(1, 6))
    
    # GAME 3
    story.append(Paragraph("GAME 3: NUMBER HIVE / EQUATION CLASH", h1_style))
    story.append(Paragraph("<b>Players:</b> 2–4 • <b>Time:</b> 20–30 min • <b>Components:</b> Number (0–9) and Math Symbol (+, -, x, /, =) Tiles", body_style))
    story.append(Paragraph("A strategic numerical game where players build intersecting equations across the 3 hex axes.", body_style))
    story.append(Paragraph("<b>Gameplay & Rules:</b>", h2_style))
    story.append(Paragraph("• <b>Hand Size:</b> Each player draws 6 Number tiles and 2 Math Symbol tiles.", bullet_style))
    story.append(Paragraph("• <b>Valid Equations:</b> Equations must read in a straight hex line from left-to-right or top-to-bottom (e.g. <b>[3] [+] [5] [=] [8]</b> or <b>[9] [x] [4] [=] [3] [6]</b>).", bullet_style))
    story.append(Paragraph("• <b>Branching Math:</b> You may connect new equations through any existing number on the table (e.g. using the [8] from above to build <b>[8] [x] [2] [=] [1] [6]</b>).", bullet_style))
    story.append(Paragraph("• <b>Scoring:</b> Points awarded equal the calculated result of your equation, plus +5 bonus points for using multiplication [x] or division [/].", bullet_style))
    
    story.append(Spacer(1, 6))
    
    # GAME 4 & 5
    story.append(Paragraph("GAME 4: HONEYCOMB CROSSWORD (Board Game)", h1_style))
    story.append(Paragraph("Play with the included <b>1.5\" Hexagonal Game Board</b>. Start on the center Star (★) and expand outwards to capture <b>2x Letter (2L)</b>, <b>3x Letter (3L)</b>, <b>2x Word (2W)</b>, and <b>3x Word (3W)</b> perimeter hexes!", body_style))
    
    story.append(Paragraph("GAME 5: TARGET 24 & ROSETTE MATH (Solo / Co-op)", h1_style))
    story.append(Paragraph("Using 6 perimeter numbers and math operators around a central target hex, create an equation loop that evaluates to exactly 24 (or the target number). Use the included printable puzzle sheets for daily brain challenges!", body_style))
    
    doc.build(story)


# ========================================================================
# PDF 3: Score Sheets & Tile Inventory Reference Card
# ========================================================================

def generate_score_sheets_pdf(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    page_w, page_h = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor('#1A1A1A'))
    c.drawCentredString(page_w / 2.0, page_h - 0.55 * inch, "HEX-GAMES: SCORE SHEET & TILE TRACKER")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#666666'))
    c.drawCentredString(page_w / 2.0, page_h - 0.72 * inch, "Official Score Tracking for Hex-Words, Number Hive, and Scrabble")
    
    # Left Column: Score Tracking Table (2 Games per page)
    def draw_score_table(top_x, top_y, title):
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(HexColor('#BF360C'))
        c.drawString(top_x, top_y, title)
        
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(HexColor('#333333'))
        
        cols = ["Rnd", "Player 1", "Player 2", "Player 3", "Player 4"]
        widths = [28, 62, 62, 62, 62]
        
        cur_y = top_y - 15
        
        # Header row
        c.setFillColor(HexColor('#EFEBE9'))
        c.rect(top_x, cur_y - 2, sum(widths), 14, fill=1, stroke=1)
        c.setFillColor(HexColor('#3E2723'))
        cx = top_x
        for col_name, w in zip(cols, widths):
            c.drawCentredString(cx + w/2.0, cur_y + 2, col_name)
            cx += w
            
        cur_y -= 14
        # 12 Rounds
        for r_num in range(1, 13):
            c.setFillColor(HexColor('#FFFFFF') if r_num % 2 == 1 else HexColor('#FAFAFA'))
            c.rect(top_x, cur_y - 2, sum(widths), 14, fill=1, stroke=1)
            c.setFillColor(HexColor('#424242'))
            c.setFont("Helvetica", 8)
            
            cx = top_x
            c.drawCentredString(cx + widths[0]/2.0, cur_y + 2, str(r_num))
            cx += widths[0]
            for w in widths[1:]:
                # Empty player cell
                cx += w
            cur_y -= 14
            
        # Total Row
        c.setFillColor(HexColor('#FFE082'))
        c.rect(top_x, cur_y - 2, sum(widths), 16, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HexColor('#5D4037'))
        c.drawCentredString(top_x + widths[0]/2.0, cur_y + 3, "TOT")
        cur_y -= 16
        
    draw_score_table(0.6 * inch, page_h - 1.1 * inch, "GAME 1: SCORE TRACKER")
    draw_score_table(0.6 * inch, page_h - 5.1 * inch, "GAME 2: SCORE TRACKER")
    
    # Right Column: Scrabble & Hive Reference Inventory
    right_x = 4.8 * inch
    ref_y = page_h - 1.1 * inch
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor('#1565C0'))
    c.drawString(right_x, ref_y, "SCRABBLE TILE INVENTORY & POINTS")
    
    # Table of Letter Distributions
    c.setFont("Helvetica", 7.5)
    c.setFillColor(HexColor('#212121'))
    
    items = [
        ("A", "1 pt", "9x", "N", "1 pt", "6x"),
        ("B", "3 pts", "2x", "O", "1 pt", "8x"),
        ("C", "3 pts", "2x", "P", "3 pts", "2x"),
        ("D", "2 pts", "4x", "Q", "10 pts", "1x"),
        ("E", "1 pt", "12x", "R", "1 pt", "6x"),
        ("F", "4 pts", "2x", "S", "1 pt", "4x"),
        ("G", "2 pts", "3x", "T", "1 pt", "6x"),
        ("H", "4 pts", "2x", "U", "1 pt", "4x"),
        ("I", "1 pt", "9x", "V", "4 pts", "2x"),
        ("J", "8 pts", "1x", "W", "4 pts", "2x"),
        ("K", "5 pts", "1x", "X", "8 pts", "1x"),
        ("L", "1 pt", "4x", "Y", "4 pts", "2x"),
        ("M", "3 pts", "2x", "Z", "10 pts", "1x"),
        ("BLANK", "0 pts", "2x", "TOTAL", "—", "100 Tiles")
    ]
    
    cur_ry = ref_y - 15
    c.setFillColor(HexColor('#E3F2FD'))
    c.rect(right_x, cur_ry - 2, 210, 13, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(HexColor('#0D47A1'))
    c.drawString(right_x + 6, cur_ry + 2, "Letter")
    c.drawString(right_x + 40, cur_ry + 2, "Pts")
    c.drawString(right_x + 75, cur_ry + 2, "Qty")
    c.drawString(right_x + 110, cur_ry + 2, "Letter")
    c.drawString(right_x + 145, cur_ry + 2, "Pts")
    c.drawString(right_x + 180, cur_ry + 2, "Qty")
    
    cur_ry -= 12
    c.setFont("Helvetica", 7.5)
    c.setFillColor(HexColor('#212121'))
    
    for row in items:
        c.drawString(right_x + 6, cur_ry + 1, row[0])
        c.drawString(right_x + 40, cur_ry + 1, row[1])
        c.drawString(right_x + 75, cur_ry + 1, row[2])
        c.drawString(right_x + 110, cur_ry + 1, row[3])
        c.drawString(right_x + 145, cur_ry + 1, row[4])
        c.drawString(right_x + 180, cur_ry + 1, row[5])
        cur_ry -= 11.5
        
    # Hive Piece Reference
    cur_ry -= 15
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor('#2E7D32'))
    c.drawString(right_x, cur_ry, "HIVE PIECE REFERENCE (PER ARMY)")
    
    hive_items = [
        ("Queen Bee", "1x", "Moves 1 space per turn"),
        ("Spider", "2x", "Moves exactly 3 spaces around rim"),
        ("Beetle", "2x", "Moves 1 space; can climb on top"),
        ("Grasshopper", "3x", "Jumps straight over lines of tiles"),
        ("Soldier Ant", "3x", "Moves unlimited spaces around rim"),
        ("Mosquito (Exp)", "1x", "Copies power of adjacent bug"),
        ("Ladybug (Exp)", "1x", "2 on top of hive, 1 down (3 total)"),
        ("Pillbug (Exp)", "1x", "Moves 1 space or warps adjacent bug")
    ]
    
    cur_ry -= 14
    c.setFillColor(HexColor('#E8F5E9'))
    c.rect(right_x, cur_ry - 2, 210, 13, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(HexColor('#1B5E20'))
    c.drawString(right_x + 6, cur_ry + 2, "Insect")
    c.drawString(right_x + 85, cur_ry + 2, "Qty")
    c.drawString(right_x + 110, cur_ry + 2, "Movement Summary")
    
    cur_ry -= 12
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor('#212121'))
    for insect, qty, desc in hive_items:
        c.drawString(right_x + 6, cur_ry + 1, insect)
        c.drawString(right_x + 85, cur_ry + 1, qty)
        c.drawString(right_x + 110, cur_ry + 1, desc)
        cur_ry -= 11.5
        
    c.save()


# ========================================================================
# PDF 4: Number Hive Math Challenge & Puzzle Sheet
# ========================================================================

def generate_math_puzzles_pdf(output_path):
    c = canvas.Canvas(output_path, pagesize=letter)
    page_w, page_h = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor('#1A1A1A'))
    c.drawCentredString(page_w / 2.0, page_h - 0.55 * inch, "NUMBER HIVE: TARGET MATH PUZZLES")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#666666'))
    c.drawCentredString(page_w / 2.0, page_h - 0.72 * inch, "Place 6 Numbers & Operators around the central hub to reach the Target Number!")
    
    tile_f2f = 1.1 * inch # 1.1 inch for puzzle diagrams
    r = tile_f2f / 2.0
    R = r / math.cos(math.radians(30))
    dx = 1.5 * R
    dy = tile_f2f
    
    # Function to draw a 7-tile Rosette Puzzle
    def draw_rosette(center_x, center_y, puzzle_id, target_val, hint_text):
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(HexColor('#0288D1'))
        c.drawString(center_x - 1.6*inch, center_y + 1.6*inch, f"PUZZLE #{puzzle_id}: Target = {target_val}")
        
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(HexColor('#757575'))
        c.drawString(center_x - 1.6*inch, center_y + 1.4*inch, f"Hint: {hint_text}")
        
        # Center target tile
        draw_hexagon(c, center_x, center_y, tile_f2f, fill_color=HexColor('#FFE082'), stroke_color=HexColor('#FFA000'), stroke_width=1.5)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#E65100'))
        c.drawCentredString(center_x, center_y - 4, str(target_val))
        
        # 6 Perimeter slots (axial coordinates)
        surrounding_coords = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        slot_names = ["A", "B", "C", "D", "E", "F"]
        
        for (q, r_c), name in zip(surrounding_coords, slot_names):
            px = center_x + (q * dx)
            py = center_y + (r_c * dy + q * (dy / 2.0))
            draw_hexagon(c, px, py, tile_f2f, fill_color=HexColor('#FAFAFA'), stroke_color=HexColor('#9E9E9E'), stroke_width=0.9)
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(HexColor('#BDBDBD'))
            c.drawCentredString(px, py - 3, name)
            
    # 4 Puzzles in 2x2 Grid
    draw_rosette(2.3 * inch, page_h - 2.8 * inch, "1", "24", "Use: 8, 3, +, x, 4, 2")
    draw_rosette(6.2 * inch, page_h - 2.8 * inch, "2", "36", "Use: 9, 4, x, 6, 6, x")
    draw_rosette(2.3 * inch, page_h - 6.4 * inch, "3", "50", "Use: 5, 2, x, 5, x, 1")
    draw_rosette(6.2 * inch, page_h - 6.4 * inch, "4", "100", "Use: 7, 3, +, 1, 0, x")
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#888888'))
    c.drawCentredString(page_w / 2.0, 0.4 * inch, "Tip: Read contiguous 3-tile chains around the ring to form valid equations evaluating to the target value.")
    
    c.save()


# ========================================================================
# HTML Dashboard: Web-Viewable & Printable in Browser
# ========================================================================

def generate_html_print_hub(output_path):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Hex-Tiles Games & Printouts Hub</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; color: #222; margin: 0; padding: 20px; }
  .container { max-width: 960px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
  h1 { color: #d84315; margin-top: 0; }
  h2 { color: #2e7d32; border-bottom: 2px solid #e0e0e0; padding-bottom: 6px; margin-top: 25px; }
  .game-card { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 18px; margin-bottom: 16px; }
  .game-title { font-size: 1.25em; font-weight: bold; color: #bf360c; }
  .tag { display: inline-block; background: #e0f2f1; color: #00695c; padding: 3px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; margin-right: 6px; }
  .btn { display: inline-block; background: #1976d2; color: #fff; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; margin: 6px 6px 6px 0; }
  .btn:hover { background: #1565c0; }
  .btn-green { background: #388e3c; }
  .btn-green:hover { background: #2e7d32; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th, td { border: 1px solid #e0e0e0; padding: 8px 12px; text-align: left; font-size: 0.9em; }
  th { background: #f5f5f5; color: #333; }
  @media print {
    body { background: #fff; padding: 0; }
    .container { box-shadow: none; padding: 0; max-width: 100%; }
    .btn { display: none; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>🎲 Hex-Tiles: Games & Printouts Hub</h1>
  <p>Your complete companion portal for <b>1.5" (38.1 mm) Hexagonal 3D Printed Scrabble and Hive Game Tiles</b>.</p>

  <h2>📥 Instant PDF Printouts (Click to Open)</h2>
  <div style="margin-bottom: 20px;">
    <a class="btn" href="hex_game_board_1.5in.pdf" target="_blank">📄 1.5" Hex Game Board (PDF)</a>
    <a class="btn btn-green" href="hex_games_rulebook.pdf" target="_blank">📖 Official Rules Pamphlet (PDF)</a>
    <a class="btn" href="score_sheets_and_tracker.pdf" target="_blank">📊 Score Sheets & Inventory (PDF)</a>
    <a class="btn btn-green" href="number_hive_math_puzzles.pdf" target="_blank">🧩 Math Rosette Puzzles (PDF)</a>
  </div>

  <h2>🎮 5 Games You Can Play Right Now</h2>

  <div class="game-card">
    <div class="game-title">1. HEX-WORDS (Free-form Tabletop Crossword)</div>
    <div style="margin: 6px 0;"><span class="tag">2–4 Players</span><span class="tag">30–45 Min</span><span class="tag">Strategy</span></div>
    <p>Play crossword words across <b>3 continuous hexagonal axes</b> on any open table. Features the <b>Honeycomb Ring Bonus (+15 pts)</b> when a player completes a 6-tile closed loop around an empty space, and <b>Tri-Intersection Double Score</b> when completing words along 3 axes simultaneously!</p>
  </div>

  <div class="game-card">
    <div class="game-title">2. HIVE-SWARM (High-Speed Simultaneous Word Race)</div>
    <div style="margin: 6px 0;"><span class="tag">2–6 Players / Solo</span><span class="tag">10–15 Min</span><span class="tag">Bee-Themed Speed Race</span></div>
    <p>A frantic, no-turns speed race! Everyone starts with 12 tiles from <b>The Meadow</b>, shouts <i>'SWARM!'</i>, and races to connect them into a hexagonal honeycomb. Call <i>'FORAGE!'</i> (or <i>'POLLEN!'</i>) when your tiles are used to send all worker bees back to the Meadow for another tile, or shout <i>'EJECT!'</i> to trade out unwanted letters. First to finish all tiles calls <i>'QUEEN'S COMB!'</i> to win!</p>
  </div>

  <div class="game-card">
    <div class="game-title">3. NUMBER HIVE / EQUATION CLASH</div>
    <div style="margin: 6px 0;"><span class="tag">2–4 Players</span><span class="tag">20–30 Min</span><span class="tag">Math & Logic</span></div>
    <p>Build branching numerical equations across the 3 hex axes (e.g. <code>[3] [+] [5] [=] [8]</code> crossing with <code>[8] [x] [2] [=] [1] [6]</code>). Score points equal to the calculated results with multipliers for multiplication and division.</p>
  </div>

  <div class="game-card">
    <div class="game-title">4. HONEYCOMB CROSSWORD (Board Game)</div>
    <div style="margin: 6px 0;"><span class="tag">2–4 Players</span><span class="tag">30–60 Min</span><span class="tag">Classic Board</span></div>
    <p>Played on the printable 1.5" calibrated game board. Start on the center Star (★) and expand outwards to control Double Letter, Triple Letter, Double Word, and Triple Word bonus tiles.</p>
  </div>

  <div class="game-card">
    <div class="game-title">5. TARGET 24 & ROSETTE MATH (Solo / Co-op Puzzle)</div>
    <div style="margin: 6px 0;"><span class="tag">1–2 Players</span><span class="tag">5–10 Min per Puzzle</span><span class="tag">Brain Teaser</span></div>
    <p>Arrange 6 perimeter numbers and operators around a central target hex to evaluate to the target number. Great for daily math puzzles, kids, and puzzle enthusiasts.</p>
  </div>
</div>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    outdir = os.path.abspath("printouts")
    os.makedirs(outdir, exist_ok=True)
    
    pdf_board = os.path.join(outdir, "hex_game_board_1.5in.pdf")
    pdf_rules = os.path.join(outdir, "hex_games_rulebook.pdf")
    pdf_score = os.path.join(outdir, "score_sheets_and_tracker.pdf")
    pdf_math = os.path.join(outdir, "number_hive_math_puzzles.pdf")
    html_hub = os.path.join(outdir, "printouts_hub.html")
    
    print("Generating printable PDFs...")
    generate_hex_board_pdf(pdf_board)
    print(f" -> Saved Board PDF: {pdf_board}")
    
    generate_rulebook_pdf(pdf_rules)
    print(f" -> Saved Rulebook PDF: {pdf_rules}")
    
    generate_score_sheets_pdf(pdf_score)
    print(f" -> Saved Score Sheets PDF: {pdf_score}")
    
    generate_math_puzzles_pdf(pdf_math)
    print(f" -> Saved Math Puzzles PDF: {pdf_math}")
    
    generate_html_print_hub(html_hub)
    print(f" -> Saved HTML Printouts Hub: {html_hub}")
    
    print("\n[SUCCESS] All printouts generated successfully!")


if __name__ == "__main__":
    main()
