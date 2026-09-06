# Copy-and-paste prompt for the website agent

Build a complete, playable web game called **BUZZHEX** in my existing website.
It is classic **11 × 11 Hex**, visually matched to our physical Buzzello tiles
and the new BUZZHEX board. Use the site's existing stack, routing, shared
components, and deployment workflow. Finish implementation and verification;
do not stop at a mockup or planning document.

## Reference files

I will provide the BUZZHEX web handoff ZIP or these files from the print project:

- `output/boards/buzzhex/game_spec.json`: authoritative 121-cell coordinates,
  six neighbor offsets, colors' goal edges, and swap semantics.
- `docs/BUZZHEX_RULES.md`: complete tabletop rules.
- `output/boards/buzzhex/images/board_and_bed_preview.png`: assembled-board reference.
- `assets/artwork/buzzhex/buzzello-tile-black.svg` and
  `assets/artwork/buzzhex/buzzello-tile-yellow.svg`: actual tile faces, projected
  from our existing 3MF. Use these exact assets.
- `output/tiles/othello/images/tile_front_back.png`: reference image of both faces.

The handoff ZIP preserves these relative paths. A prompt alone cannot transfer
local assets: if the files are unavailable in your workspace or attachments,
request them before inventing replacement artwork.

## Required game rules

1. Two human players sharing one device. Start with an empty **121-cell rhombus**.
   Player 1 starts Black, Player 2 Yellow. Black places first.
2. On a normal turn, place one tile of the current player's color on an empty
   cell. No moves onto occupied cells. No flipping, captures, passing, movement,
   randomness, score multipliers, or Othello mechanics.
3. Black wins by connecting `q=0` to `q=10`; Yellow wins by connecting `r=0` to
   `r=10`. Search only through the winning color's tiles sharing hexagon edges.
   Corner cells belong to both incident board edges. Detect victory immediately,
   show the actual winning path, and disable further moves. Legal Hex has no draw.
4. After exactly one opening black placement, Player 2 may either place Yellow
   or choose **Swap colors**. Swapping exchanges player-to-color assignments,
   leaves the black opening tile at its original coordinate, consumes Player 2's
   turn without placing anything, and makes the original opener play Yellow next.
   Goal edges remain fixed to colors. The offer ends permanently after the swap
   or the first yellow placement. Never recolor or transpose the opening tile.
5. Track human identity separately from color so the turn indicator, winner,
   move log, undo, and restored state remain correct after swapping.

## Coordinates and rendering

Use integer axial coordinates `q,r` from 0 through 10 inclusive. A cell's only
neighbors are `(q+1,r)`, `(q-1,r)`, `(q,r+1)`, `(q,r-1)`, `(q+1,r-1)`, and
`(q-1,r+1)`, clipped to the board. Do not use square-grid diagonals or array
index wrapping. Keep game logic independent of rendering.

Match the supplied broad diamond-shaped rhombus and **flat-top** hexagonal tiles.
For a pitch `p`, use `x=(q+r-10)*p*sqrt(3)/2`,
`y=(q-r)*p/2` in screen coordinates (positive Y downward). This is the physical
board's world Y inverted for the browser. Tile centers sit at these positions;
regular flat-top hexagons at pitch p tile this lattice without topology changes.
Scale tile artwork to occupy roughly `33.02/35.7` of the lattice across flats.
The SVG viewBox includes transparent padding; account for its actual silhouette
bounds when sizing. Prefer a single responsive SVG with a generous viewBox.

Letters A–K mean q=0–10; numbers 1–11 mean r=0–10. Show readable edge labels
and let the selected cell display its coordinate. Black's rails are upper-left
and lower-right; Yellow's are lower-left and upper-right. At each tip the two
rails meet without assigning a corner exclusively to one player.

## Visual direction

Use a white honeycomb board with black grid lines, clearly contrasting black and yellow goal
rails, and the **exact Buzzello black/yellow rosette tile faces**. Their large
background identifies ownership; their inverted interior logo is decorative.
Preserve the hexagonal silhouette and artwork. Add restrained depth and a crisp
placement transition to echo the physical 4.8 mm tiles. Respect reduced motion.
Use a visible outline/shadow for black rails against a dark page background.
Do not show print-bed dimensions, section numbers, purge towers, manufacturing
seams, or printer instructions in the game interface. Default to the full
11 × 11 game; do not substitute a 7 × 7 or 61-cell board.

## Complete user flow

- A polished game screen with title, concise connection objective, player names,
  each player's current color and target edges, turn status, and placement count.
- Start immediately as “Player 1” and “Player 2”; names may be edited.
- Desktop: click a free cell to place. Touch: use a clear select/confirm placement
  flow if needed for accuracy; a pan or pinch gesture must never place a tile.
  Hover/selection previews must show the current player's face and legal target.
- Show the one-time **Swap colors** offer prominently at the correct moment.
- Announce moves, swaps, and the winner through an accessible live region.
  Support keyboard navigation and Enter/Space to place, visible focus, and labels
  such as “F6, empty” or “F6, black, Player 2.” Goal labels and player identity
  must supplement color. Keep occupied cells inspectable.
- Include rules/help with the swap example, and a move history that records
  swaps as actions separately from tile placements.
- Include undo of the last action for casual same-device play; undo restores
  the entire prior state, including player colors, turn, swap eligibility,
  winner, and path. This is a practice convenience, not a tabletop rule change.
- Confirm before clearing an in-progress game. New game fully resets the board,
  assignments, turn, opening offer, winner, and history.
- Save locally after each action and restore on reload. Version and validate the
  save, preferably by replaying validated actions. Reject malformed or illegal
  saved actions gracefully, without crashing or declaring a false winner.
- Make all controls usable on phone, tablet, and desktop. At phone widths,
  provide board zoom/pan or another tested way to select all 121 cells accurately
  while keeping turn status and essential controls reachable.

Deliver same-device play fully. Online multiplayer, accounts, rankings, and an
AI opponent are outside this request; do not add nonworking buttons for them.

## Required tests and acceptance checks

- Exactly 121 uniquely addressable cells with correct neighbor sets and four
  properly assigned goal edges. `(5,5)` connects to `(6,5)`, `(4,5)`, `(5,6)`,
  `(5,4)`, `(6,4)`, `(4,6)`, but **not** `(6,6)` or `(4,4)`.
- Detect Black on every `(q,5)` for q=0–10 and Yellow on every `(5,r)` for r=0–10
  in separate engine fixtures. Detect a winding path, correctly handle corner
  starts/ends, and reject disconnected groups or vertex-only contacts.
- Swap fixture: P1 plays Black at `(2,7)`; P2 swaps. That cell is still Black at
  `(2,7)`; P2 is Black; P1 is Yellow and moves next; there is still one tile.
  P1 then places Yellow; P2 plays Black next. No second swap is possible.
- Declining swap by placing Yellow closes the offer. Reject swap before the first
  placement and after the opening decision. Occupied-cell attempts change nothing.
- Correct winning human after a swap; no moves accepted after a win.
- Undo ordinary placement, swap, and winning move; save/reload after a swap;
  corrupt save recovery; full new-game reset.
- Verify board geometry visually and exercise touch/keyboard input, selection,
  all corners, zoom/pan, and readable controls at phone and desktop sizes.
- Run the project's relevant tests, type checks, and production build. Fix
  failures. Report what was implemented, the route, validation results, and
  anything that still needs my action.

Rules reference: https://en.wikipedia.org/wiki/Hex_(board_game).
Use our attached specification to fix the board size, exact tiles, palette,
coordinate convention, and player-assignment form of the swap rule.
