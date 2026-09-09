"""Printable tabletop rules matched to the ARES website's canonical game rules."""
from pathlib import Path
from math import cos, sin, pi, sqrt
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
YELLOW = HexColor('#F3D928')
INK = HexColor('#161819')
BLUE = HexColor('#08679B')
STYLE = ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=14,
                       textColor=INK, spaceAfter=8)

def paragraph(c, text, x, y, width=252):
    p = Paragraph(text, STYLE)
    _, h = p.wrap(width, 700)
    if y-h < 64:
        raise ValueError(f'Rulesheet overflow: {text[:60]} at {y-h}')
    p.drawOn(c, x, y-h)
    return y-h-8

def section(c, title, text, x, y):
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(x, y-12, title)
    return paragraph(c, text, x, y-23)

def header(c, game, subtitle):
    c.setTitle(f'{game} - Tabletop Rules')
    c.setAuthor('ARES FTC 23247')
    c.setFillColor(YELLOW)
    c.rect(0, 775, 612, 17, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 30)
    c.drawString(36, 735, game)
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(576, 741, 'TABLETOP RULES')
    c.setFont('Helvetica', 11)
    c.drawString(36, 713, subtitle)
    c.setStrokeColor(YELLOW)
    c.setLineWidth(3)
    c.line(36, 701, 576, 701)

def footer(c, url, extra=None):
    c.setStrokeColor(HexColor('#C9CDD0'))
    c.setLineWidth(.5)
    c.line(36, 55, 576, 55)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(BLUE)
    c.drawString(36, 39, url)
    c.linkURL('https://'+url, (36,35,330,49), relative=0)
    c.setFillColor(INK)
    c.setFont('Helvetica', 8)
    c.drawRightString(576, 39, 'ARES FTC 23247 | September 2026 | 1 / 1')
    c.setFont('Helvetica', 7.5)
    c.drawString(36, 23, extra or 'Team-created game. This is not an official FIRST competition game.')

def hexagon(c, x, y, radius, fill, label='', color=INK, angle=0):
    p = c.beginPath()
    for i in range(6):
        px, py = x+radius*cos(i*pi/3+angle), y+radius*sin(i*pi/3+angle)
        if i == 0: p.moveTo(px, py)
        else: p.lineTo(px, py)
    p.close()
    c.setFillColor(fill)
    c.setStrokeColor(INK)
    c.setLineWidth(.8)
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(color)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(x, y-4, label)

def make_buzzello():
    c=canvas.Canvas(str(OUT/'BUZZELLO_Rules_Classic_and_Large.pdf'), pagesize=(612,792))
    header(c, 'BUZZELLO', '2 players | Classic: 61 cells | Large: 91 cells | Yellow moves first')
    y=681
    y=section(c,'Win the hive','Finish with more pieces showing your color than your opponent. Each occupied hex counts as one piece.',36,y)
    y=section(c,'Set up','Choose one complete board edition. Use the same 1.3-inch reversible black/yellow pieces for either size. Keep a shared supply: 61 pieces for Classic or 91 for Large.<br/><br/>Leave the center empty. Put three Yellow and three Black pieces in alternating order around it. Use the board\'s starting marks or the diagram below. Choose your colors; Yellow takes the first turn.',36,y)
    y-=8
    cx,cy,r=159,y-67,23
    hexagon(c,cx,cy,r,white,'')
    for q,rr,label in [(1,0,'Y'),(0,1,'B'),(-1,1,'Y'),(-1,0,'B'),(0,-1,'Y'),(1,-1,'B')]:
        hexagon(c,cx+1.5*r*q,cy-sqrt(3)*r*(rr+q/2),r,YELLOW if label=='Y' else INK,label,INK if label=='Y' else white)
    c.setFont('Helvetica',9)
    c.setFillColor(INK)
    c.drawCentredString(cx,cy-75,'Y = Yellow   B = Black   Center = empty')
    y=cy-96
    y=section(c,'One board, two sizes','Large adds a 30-cell outer ring. The opening, legal moves, flipping and victory rules are identical. Do not mix Classic and Large printed sections.',36,y)
    y=681
    y=section(c,'1. Place one piece','Put a piece of your color in an empty cell. The move must trap at least one opposing piece in a straight, unbroken line between your new piece and another piece already showing your color.',324,y)
    y=section(c,'2. Flip every trapped line','Check all six directions from the new piece. Flip every opposing piece in each qualifying line to your color. You must flip all such lines.<br/><br/>An empty cell or board edge breaks a line. Lines cannot bend or jump. Flipped pieces do not start extra chain-reaction captures.',324,y)
    y-=7
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold',10)
    c.drawString(324,y,'Example: Yellow plays at the left')
    y-=26
    for i,label in enumerate(['Y','B','B','Y']):
        hexagon(c,400+i*sqrt(3)*19,y,19,YELLOW if label=='Y' else INK,label,INK if label=='Y' else white,pi/6)
    y=paragraph(c,'The two Black pieces turn Yellow. This works along any straight hex direction.',324,y-29)
    y=section(c,'3. Take turns - or pass','Black plays next, then alternate. If you have no legal move, you must pass. You may not pass when a legal move exists. If your opponent can move, they play again.',324,y)
    y=section(c,'End and score','Stop when neither player has a legal move, the board is full, or one color has no pieces left. Count the visible Yellow and Black pieces. Higher count wins; equal counts are a draw. Empty cells score nothing.',324,y)
    footer(c,'aresfirst.org/buzzello')
    c.save()

