# BUZZHEX

**Classic Hex on an 11 × 11 board, using the same reversible tiles as Buzzello.**

Two players. No dice, captures, or scoring. Connect your two matching goal edges
with one unbroken chain of your own tiles to win.

## Components and setup

Use the [121-cell BUZZHEX board](../output/boards/buzzhex/PRINT_GUIDE.md) and
121 existing black/yellow Buzzello tiles in a shared supply. You do not need
separate sets for each color: expose the appropriate face when placing a tile.
Start with every board pocket empty.

Choose who opens. The opener starts as **Black**; the other player starts as
**Yellow**. Black connects the two black rails, and Yellow connects the two yellow
rails. In the [assembly diagram](../output/boards/buzzhex/images/board_and_bed_preview.png):

- Black connects **A to K**: the upper-left and lower-right edges.
- Yellow connects **1 to 11**: the lower-left and upper-right edges.

The four corner cells A1, A11, K1, and K11 each touch both adjoining goal edges.
They are ordinary playable cells. A tile in a corner still belongs to only its
displayed color, but it counts as touching that color's incident goal edge.

## Your turn

Place one tile, your color face up, in any empty cell. Tiles connect through
shared hexagon edges in any of the six neighboring directions. A chain may
turn, branch, or touch the board edge multiple times. Point contact alone does
not connect tiles.

After placement, check for a path joining your two goal edges. If one exists,
you win immediately. Otherwise the other player takes a turn.

Once placed, tiles stay in their cells and retain their displayed color.
There is no flipping, flanking, jumping, moving, capturing, passing, or bonus
for surrounding tiles. The rosette inside a tile is artwork, not a separate
piece or a connection pattern.

## Opening swap rule

Use the standard pie rule to balance the first move:

1. Player 1 places one **black** tile anywhere.
2. Player 2 chooses either to place a **yellow** tile normally, or to **swap colors**.
3. If Player 2 swaps, they become Black and own the opening tile. Player 1
   becomes Yellow and makes the next placement. The opening tile remains
   **black, in its original cell**. Nobody flips or moves it.
4. The swap uses Player 2's turn. It adds no tile. There is no second swap.
   Playing a yellow tile instead permanently declines the option.

Goal edges always stay attached to colors, even when the players exchange
colors. For example, after a swap Player 2 now connects A to K.

## Winning and ending

The first player to complete their own edge-to-edge chain wins. Count neither
the number of tiles nor captured territory. A legal completed Hex game cannot
draw; a full board has a winner. Either player may resign earlier.

Examples: all eleven cells A6, B6, …, K6 form a Black win. All eleven cells
F1, F2, …, F11 form a Yellow win. These are separate example positions; the
two complete paths cannot coexist because they would both require F6.

## Credit and compatibility

BUZZHEX is this project's working name for a tile-compatible edition of Hex.
The game retains the connection and swap rules described in
[Hex — rules and background](https://en.wikipedia.org/wiki/Hex_%28board_game%29).
Hex was invented by Piet Hein and independently rediscovered by John Nash.

Buzzello's reversible pieces are reused, but its six-sided 61-cell board and
flipping rules are not used. BUZZHEX requires the four-sided 11 × 11 rhombus
board. The web version must use the same 121-cell topology and tile artwork.
