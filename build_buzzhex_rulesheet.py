"""Create BUZZHEX's one-page tabletop rules from docs/BUZZHEX_RULES.md."""
from build_game_rulesheets import canvas, OUT, header, footer, section


def make_buzzhex():
    c = canvas.Canvas(str(OUT / 'BUZZHEX_Rules.pdf'), pagesize=(612, 792))
    header(c, 'BUZZHEX', '2 players | 11 x 11 board | 121 cells | Black opens')
    y = 681
    y = section(c, 'Connect your edges', 'Build an unbroken chain of your own tiles between your two matching goal rails. The first player to connect their edges wins immediately. There are no dice, captures or points.', 36, y)
    y = section(c, 'Set up', 'Assemble the six BUZZHEX sections. Start with every pocket empty. Keep 121 reversible black/yellow tiles in a common supply. Turn each tile to the right color before placing it.<br/><br/>The large background on the tile identifies its color. The honeycomb rosette is decoration; each tile occupies one cell.', 36, y)
    y = section(c, 'Choose your goal edges', '<b>Black connects the two black rails:</b> A to K in the assembly diagram (upper-left to lower-right).<br/><br/><b>Yellow connects the two yellow rails:</b> 1 to 11 (lower-left to upper-right).<br/><br/>The four corner cells are playable. Each touches both adjoining goal edges, but a tile counts only for its displayed color.', 36, y)
    y = section(c, 'Take a turn', 'Place one tile, your color face up, in any empty cell. Then check whether it completes your connection. If not, the other player takes a turn.<br/><br/>Tiles connect through shared hexagon edges in all six directions. Your chain may bend or branch. Point contact alone does not connect tiles.', 36, y)
    y = 681
    y = section(c, 'Balance the opening: swap rule', '<b>1.</b> Player 1 places one Black tile anywhere.<br/><br/><b>2.</b> Player 2 either places a Yellow tile normally or chooses to swap colors.<br/><br/><b>3.</b> After a swap, Player 2 becomes Black and owns the opening tile. Player 1 becomes Yellow and places the next tile.<br/><br/><b>The opening tile stays Black in its original cell.</b> Do not move or flip it. Swapping uses Player 2\'s turn and adds no tile. There is no second swap. Playing Yellow instead permanently declines the option.<br/><br/>The goal rails stay attached to colors even when the players exchange colors.', 324, y)
    y = section(c, 'Placed tiles stay put', 'There is no flipping, moving, jumping, flanking, capturing or passing. Surrounding tiles earns no bonus. Although BUZZHEX reuses BUZZELLO pieces, the rules are different.', 324, y)
    y = section(c, 'Win the connection', 'Win as soon as your own chain reaches both of your goal edges. Do not count tiles or territory. A completed legal Hex game cannot draw; a full board has a winner. Either player may resign earlier.', 324, y)
    y = section(c, 'Example paths', '<b>Black:</b> A6, B6, through K6.<br/><b>Yellow:</b> F1, F2, through F11.<br/><br/>These are separate examples. Both complete paths cannot coexist because both need F6.', 324, y)
    footer(c, 'aresfirst.org', 'BUZZHEX by ARES FTC 23247 | Based on Hex | Rules source: docs/BUZZHEX_RULES.md')
    c.save()


if __name__ == '__main__':
    make_buzzhex()
    print(OUT / 'BUZZHEX_Rules.pdf')