def make_buzzle():
    c=canvas.Canvas(str(OUT/'BUZZLE_Rules.pdf'), pagesize=(612,792))
    header(c, 'BUZZLE', '2-4 players | 217-cell honeycomb board | 7 tiles per rack')
    y=681
    y=section(c,'Set up','Use the 100-letter set, including two blanks, the assembled board, a bag and a scorepad. Mix the tiles face down. Each player draws seven and keeps them hidden. Choose a first player and take turns clockwise.<br/><br/>Agree to use the ARES word checker below so everyone uses the same word list. Highest final score wins.',36,y)
    y=section(c,'Play a word','Place 1-7 rack tiles into empty cells along one straight hex line. Words may run along any of the three board axes. New tiles and any existing letters between them must make a continuous word with no gaps.<br/><br/><b>First turn:</b> make a word of at least two letters covering the center star.<br/><b>Later turns:</b> connect to the existing hive by reusing letters or touching an occupied cell along an edge.<br/><br/>Check every new or extended word of two or more letters on all three axes. Each must be valid. A single tile may create several words. Existing tiles stay in place.',36,y)
    y=section(c,'Finish your turn','Agree that every word is valid, add your score, then draw back to seven tiles while the bag allows. Announce the letter represented by a blank when placing it. That letter stays fixed; its value remains zero.',36,y)
    y=section(c,'Exchange or pass','Instead of playing, exchange 1-7 rack tiles if the bag holds at least that many replacements. Draw replacements before returning and mixing the old tiles. The exchange uses your turn.<br/><br/>Or pass without changing your rack. A played word or exchange resets the consecutive-pass count.',36,y)
    y=681
    y=section(c,'Score every word','Add the printed letter values in each newly formed or extended word, including old letters. Score each distinct word once. Then add the scores of all words made by the play.',324,y)
    y=section(c,'Bonus cells','Bonuses apply <b>only to tiles placed this turn</b>:<br/><b>DL:</b> double that letter. <b>TL:</b> triple it.<br/><b>DW:</b> double the whole word.<br/><b>TW:</b> triple the whole word.<br/><b>Center star:</b> double word on the opening.<br/><b>DW / KEY:</b> the normal DW bonus; no extra key bonus.<br/><br/>Apply letter bonuses before word bonuses. Multiple word bonuses multiply together. A new bonus tile counts in each word it helps make. A blank stays worth zero, but its word bonus still applies.',324,y)
    y=section(c,'Use all seven: +50','Playing all seven rack tiles in one turn earns a 50-point Hive Flush after scoring the words.',324,y)
    y=section(c,'Quick scoring example','CAT has C=3, A=1, T=1: 5 points. If the new C lands on DL, it is 6+1+1=8. If that same word also covers a new DW, it scores 16. Add any valid crossing words separately.',324,y)
    y=section(c,'End the game','End when the bag is empty and a player uses their last tile, or after three full rounds of consecutive passes: 6 passes for two players, 9 for three, 12 for four.<br/><br/>Everyone subtracts the value of tiles left in their rack. If someone went out, they also add the total remaining tile values of the other players. After a pass ending, nobody receives that extra award. Highest score wins; a tie is a draw.',324,y)
    y=paragraph(c,'<b>Dictionary, word checker and two-letter list:</b><br/><link href="https://aresfirst.org/buzzle/word-tools" color="#08679B">aresfirst.org/buzzle/word-tools</link>',324,y)
    footer(c,'aresfirst.org/buzzle')
    c.save()

if __name__ == '__main__':
    make_buzzello()
    make_buzzle()
    print('Created two rulesheets in',OUT)
